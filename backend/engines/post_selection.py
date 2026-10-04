"""Descriptive recorded milestones and closures, never predicted student dropouts."""
from collections import Counter, defaultdict
from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy import select
from models import Interview, Job, Offer, OfferEvent, ScheduleEvent
from schemas import PostSelectionAnalytics

STATUS_VALUES = {
    "offer_letter_status": {"draft", "issued", "withdrawn"},
    "documents_status": {"pending", "submitted", "changes_requested"},
    "acceptance_status": {"pending", "accepted", "declined"},
    "verification_status": {"pending", "verified", "rejected"},
    "joining_status": {"pending", "joined", "not_joined"},
}
MILESTONE_FIELDS = {"issued": "offer_letter_status", "accepted": "acceptance_status",
    "verified": "verification_status", "joined": "joining_status"}
CLOSURE_FIELDS = {"withdrawn": "offer_letter_status", "declined": "acceptance_status", "not_joined": "joining_status"}
CLOSURE_ACTIONS = {"withdrawn": "offer_letter_status:withdrawn", "declined": "decline", "not_joined": "joining_status:not_joined"}
CLOSURE_LABELS = {"withdrawn": "Offer withdrawn", "declined": "Offer declined", "not_joined": "Non-joining recorded"}
SCOPE_EXPLANATIONS = {
    "recorded": "Recorded college workflow excludes archived demo colleges and explicitly synthetic or seed-marked records. These records are not independent verification of employment.",
    "synthetic": "Synthetic and archived workflow records only. Archived demo colleges include manually entered test records regardless of the offer's synthetic flag; these are not real placement outcomes.",
    "all": "All recorded workflow in this college, including labeled synthetic and archived demonstration records. This is not independent verification of employment.",
}


def _load(session, college, job_id):
    drives = session.execute(select(Job.id, Job.title).where(Job.college_id == college).order_by(Job.id.desc())).mappings().all()
    if job_id is not None and job_id not in {row["id"] for row in drives}:
        raise HTTPException(404, "Drive not found in this college.")
    interviews_query = select(Interview.id, Interview.student_id, Interview.job_id, Interview.status, Interview.seed_key).where(Interview.college_id == college)
    offers_query = select(Offer.id, Offer.student_id, Offer.job_id, Offer.interview_id, Offer.is_synthetic,
        *[getattr(Offer, key) for key in STATUS_VALUES], Interview.student_id.label("linked_student_id"),
        Interview.job_id.label("linked_job_id")).join(Interview,
            (Interview.id == Offer.interview_id) & (Interview.college_id == Offer.college_id)).where(
                Offer.college_id == college, Interview.college_id == college)
    if job_id is not None:
        interviews_query = interviews_query.where(Interview.job_id == job_id)
        offers_query = offers_query.where(Offer.job_id == job_id)
    interviews = session.execute(interviews_query).mappings().all()
    offers = session.execute(offers_query).mappings().all()
    offer_events = session.execute(select(OfferEvent.id, OfferEvent.offer_id, OfferEvent.action, OfferEvent.reason,
        OfferEvent.snapshot).where(OfferEvent.college_id == college, OfferEvent.offer_id.in_([row["id"] for row in offers]))
        .order_by(OfferEvent.id)).mappings().all()
    selection_events = session.execute(select(ScheduleEvent.id, ScheduleEvent.interview_id, ScheduleEvent.snapshot).where(
        ScheduleEvent.college_id == college, ScheduleEvent.interview_id.in_([row["id"] for row in interviews]),
        ScheduleEvent.action == "interview_status").order_by(ScheduleEvent.id)).mappings().all()
    return drives, interviews, offers, offer_events, selection_events


def _states(snapshot, expected, values):
    # Do not turn malformed or mismatched audit JSON into milestone evidence.
    if not isinstance(snapshot, dict) or not isinstance(snapshot.get("after"), dict):
        return [], True
    result = []
    for side in ("before", "after"):
        state = snapshot.get(side)
        if state is None and side == "before":
            continue
        if not isinstance(state, dict):
            return [], True
        if any(key in state and (type(state[key]) is not int or state[key] != value) for key, value in expected.items()):
            return [], True
        if any(key in state and (not isinstance(state[key], str) or state[key] not in allowed) for key, allowed in values.items()):
            return [], True
        if not any(key in state for key in values):
            return [], True
        result.append(state)
    return result, False


def _pair(row):
    return row["student_id"], row["job_id"]


def _closure(row):
    # A contradictory legacy row is counted once, with this stated precedence.
    return next((key for key, field in CLOSURE_FIELDS.items() if row[field] == key), None)


def _matches_scope(synthetic, scope):
    return scope == "all" or synthetic == (scope == "synthetic")


def _selection(interviews, offers, selection_events):
    lookup = {row["id"]: row for row in interviews}
    current = {_pair(row) for row in interviews if row["status"] == "selected"}
    historical, bad_pairs = set(), []
    for event in selection_events:
        row = lookup[event["interview_id"]]
        states, invalid = _states(event["snapshot"], {key: row[key] for key in ("id", "student_id", "job_id")},
            {"status": {"scheduled", "completed", "selected", "rejected", "cancelled"}})
        if invalid:
            bad_pairs.append(_pair(row))
        elif any(state.get("status") == "selected" for state in states):
            historical.add(_pair(row))
    valid_offers = [row for row in offers if (row["linked_student_id"], row["linked_job_id"]) == _pair(row)]
    linked = {_pair(row) for row in valid_offers}
    # Creation requires selection, so a linked offer is retained selection evidence
    # even when an interview's current outcome has later been revised.
    return current, historical, linked, bad_pairs, valid_offers


def _offer_history(offers, events):
    lookup = {row["id"]: row for row in offers}
    history, invalid = defaultdict(list), Counter()
    for event in events:
        row = lookup.get(event["offer_id"])
        if row is None:
            continue
        states, bad = _states(event["snapshot"], {key: row[key] for key in ("id", "student_id", "job_id", "interview_id")}, STATUS_VALUES)
        if bad:
            invalid[row["id"]] += 1
        else:
            history[row["id"]].append((event, states))
    return history, invalid


def _terminal_reason(row, history, closure):
    field = CLOSURE_FIELDS[closure]
    for event, states in reversed(history):
        after = states[-1]
        if after.get(field) != closure:
            continue
        source = "recorded_action" if event["action"] == CLOSURE_ACTIONS[closure] else "synthetic_import" if event["action"] == "synthetic_import" else None
        reason = event["reason"]
        if source and isinstance(reason, str) and reason.strip():
            return reason, source
    return "No matching recorded reason is available.", "missing"


def _stages(pairs, evidence, closures):
    stages, previous = [], None
    for key, label in (("selected", "Selected"), ("issued", "Letter issued"), ("accepted", "Accepted"),
            ("verified", "Accepted and verified"), ("joined", "Joined")):
        reached = pairs if key == "selected" else previous & evidence[key]
        missing = set() if previous is None else previous - reached
        closed = missing & closures
        denominator = None if previous is None else len(previous)
        explanation = (f"{len(reached)} distinct student-drive pairs have recorded selection evidence; interview rounds are counted once." if previous is None else
            f"{len(reached)} / {denominator} pairs from the previous stage have all milestones through {label.lower()} recorded. "
            f"{len(missing) - len(closed)} have no recorded terminal offer closure and have not reached this stage; {len(closed)} have a recorded terminal offer closure. Missing progress is not a predicted dropout.")
        stages.append(dict(key=key, label=label, count=len(reached), distinct_students=len({pair[0] for pair in reached}),
            previous_count=denominator, conversion_percent=round(len(reached) / denominator * 100, 2) if denominator else None,
            not_reached_from_previous=len(missing), pending_from_previous=len(missing - closed), closed_from_previous=len(closed), explanation=explanation))
        previous = reached
    return stages


def _summarize_closures(offers, history, synthetic):
    groups, closed, missing = {}, defaultdict(set), Counter()
    for row in offers:
        closure = _closure(row)
        if closure is None:
            continue
        pair = _pair(row)
        closed[closure].add(pair)
        reason, source = _terminal_reason(row, history[row["id"]], closure)
        missing[closure] += source == "missing"
        key = closure, reason, source
        group = groups.setdefault(key, dict(closure=closure, reason=reason, reason_source=source,
            count=0, synthetic_count=0, recorded_count=0))
        group["count"] += 1
        group["synthetic_count" if synthetic[pair] else "recorded_count"] += 1
    closures = [dict(key=key, label=label, count=len(closed[key]), distinct_students=len({pair[0] for pair in closed[key]}),
        missing_reason_count=missing[key], explanation=f"{len(closed[key])} offers/student-drive pairs currently have {label.lower()}; these are recorded offer outcomes, not labels of student failure. {missing[key]} have no matching recorded reason.")
        for key, label in CLOSURE_LABELS.items()]
    reasons = sorted(groups.values(), key=lambda row: (-row["count"], row["closure"], row["reason_source"], row["reason"]))
    return closures, reasons, set().union(*closed.values()) if closed else set()


def report(session, user, scope="recorded", job_id=None, offset=0, limit=20):
    if user.role != "admin":
        raise HTTPException(403, "Post-selection analytics is available to placement administrators only.")
    college = user.college_id
    drives, interviews, all_offers, events, selection_events = _load(session, college, job_id)
    current, historical, linked, bad_selection, valid_offers = _selection(interviews, all_offers, selection_events)
    cohort = current | historical | linked
    synthetic = {_pair(row): college in (1, 2) for row in interviews}
    for row in interviews:
        if row["seed_key"] is not None:
            synthetic[_pair(row)] = True
    for row in valid_offers:
        synthetic[_pair(row)] = synthetic[_pair(row)] or row["is_synthetic"]
    pairs = {pair for pair in cohort if _matches_scope(synthetic[pair], scope)}
    offers = [row for row in valid_offers if _pair(row) in pairs]
    history, invalid = _offer_history(offers, events)
    evidence = {key: set() for key in MILESTONE_FIELDS}
    for row in offers:
        states = [row] + [state for _, snapshots in history[row["id"]] for state in snapshots]
        for key, field in MILESTONE_FIELDS.items():
            if any(state.get(field) == key for state in states):
                evidence[key].add(_pair(row))
    closures, reasons, closed_pairs = _summarize_closures(offers, history, synthetic)
    milestones = [dict(key=key, label=f"Ever recorded {key}", count=len(group), distinct_students=len({pair[0] for pair in group}),
        explanation=f"{len(group)} student-drive pairs have {key} recorded in current statuses or retained valid snapshots, independent of the other milestones. This does not establish when or in which order events happened.")
        for key, group in evidence.items()]
    verification_only = evidence["verified"] - evidence["accepted"]
    milestones.append(dict(key="verified_without_acceptance", label="Verification without acceptance evidence", count=len(verification_only),
        distinct_students=len({pair[0] for pair in verification_only}), explanation=f"{len(verification_only)} pairs have verification evidence but no acceptance evidence. Acceptance and verification are independent; this count does not infer timing or rejection."))
    event_ids = {event["offer_id"] for event in events}
    return PostSelectionAnalytics(scope=scope, college_id=college, job_id=job_id, archive_demo=college in (1, 2),
        scope_explanation=SCOPE_EXPLANATIONS[scope], drives=drives,
        cohort=dict(selected_pairs=len(pairs), distinct_students=len({pair[0] for pair in pairs}), offers=len(offers), without_offer=len(pairs - linked),
            synthetic_pairs=sum(synthetic[pair] for pair in pairs), recorded_pairs=sum(not synthetic[pair] for pair in pairs), excluded_pairs=len(cohort - pairs)),
        stages=_stages(pairs, evidence, closed_pairs), milestones=milestones, closures=closures,
        reasons=reasons[offset:offset + limit], reason_total=len(reasons), offset=offset, limit=limit,
        data_quality=dict(offers_without_history=sum(row["id"] not in event_ids for row in offers), invalid_offer_history_events=sum(invalid.values()),
            invalid_selection_history_events=sum(_matches_scope(synthetic[pair], scope) for pair in bad_selection),
            withdrawn_without_issuance_evidence=sum(row["offer_letter_status"] == "withdrawn" and _pair(row) not in evidence["issued"] for row in offers),
            accepted_without_issuance_evidence=len(evidence["accepted"] - evidence["issued"]), selection_from_linked_offer=len((linked - current - historical) & pairs),
            selection_from_history=len((historical - current) & pairs),
            offers_with_mismatched_interview=sum((row["linked_student_id"], row["linked_job_id"]) != _pair(row) and
                _matches_scope(college in (1, 2) or row["is_synthetic"], scope) for row in all_offers),
            historical_selection_no_current_selection=len((historical - current) & pairs)),
        methodology="Descriptive counts, not a score or forecast. The unit is a distinct student-drive pair; multiple interview rounds count once and the database allows at most one offer per pair. Selection uses current/historical selected interview evidence or a consistently linked offer whose creation required selection. The funnel intersects ever-recorded milestones in presentation order: selected, issued, accepted, accepted AND verified, joined. Verification can be recorded independently of acceptance. Current statuses and valid before/after snapshots preserve reached milestones after withdrawal or corrections; they do not prove event timing. Conversion divides a cumulative stage by the preceding cumulative stage and is unavailable for a zero denominator. Only current explicit withdrawal, decline or non-joining counts as a closure; precedence is withdrawn, declined, then not_joined. Reason groups use exact recorded action text or separately labeled synthetic import notes, never inferred causes.",
        limitations=["No date cohort, elapsed-time attribution or prediction of future placement/dropout is inferred from collapsed or incomplete history.",
            "An unmet stage with no recorded terminal offer closure is not proof that a process is still actively awaiting progress; selections can be revised and offers may never be created.",
            "Historical milestones remain counted even if a later human decision revised the current outcome; this is not a count of active accepted offers.",
            "Synthetic import notes describe data-generation assumptions, not employer or student explanations of withdrawal/non-joining.",
            "One student can appear in several drive pairs and closure categories; distinct student counts must not be summed across stages or categories.",
            "Recorded statuses and human reasons are declarations, not independent verification of employment or documents."],
        generated_at=datetime.now(timezone.utc))
