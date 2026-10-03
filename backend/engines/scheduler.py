"""Deterministic greedy interval checks. No LLM or metaheuristic solver."""
from datetime import datetime, time, timedelta, timezone
from functools import lru_cache
from zoneinfo import ZoneInfo
from schemas import ConflictResponse, CalendarConflictResponse, SlotProposal

METHOD = ("Deterministic greedy search over half-open intervals [start, end). "
    "Checks student, venue, panel, shared-drive bookings, declared availability, exam blocks, "
    "configured campus working hours and numbered-round order. It advances to blocker ends "
    "or the next declared opening and rechecks everything. The whole interview must fit "
    "within seven days of the requested start. Independent drives can run in parallel. "
    "Declarations are human-entered; unknown availability is not inferred. Every proposal "
    "requires human approval and a fresh check of current constraints.")


def conflicts_for(slot, bookings):
    start = slot.scheduled_time
    end = start + timedelta(minutes=slot.duration_minutes)
    found = []
    for booking in bookings:
        if booking.id == slot.reschedule_interview_id or booking.status == "cancelled":
            continue
        if start >= booking.end_time or end <= booking.scheduled_time:
            continue
        kinds = []
        if booking.student_id == slot.student_id:
            kinds.append("student")
        if booking.venue == slot.venue:
            kinds.append("venue")
        if booking.panel_id == slot.panel_id:
            kinds.append("panel")
        if not kinds:
            continue
        if booking.job_id != slot.job_id:
            kinds.append("overlapping_drive")
        found.append(ConflictResponse(interview_id=booking.id, job_id=booking.job_id,
            student_id=booking.student_id, scheduled_time=booking.scheduled_time, end_time=booking.end_time,
            kinds=kinds, explanation=f"Interview #{booking.id} in drive #{booking.job_id} overlaps this interval and shares "
                + ", ".join(k for k in kinds if k != "overlapping_drive")
                + (" across different drives." if "overlapping_drive" in kinds else ".")))
    return sorted(found, key=lambda c: (c.scheduled_time, c.interview_id))


def union_windows(windows):
    """Join touching positive windows; the entire duration must fit their union."""
    merged = []
    for start, end in sorted(windows):
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged


def next_window(start, duration, windows):
    for opening, closing in union_windows(windows):
        candidate = max(start, opening)
        if candidate + duration <= closing:
            return candidate
    return None


@lru_cache(maxsize=512)
def working_windows(local_date, timezone_name, opening, closing):
    """Build actual UTC openings using local wall-clock minutes, including DST.

    UTC scanning makes nonexistent local times disappear and repeated times remain
    distinct. It avoids silently attaching a timezone to an invalid local time.
    All configured boundaries have minute precision; cached daily windows serve
    every proposal/approval in that local date without recomputing the scan.
    """
    zone = ZoneInfo(timezone_name)
    start = datetime.combine(local_date, time.min, zone).astimezone(timezone.utc) - timedelta(hours=3)
    end = datetime.combine(local_date + timedelta(days=1), time.min, zone).astimezone(timezone.utc) + timedelta(hours=3)
    windows = []
    active_start = None
    cursor = start
    while cursor < end:
        local = cursor.astimezone(zone)
        clock = local.strftime("%H:%M")
        active = local.date() == local_date and opening <= clock < closing
        if active and active_start is None:
            active_start = cursor
        elif not active and active_start is not None:
            windows.append((active_start, cursor))
            active_start = None
        cursor += timedelta(minutes=1)
    if active_start is not None:
        windows.append((active_start, end))
    return tuple(windows)


def hours_windows(start, horizon, settings):
    zone = ZoneInfo(settings.timezone)
    first = start.astimezone(zone).date()
    last = horizon.astimezone(zone).date()
    windows = []
    date = first
    while date <= last:
        if date.weekday() in settings.weekdays:
            windows.extend(working_windows(date, settings.timezone, settings.day_start, settings.day_end))
        date += timedelta(days=1)
    return windows


def calendar_conflicts_for(slot, bookings, settings=None, constraints=(), student_branch="", horizon=None):
    """Return named blockers and next possible forward start (None if none).

    The hours toggle controls only recurring hours. Dated blocks and positive
    declarations always apply. Explicit required-window flags also apply when
    recurring hours are disabled. Any active positive declaration for a resource
    requires containment, including when its dates fall outside the horizon.
    """
    start = slot.scheduled_time
    duration = timedelta(minutes=slot.duration_minutes)
    end = start + duration
    horizon = horizon or start + timedelta(days=7)
    next_times = [start]
    found = []
    branch = " ".join(student_branch.upper().split())
    active = [c for c in constraints if c.status == "active" and (
        c.scope == "campus" or c.scope == "branch" and c.resource_name == branch
        or c.scope == "student" and c.student_id == slot.student_id
        or c.scope == "panel" and c.resource_name == slot.panel_id)]

    if settings is not None and settings.enabled:
        next_start = next_window(start, duration, hours_windows(start, horizon, settings))
        if next_start != start:
            found.append(CalendarConflictResponse(kind="working_hours", starts_at=start, ends_at=end,
                explanation=f"The full interview must fit configured campus hours {settings.day_start}–{settings.day_end} in {settings.timezone}, on the chosen weekdays."))
            next_times.append(next_start)

    for scope, required in (("student", bool(settings and settings.require_student_availability)),
                            ("panel", bool(settings and settings.require_panel_availability))):
        positive = [c for c in active if c.scope == scope and c.kind == "available"]
        if positive or required:
            next_start = next_window(start, duration, [(c.starts_at, c.ends_at) for c in positive])
            if next_start != start:
                found.append(CalendarConflictResponse(kind=f"{scope}_availability", starts_at=start, ends_at=end,
                    explanation=f"The full interview does not fit the {scope}'s active declared availability windows. "
                    + ("No active window is recorded." if not positive else "Touching windows are combined; gaps remain unavailable.")))
                next_times.append(next_start)

    for constraint in active:
        if constraint.kind == "available" or start >= constraint.ends_at or end <= constraint.starts_at:
            continue
        found.append(CalendarConflictResponse(constraint_id=constraint.id,
            kind="exam" if constraint.kind == "exam" else f"{constraint.scope}_unavailable",
            starts_at=constraint.starts_at, ends_at=constraint.ends_at,
            explanation=f"{constraint.scope.capitalize()} {constraint.kind}: {getattr(constraint, 'label', 'declared calendar block')}."))
        next_times.append(constraint.ends_at)

    for booking in bookings:
        if booking.status == "cancelled" or booking.id == slot.reschedule_interview_id:
            continue
        if booking.student_id != slot.student_id or booking.job_id != slot.job_id:
            continue
        number = getattr(booking, "round_number", 1)
        if number < slot.round_number and start < booking.end_time:
            found.append(CalendarConflictResponse(kind="round_order", starts_at=booking.scheduled_time, ends_at=booking.end_time,
                explanation=f"Round {slot.round_number} must start after recorded earlier round {number} (interview #{booking.id}) ends."))
            next_times.append(booking.end_time)
        elif number > slot.round_number and end > booking.scheduled_time:
            found.append(CalendarConflictResponse(kind="round_order", starts_at=booking.scheduled_time, ends_at=booking.end_time,
                explanation=f"Round {slot.round_number} must finish before recorded later round {number} (interview #{booking.id}) begins; moving forward cannot resolve this order."))
            next_times.append(None)
    return found, None if None in next_times else max(next_times)


def propose_slot(slot, bookings, settings=None, constraints=(), student_branch=""):
    candidate = slot.model_copy()
    encountered = {}
    calendar_encountered = {}
    horizon = slot.scheduled_time + timedelta(days=7)
    duration = timedelta(minutes=slot.duration_minutes)
    while candidate.scheduled_time + duration <= horizon:
        conflicts = conflicts_for(candidate, bookings)
        calendar_conflicts, next_start = calendar_conflicts_for(candidate, bookings, settings,
            constraints, student_branch, horizon)
        for conflict in conflicts:
            encountered[conflict.interview_id] = conflict
        for conflict in calendar_conflicts:
            key = (conflict.constraint_id, conflict.kind, conflict.starts_at, conflict.ends_at, conflict.explanation)
            calendar_encountered[key] = conflict
        if not conflicts and not calendar_conflicts:
            explanation = ("The requested time clears the recorded booking and calendar constraints."
                if not encountered and not calendar_encountered else
                f"Found {len(encountered)} blocking interview(s) and {len(calendar_encountered)} calendar constraint(s). The proposed time clears the recorded constraints.")
            if settings is None or not settings.enabled:
                explanation += " Recurring campus working hours are not configured/enabled."
            return SlotProposal(requested_time=slot.scheduled_time, proposed_time=candidate.scheduled_time,
                proposed_end_time=candidate.scheduled_time + duration, conflicts=list(encountered.values()),
                calendar_conflicts=list(calendar_encountered.values()),
                explanation=explanation + " Awaiting administrator approval.", methodology=METHOD)
        if next_start is None:
            break
        candidate.scheduled_time = max([next_start] + [c.end_time for c in conflicts])
    reasons = list(dict.fromkeys(c.explanation for c in calendar_encountered.values()))
    explanation = "No complete free slot was found within seven days. "
    if reasons:
        explanation += " ".join(reasons[:3]) + " "
    explanation += "Review availability windows, calendar constraints or round order; nothing has been booked."
    return SlotProposal(requested_time=slot.scheduled_time, proposed_time=None, proposed_end_time=None,
        conflicts=list(encountered.values()), calendar_conflicts=list(calendar_encountered.values()),
        explanation=explanation,
        methodology=METHOD)
