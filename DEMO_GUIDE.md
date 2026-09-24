# JobJugaad — exact demo clicks

**Open [the live app](https://jobjugaad.vercel.app) about five minutes before your presentation.** Use Demo College 1 for every login below. Read [JUDGE_REVIEW.md](JUDGE_REVIEW.md) aloud during rehearsal. Say: “Explainability-first placement support, with weighted rules, visible evidence and human decisions.”

## Accounts and named fixtures

Use the existing private synthetic student/recruiter credentials from the local, ignored `.local/phase4-live-test.json` file (`student` and `recruiter` entries). Never project that file, upload it, paste credentials into a public document or commit it. Use your existing allowlisted administrator account for Command Center. These are three different roles; log out and log back in when switching roles. Seeded cohort passwords are unshared, so do not attempt to log in as Synthetic Student 301.

| Purpose | Exact fixture |
|---|---|
| Interactive student | **Synthetic Phase 4 Lifecycle Check**, student **#4805** |
| Recruiter/company | **Synthetic Phase 4 Workflow Company** |
| Existing drive | **Synthetic Phase 4 Lifecycle Drive**, drive **#17**, CTC **6.50 LPA** |
| Completed lifecycle | Interview **#7556** → offer **#2385**, already joined |
| Seeded support example | **Synthetic Support Student 01**, target **Simulated Cloud Support Track** |
| Original seeded overlap | **Synthetic Support Student 01**, **Simulated Python Backend Engineer** and **Simulated React Frontend Engineer**, **demo hall / demo panel**, seed keys `phase3-double-booking-a/b` |
| Fresh rehearsal drive | **Synthetic Final Demo Drive — Run 1** (new ID appears after creation; record it) |

The 4,800 synthetic cohort and 45 companies come from seed.py. The #4805/#17 lifecycle fixture was separately created for the authorized synthetic live walkthrough. They are all fictional demonstration records, not hiring evidence. The original overlap was already resolved during Phase 3; a restart will not recreate it.

## 1. Profiling — student

1. Open `/login`. Enter the private synthetic **student** credentials, select **Demo College 1**, then **Log in**.
2. Open **My profile**. Confirm the name is **Synthetic Phase 4 Lifecycle Check** before editing anything.
3. At **Kitne Ready Ho?**, show the current band, explanation, all six rows of **Why this score? Every contributing factor**, and **Your Next Jugaad**. Describe the 30/20/15/15/10/10 weighted rule, not a placement prediction.
4. Scroll to **02 Your resume, readable.** Click **Resume PDF**, choose the existing local `.local/synthetic-resume.pdf` synthetic sample, then **Upload & extract text**. Expand **Review saved resume text**. Explain that text extraction does not invent skills or recalculate readiness by itself.
5. For an editable demonstration, change the existing Python proficiency from 80 to 81, then click **Save profile & recalculate**. Show the changed technical factor and total. Restore 80 and save again so the fixture stays reproducible. Do not edit the frozen evaluation cohort.
6. Click **Log out**.

## 2. Matching — recruiter

1. Log in with the private synthetic **recruiter** credentials and **Demo College 1**. The page title is **Talent Finder**.
2. In the drive list select **Synthetic Phase 4 Lifecycle Drive**. Confirm CTC 6.50, branch CSE, minimum CGPA 6 and Python/SQL targets 60.
3. Click **Run AI Matching**. Read the adjacent disclosure: keyword matching and a weighted rule, no trained model, unvalidated starting weights.
4. In **Candidate view**, keep **Shortlisted for review**. Use the first named synthetic candidate identified in the dated fixture check below. Show the score **together with** the five-row factor table and explanation. Expand **Kahan Kami Hai? · Skill-by-skill comparison**.
5. Change **Candidate view** to **Excluded / manually rejected**. Use the named excluded fixture below. Read the whole **Below Threshold** explanation and missing requirements; do not present a diagnostic score as proof of eligibility.
6. Optional human decision: expand **Human review · promote or reject**, choose **Promote to shortlist**, enter `Synthetic demonstration: recruiter reviewed the stated gap`, then **Record decision**. Expand **Audit history → Evidence at decision time** to show the preserved score, factors and explanation. This persists a demonstration override; it does not improve the calculated score. Do not do this to a real profile.
7. For the fast replay, continue to Scheduling with drive #17. For a fresh live offer, first complete the next subsection.

### Fresh lifecycle preparation (only when demonstrating new writes)

1. In **Create a drive**, enter **Synthetic Final Demo Drive — Run 1**. Use a new Run number on subsequent rehearsals.
2. Enter CTC **6.50**, minimum CGPA **6**, maximum backlogs **0**, eligible branches **CSE**.
3. Set Skill 1 **python**, target **60**. Click **Add skill**, enter **sql**, target **60**. Leave scoring settings at their displayed defaults.
4. Click **Create drive**, record the displayed drive ID, then **Run AI Matching**. This uses the same seeded population and requirements as #17.
5. Use this exact new drive title/ID through scheduling and offer creation below. Offer #2385 is already closed and cannot be used for another acceptance/joining demonstration.
6. Log out, then log in with your existing administrator account, **Demo College 1**.

## 3. Scheduling — administrator

### Show a real constraint conflict without restoring old double bookings

1. Open **Command Center → Scheduling → 02 Propose an interview**. Ensure this is a new interview, not a reschedule form.
2. Choose **Simulated Python Backend Engineer** and **Synthetic Support Student 01**. Set **Requested start** to a future date/time you can read clearly, duration **5**, venue **Final Demo Conflict Room**, panel **Final Demo Conflict Panel**. Write down that exact start as **T**.
3. Click **Check availability**. If a different time is suggested, use that cleared time as T. Click **Create pending proposal**.
4. Under **03 Pending approval**, find the same student/drive. Enter `Synthetic final demo: establish occupied slot`, then **Approve proposal #…**. Confirm it appears scheduled in **04 Interview calendar** and copy its actual start as T.
5. Return to **02 Propose an interview**. Choose **Simulated React Frontend Engineer**, the **same student**, **same T**, **5 minutes**, **same room**, **same panel**. Click **Check availability**.
6. Read the student/venue/panel and overlapping-drive conflict explanation, then the next clear slot. If no other bookings interfere, the alternative is T + 5 minutes; use the actual returned time, not a promised fixed answer.
7. Click **Create pending proposal**. The calendar remains unchanged until approval. In **03 Pending approval**, enter `Synthetic final demo: approve conflict-free alternative` and click **Approve proposal #…**. Show **Jugaad Ho Gaya ✓**, then both non-overlapping bookings and **05 Calendar review history**.

The fresh scenario deliberately requests a collision but never stores an overlapping confirmed booking. The original seed deliberately imported a real double booking; its resolved history remains the evidence for that separate requirement. Pending proposals do not reserve rooms or panels. Campus working hours are not modeled.

### Continue the same student's fresh offer journey

1. In **02 Propose an interview**, choose **Synthetic Final Demo Drive — Run 1** (the recorded new ID) and **Synthetic Phase 4 Lifecycle Check (#4805)**.
2. Set **today's date**, a start about one minute ahead, duration **5**, venue **Final Demo Lifecycle Room**, panel **Final Demo Lifecycle Panel**. The default date is tomorrow: change it deliberately. All displayed times use your browser timezone.
3. Click **Check availability**, then **Create pending proposal**. Under **03 Pending approval**, enter `Synthetic final demo lifecycle verification` and click **Approve proposal #…**.
4. In **04 Interview calendar**, locate the same student and new drive, and note the new interview ID and **end time**. A saved proposal alone is not a confirmed booking.
5. **Wait until the displayed end time has passed.** While waiting, show the original completed offer #2385 or the rule-based support evidence in Analytics below. Do not try to bypass the time rule or mark the wrong interview selected.
6. Expand **Record outcome or cancellation** on the new interview. Choose **Selected**, enter `Synthetic final demo: interview completed and selected`, then click **Save interview status**. Confirm the inline saved message and selected status. Selected is not yet an offer or placement.

For a short replay without new lifecycle writes, skip these six steps and use completed interview #7556/offer #2385. Old non-scheduled calendar records show only the latest 50, so an older #7556 may move out of that view; the offer history remains available.

## 4. Offer — administrator → student → administrator

**Fast replay:** open **Offers → College offers**, locate **Offer #2385** under **Synthetic Phase 4 Lifecycle Drive**, and expand **Stage history**. Show issued / submitted / verified / accepted / joined and all six actions. This is an already completed journey; no new action is available on a closed offer. The student sees it under **My offers**, with its simulated messages under **Notifications**.

**New live journey:** use the new drive/interview from the prior section.

1. Administrator: **Command Center → Offers → Create an offer**. In **Find selected student**, enter `Synthetic Phase 4 Lifecycle Check`, then click **Search**.
2. In **Selected interview**, choose that student plus **Synthetic Final Demo Drive — Run 1** and the correct new interview ID. Leave **Offer CTC** empty to use **6.50 LPA**. Enter `Synthetic final demo: create offer after selection`, then **Create draft offer**. Note the new offer ID. Do not select another student's card or enter 10000 as CTC.
3. On that exact offer card, choose **Record an action → Record letter issued**, enter `Synthetic final demo: letter issued externally`, then **Confirm action**. Verify **Offer letter: issued**.
4. Log out and log in as synthetic **student #4805**, Demo College 1. Click **My offers** and locate the new drive/offer ID.
5. Choose **Accept offer**, enter `Synthetic final demo: student accepts this offer`, click **Confirm action**. Verify **Acceptance: accepted**.
6. Choose **Record documents submitted**, enter `Synthetic final demo: external document submission declared`, click **Confirm action**. Verify **Documents: submitted**. No document files are uploaded here.
7. Click **Notifications**. Show the new interview/offer records, their in-app-only disclosure and **Mark as read**. No email/SMS was sent.
8. Log out and log in as the administrator. **Command Center → Offers**; locate the same new offer ID. Select **Record documents verified**, enter `Synthetic final demo: external verification recorded`, and **Confirm action**.
9. Select **Record joined**, enter `Synthetic final demo: joining recorded by administrator`, and **Confirm action**. Show the five separate completed stages and **Stage history**. This persists a fictional workflow record, not a validated real placement.

## 5. Analytics — administrator

1. Click **Overview → Refresh dashboard**.
2. Show the four KPI tiles. Explain that the placement percentage is an **accepted-offer proxy**, not proof of joining.
3. Scroll through the branch and skill Recharts plots and their tables. These show **shortlist conversion**, not placement conversion. Show the written numerator/denominator and synthetic-data disclosures.
4. At **04 Recorded offer outcomes**, read the current values for **Students with accepted offers**, **Students recorded joined**, and **Offers (all stages)**. The user-verified 2026-09-23 snapshot was 1,418 / 701 / 2,385; it is a historical snapshot, not a hardcoded target. Another offer for already-joined #4805 can increase offers without increasing distinct accepted/joined students.
5. Read **CTC for active accepted offers** separately from advertised drive CTC. Show the seeded-synthetic offer count and explain that manually created demonstration records are fictional too.
6. Click **Placement support**, choose **Simulated Cloud Support Track**, then **Run support checks**. Find **Synthetic Support Student 01** (use **Next** if needed). Show **Thoda Aur Jugaad Chahiye**, all three named indicators, explanation and recommended support. This count is not a risk probability or prediction of failure.
7. Open [the evaluation report](evaluations/phase4-report.md): 25/30 expected matching hits, 10/10 readiness-band agreements and 10/10 support-flag agreements. Show the five matching misses and sample limitations. Call it a **synthetic sanity check against our own assumptions**, never a validated accuracy percentage.

## Presenter checks

Verify the role, Demo College, student name/ID and drive title before every write. After any error, read the message beside the button; do not repeatedly create duplicates. A two-hour session may need a fresh login. Warm the app before the actual demo and rehearse these clicks in your own browser. Automated API/component checks are not a claim that this fresh live sequence has already been performed.

## Dated fixture check — 2026-09-23

Live read-only API lookup confirmed **Synthetic Student 1995 (#2003)** as the first shortlisted result for drive #17 and **Synthetic Student 4491 (#4499)** as the first excluded result. The excluded profile meets skill targets but has branch ECE outside the required CSE: its explanation uses the user-approved truthful no-skill-gap variant rather than inventing a missing skill. Rankings can change after profile edits or overrides; identify the student by name/ID and use Next if needed. Student #4805's readiness is Ready, with all six factors returned; offer #2385 is still present. Use the card's current values with its explanation, not a memorized bare number. These were API reads, not a new browser rehearsal.


## Updated portal entry flow (2026-09-24)

Landing → Get Started / Login → choose Student, Recruiter or Admin → sign in using the same college as registration. Admin accounts remain allowlisted. Student now opens `/student` (the old profile URL redirects); the role is shown in the top navigation alongside logout. In Career Copilot, use **Readiness**, **Skill gaps**, **Opportunities**, **Resume**, **My profile** and **Placement models** section links. Choose **Gaps / excluded roles** to inspect why an opportunity misses current rules; this read-only comparison does not make a recruiter shortlist decision. Talent Finder's **Your drives** and **Matching & candidates** links lead to the existing recorded review flow. Command Center's Scheduling, Placement support and Offers sections retain the original named fixtures and actions above.
