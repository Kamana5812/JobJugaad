"""Deterministic greedy constraint checking. No LLM or metaheuristic solver."""
from datetime import timedelta
from schemas import ConflictResponse, SlotProposal

METHOD = ("Deterministic greedy search over half-open time intervals [start, end). "
    "Checks student, venue and panel overlap, including shared resources across drives. "
    "Advances to the latest end of current blockers and rechecks all resources, up to seven days. "
    "Independent drives can run in parallel. No campus opening-hours calendar is configured. "
    "Every proposal requires human approval and a fresh conflict check.")


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


def propose_slot(slot, bookings):
    candidate = slot.model_copy()
    encountered = {}
    horizon = slot.scheduled_time + timedelta(days=7)
    while candidate.scheduled_time <= horizon:
        conflicts = conflicts_for(candidate, bookings)
        for conflict in conflicts:
            encountered[conflict.interview_id] = conflict
        if not conflicts:
            explanation = ("The requested time clears all student, venue, panel and shared-drive constraints."
                if not encountered else
                f"Found {len(encountered)} blocking interview(s). The proposed time clears all student, venue, panel and shared-drive constraints.")
            return SlotProposal(requested_time=slot.scheduled_time, proposed_time=candidate.scheduled_time,
                proposed_end_time=candidate.scheduled_time + timedelta(minutes=slot.duration_minutes),
                conflicts=list(encountered.values()), explanation=explanation + " Awaiting administrator approval.", methodology=METHOD)
        candidate.scheduled_time = max(c.end_time for c in conflicts)
    return SlotProposal(requested_time=slot.scheduled_time, proposed_time=None, proposed_end_time=None,
        conflicts=list(encountered.values()), explanation="No free slot was found within seven days. Change the requested time or resources; nothing has been booked.",
        methodology=METHOD)
