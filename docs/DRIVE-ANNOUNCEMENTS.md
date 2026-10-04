# Drive announcements and reminders

Placement officers publish plain-text messages into students' existing **Notifications** feed. Hiring messages are not emailed or sent by SMS. A reminder is published immediately by an officer; there is no scheduled-delivery worker or external calendar integration.

## Publish a message

1. Sign in with an approved, server-allowlisted administrator account for the correct college.
2. Open **Command Center → Announcements**.
3. Choose the drive and either **Drive update** or **Reminder**.
4. Choose the audience, optionally narrowing it to a branch:
   - **Active applicants:** saved applications marked submitted, under review or shortlisted.
   - **Shortlisted candidates:** a saved shortlisted application or a saved effective matching shortlist. A rejected/withdrawn application or a rejected matching override excludes the student. This audience does not rerun matching or imply every calculated shortlist was manually approved.
   - **Scheduled interview students:** confirmed bookings currently marked scheduled. Pending proposals, cancelled bookings and completed/outcome records do not qualify. A past booking still marked scheduled qualifies until its status is updated.
   - **Approved college students:** student-role accounts in this college; branch selection can narrow this group. This is an explicit college-wide audience, not an eligibility calculation.
5. Enter a clear title and message. Include dates, timezone, location and what students should do when relevant. Do not include other students' personal information or private hiring reasons.
6. Click **Preview audience**. Review the drive, message, actual recipient count, audience explanation and sample of up to ten students. A sample is not the full recipient list.
7. Click **Publish to [count] students** only after reviewing the preview. An empty audience cannot be published. If the content or audience changes, obtain a new preview.
8. The publication appears in history with its author ID, timestamp, frozen message and recipient count. Expand its delivery history to inspect recipients and read status; use pagination and refresh as needed.

Real-college recipients must be email-verified and college-approved student accounts. Approved recruiter ownership is required for the selected drive. Archived demonstration colleges permit their existing accounts, but administrators/recruiters retaining old student profiles are excluded from every audience. Branch comparison ignores letter case and extra whitespace; it does not infer equivalence between abbreviations and full branch names. A filter is limited to eighty normalized characters; unusual Unicode uppercase expansion can exceed that limit. Unfiltered publication still retains the full recipient branch snapshot.

## Read a message

1. Sign in as an intended student and open **Notifications**.
2. Click **Refresh feed**. The card is labeled as a drive update or reminder and includes the drive/company context.
3. Use **Open related page** to reach the student's applications workspace.
4. Click **Mark as read**. Repeating this action is harmless. The officer's refreshed delivery history shows the recorded read time.

An in-app record is not proof of email delivery, device notification, attendance or that a student understood the message. Read status means the student explicitly marked the item as read; simply displaying the feed does not mark it read.

## History and retries

The audience is captured when publication succeeds and is not expanded by later applications, approvals, profile edits or interview changes. Message and recipient snapshots are retained. To correct a published message, publish a new update that clearly identifies the correction; this release does not edit, retract or delete published notices.

While the draft remains open, the browser retains a publication identifier on an uncertain network result and locks editing/preview until the same attempt is resolved. Retrying that publication returns its existing result instead of sending duplicates. Closing, reloading or leaving the draft loses that local identifier; first check published history before creating another notice. Reusing an identifier with different content is rejected. The server checks the preview again before publishing and refuses a changed audience/content snapshot; preview once more before retrying that case. Announcement, frozen recipients and feed records are committed together, so a failed transaction does not leave a partial delivery.

## Safe walkthrough

The prepared live fixture uses archived **Demo College 1** only: **Synthetic Announcement Workflow Check 2026-10-04 (#18)**, audience **Drive applicants**, branch **CSE**. It has one submitted test application (#2) from existing **Synthetic Phase 4 Lifecycle Check (#4805)**. Preview must show exactly that one recipient before publishing. Use title **Synthetic announcement verification** and message **No action required. This is a synthetic in-app workflow verification.** Record the resulting announcement number, read its owning-student feed copy, mark it read and refresh the officer's delivery history. After verification, withdraw the test application with an explanatory reason; preserve history rather than deleting records. Once withdrawn, this applicant audience is empty; do not claim it remains a reusable active fixture. Check existing publication history before sending another test notice.

The older **Synthetic Phase 4 Lifecycle Drive (#17)** can demonstrate scheduled-student targeting, but its preview may include other scheduled students or may be empty after outcomes were recorded. Do not publish to an unexpected audience. A historical selected/completed interview does not belong to that audience. Do not change a real account or interview just to generate test recipients.

Local integration fixtures are synthetic records in an explicitly enabled localhost PostgreSQL database. Live verification must distinguish public route/policy checks, authenticated reads, and actual publication/read receipt. The real Gmail inbox-verification check remains a separate unfinished account-onboarding task.
