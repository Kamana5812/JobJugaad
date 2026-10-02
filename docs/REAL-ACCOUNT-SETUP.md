# Real college account setup

The requested college is **College of Engineering Bhubaneswar · BPUT code 219 · tenant ID 10219**. Its directory entry comes from BPUT’s 2022–23 snapshot; current affiliation and institutional authorization are not automatically certified by JobJugaad.

Real account flow: signup → verify inbox → submit affiliation reference with consent → administrator approves/rejects with reason → profile/company → drive → application → recruiter shortlist → administrator proposes/approves interview → recorded outcome → offer stages → analytics. The directory and matching suggestions alone never confer college membership or an offer.

## Resend connection (service owner)

The owner selected Resend's **default test sender**, `onboarding@resend.dev`, with **kamnaa313@gmail.com** as the test recipient. That Gmail address must be the email on your Resend account. It is not the sender. This setup can activate only that inbox; it cannot yet onboard other students or recruiters. Use Resend's HTTPS API on the existing Render Free service; no Gmail OAuth or SMTP app password is needed.

1. Sign in to [Resend](https://resend.com/), open **API Keys → Create API Key**, and create a key with **Sending access**. Keep the real key private. The masked example in chat is not a usable key.
2. Open [Render service Environment](https://dashboard.render.com/web/srv-daol1s5g1s2s738prvhg/env), choose **Edit**, and add/update these values:

| Key | Value for the selected owner-only test |
|---|---|
| RESEND_API_KEY | Your real Resend API key (secret) |
| MAIL_FROM | onboarding@resend.dev |
| RESEND_TEST_RECIPIENT | kamnaa313@gmail.com |

Keep DATABASE_URL, JWT_SECRET and the existing ADMIN_ACCOUNTS configuration. Click **Save, rebuild, and deploy**. Never add the key to a VITE_ variable, source file or chat. The backend no longer uses GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET, GMAIL_REFRESH_TOKEN or SMTP_PASSWORD.

3. Register/sign in to your own college-219 account, then select **Send verification email**. Check inbox and spam, open the received JobJugaad verification link, and refresh the account. The app sends a real one-hour verification link, not the documentation's Hello World example. Environment-variable presence or an API acceptance response is not proof that the message reached your inbox. Delivery errors keep the account unverified; no automatic approval occurs.

**To onboard other users:** verify a domain you own under **Resend → Domains** using its required DNS records. After its status is verified, set MAIL_FROM to an address on that domain, for example `accounts@your-owned-domain.com` (a placeholder, not a supplied domain), and clear RESEND_TEST_RECIPIENT. Restrict your Sending access API key to that domain where available, then save/redeploy and check an actual recipient inbox. You cannot verify gmail.com or the shared vercel.app domain as your own. Do not claim real multi-user email delivery while using onboarding@resend.dev. Resend enforces domain verification and account sending limits; local checks cannot establish either. No delivery queue or password recovery is implemented here.

## Bootstrap the college administrator

1. After this release is deployed, open [student signup](https://jobjugaad.vercel.app/auth?role=student&mode=signup), select **College of Engineering Bhubaneswar · 219**, and register **kamnaa313@gmail.com** with your own password. An existing Demo College 1 login is a different tenant account; passwords and profiles are not copied. If this email already has an account in college 219, sign in instead.
2. On the activation screen select **Send verification email**, open the received link, then refresh the account. The account remains outside placement workflows until approval/admin provisioning.
3. Only after the account exists and the email is verified, update Render’s server-side **ADMIN_ACCOUNTS** to include **{"email":"kamnaa313@gmail.com","college_id":10219}**. Preserve any deliberately retained existing administrator entry. Example retaining the old demo administrator:

```json
[{"email":"kamnaa313@gmail.com","college_id":1},{"email":"kamnaa313@gmail.com","college_id":10219}]
```

4. Save/redeploy, then sign in through the **Admin** portal using college 219. The server allowlist grants administrator authority; inbox verification is still mandatory. This is an owner-provisioned college workspace, not proof that the college has officially endorsed the service. There is no public admin signup.
5. In **Account approvals**, review verified student/recruiter requests using your college’s agreed enrollment/company checks. Record a reason. Access can be revoked; the next protected API request checks the current approval state even with an older JWT.

## Real hiring workflow

- Student/recruiter signup does not generate synthetic evidence, drives or offers. Existing synthetic records remain only in demo tenants 1/2. Startup seeding is disabled by default; ALLOW_DEMO_SIGNUPS and SEED_DEMO_DATA are local regression opt-ins, not normal deployment settings.
- Approved students save their own academics, skills, projects and existing external assessment results. Resume upload extracts readable PDF text for review; it does not automatically verify qualifications.
- Approved recruiters create their company profile and college drives, then review student applications. Matching uses the existing explained keyword/weighted rules and approved student pool; no scoring weights or trained models are changed.
- Students apply from College drives. Recruiters explicitly shortlist an application with a reason. Administrators choose the applicant under Scheduling → Recruiter-shortlisted applicants, propose a time and approve it after deterministic availability checks. A score or matching override alone is not an application shortlist.
- Students see confirmed bookings under My interviews. Outcomes can be recorded only after the scheduled end. Selected is separate from an offer.
- Administrators create an offer from a selected interview, issue the letter status, students record acceptance/document submission, administrators record verification and joining. These are human declarations; files are exchanged through the college’s agreed channel.
- Hiring notifications are recorded in-app only; only account-verification email uses Resend delivery. Analytics describe recorded outcomes, not verified employment or real-data model accuracy.

## Technical safeguards and limits

account_access, account_access_events and email_verification_tokens each carry college_id, application filters, composite tenant foreign keys and ENABLE/FORCE college_isolation RLS. Raw verification tokens exist transiently in the email/link; only SHA-256 digests are stored, expire in one hour, and are replaced on resend. The link uses a browser fragment, which is cleared from the address bar before verification. Requests are limited to one per minute and ten per account per day. Review actions require versions and reasons; history remains. There is no claim of absolute security, verified institutional partnership, delivered email before a real inbox check, or production operational certification.

Sources: [Resend send API](https://resend.com/docs/api-reference/emails/send-email), [default sender recipient restriction](https://resend.com/docs/knowledge-base/403-error-resend-dev-domain), [domain verification](https://resend.com/docs/dashboard/domains/introduction), [idempotency keys](https://resend.com/docs/dashboard/emails/idempotency-keys), [Render Free restrictions](https://render.com/docs/free).
