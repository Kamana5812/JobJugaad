# Scheduling availability

This extension adds recorded calendar constraints to the existing deterministic greedy checker. It proposes the first slot that clears the recorded rules within seven days, then waits for a placement administrator to approve it. It is not an optimal-timetable solver or an AI model.

## Configure the campus

1. Sign in as your college administrator and open Scheduling.
2. In **Campus calendar rules**, choose an IANA timezone, working weekdays and daily opening/closing times. Enable campus hours to enforce them. No institution's hours are invented or enabled automatically.
3. Decide whether every student and panel must supply a positive availability window. Missing required windows prevent a proposal.
4. Enter a reason and save. The saved configuration applies to checks and approvals; it does not automatically cancel existing bookings.

## Record dates

- Students record their own Available or Unavailable intervals in My interviews. These are calendar declarations, not approved interview bookings.
- Administrators record student/panel intervals and campus-wide or branch-specific exam blocks. Panel names use the same case/whitespace normalization as interview resources. Branch exam scope must match the student's recorded branch.
- Dated intervals include timezone offsets; forms show the browser timezone and submit UTC instants. Recurring campus hours use the saved campus timezone, which can differ from the browser's.
- If a resource has active Available intervals, the whole interview must fit inside their combined coverage. Cancel or replace outdated windows; a window outside the seven-day search does not make the resource unconstrained. Unavailable intervals and exams block overlapping time.
- Cancelling a calendar entry records a reason and versioned audit evidence instead of deleting history. Students cannot edit another student's or a panel's calendar.

## Schedule a round

1. Choose an approved recruiter-shortlisted applicant in the admin Scheduling panel (real college workflow).
2. Choose a round number and a descriptive name, for example 1 / Technical or 2 / HR. Enter the requested date, duration, venue and panel.
3. Click Check availability. Review the suggested time, booking clashes and calendar explanations.
4. Click Create pending proposal. Pending proposals do not reserve resources.
5. Approve the proposal with a reason. The server checks all current constraints again under the college calendar lock. If constraints changed, recheck the proposal and approve its new version.
6. Use Propose reschedule to change time/resources while retaining the original round identity. The old booking remains until the replacement is approved.

Later-numbered rounds must follow earlier recorded rounds for the same student and drive. Round numbers organize interview bookings; they do not automatically pass a student, imply a final selection or issue an offer. Selection and offer actions remain explicit human decisions.

## Security and limits

Calendar settings and constraints have application-level college filters and PostgreSQL ENABLE/FORCE college_isolation policies. Student routes additionally enforce ownership. Calendar writes share the existing transaction advisory lock with approval, rescheduling and outcome changes, and use version checks to prevent stale edits. Audit history uses the existing tenant-isolated scheduling events.

This checks only recorded facts. Panel expertise, holiday imports, room capacity, external calendar synchronization and a globally optimal timetable are not implemented. Calendar declarations do not prove attendance. Other items in the improvement backlog are separate work.
