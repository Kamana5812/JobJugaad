# Real college account setup

The requested college is **College of Engineering Bhubaneswar · BPUT code 219 · tenant ID 10219**. Its directory entry comes from BPUT’s 2022–23 snapshot; current affiliation and institutional authorization are not automatically certified by JobJugaad.

Real account flow: signup → verify inbox → submit affiliation reference with consent → administrator approves/rejects with reason → profile/company → drive → application → recruiter shortlist → administrator proposes/approves interview → recorded outcome → offer stages → analytics. The directory and matching suggestions alone never confer college membership or an offer.

## Gmail API connection (service owner)

Use **kamnaa313@gmail.com** as the sending account. No app password is needed for this API option. Gmail SMTP cannot run on Render Free because ports 25, 465 and 587 are blocked. Google Gmail API sends through HTTPS instead.

1. Open [Google Cloud Console](https://console.cloud.google.com/), create/select a JobJugaad project, then **APIs & Services → Library → Gmail API → Enable**.
2. Open **Google Auth Platform** (or APIs & Services → OAuth consent screen). Configure Branding with the app name and support/contact email. Choose **External** audience. For initial testing, add **only kamnaa313@gmail.com** as a test user. Under Data Access add **https://www.googleapis.com/auth/gmail.send**. This is send-only permission; do not grant inbox-reading or full-mailbox scopes. Only the service owner connects Gmail; student/recruiter users do not authorize Google.
3. In **Clients → Create client**, choose **Web application**. Add the authorized redirect URI **https://developers.google.com/oauthplayground**. Copy the client ID and client secret privately; do not paste them into chat or commit them.
4. Open [Google OAuth Playground](https://developers.google.com/oauthplayground/). Open its settings gear, enable **Use your own OAuth credentials**, and enter your client ID/secret there. Use **Offline** access and consent prompt. In Step 1 enter **https://www.googleapis.com/auth/gmail.send** and authorize as kamnaa313@gmail.com. In Step 2 select **Exchange authorization code for tokens**. Keep the refresh token private. The playground’s default shared client is unsuitable for the deployed integration; use your own credentials.
5. In [Render service Environment](https://dashboard.render.com/web/srv-daol1s5g1s2s738prvhg/env), add these four values:

| Key | Value |
|---|---|
| MAIL_FROM | kamnaa313@gmail.com |
| GMAIL_CLIENT_ID | Your OAuth client ID |
| GMAIL_CLIENT_SECRET | Your OAuth client secret |
| GMAIL_REFRESH_TOKEN | Your refresh token |

Keep DATABASE_URL, JWT_SECRET and the existing ADMIN_ACCOUNTS configuration. Click **Save, rebuild, and deploy**. Do not use VITE_ variables for secrets; frontend bundles are public. SMTP_PASSWORD / RESEND_API_KEY are not used by this implementation.

6. Confirm that a verification email actually arrives and its link verifies the correct tenant. Environment-variable presence alone is not proof of delivery. Google can reject/revoke credentials; the app returns a generic delivery error and leaves the account unverified.

**Testing versus sustained use:** Google External apps in Testing issue refresh tokens expiring after seven days for Gmail scopes. Reauthorization is needed while Testing. For sustained use, review Google’s publishing/verification requirements and change the OAuth app’s publishing status as appropriate, then reconnect with your own client. Do not claim perpetual delivery or Google verification. Gmail account sending limits, revocation, consent requirements and Render cold starts still apply. No delivery queue or password recovery is implemented here.

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
- Hiring notifications are recorded in-app only; only account-verification email uses Gmail delivery. Analytics describe recorded outcomes, not verified employment or real-data model accuracy.

## Technical safeguards and limits

account_access, account_access_events and email_verification_tokens each carry college_id, application filters, composite tenant foreign keys and ENABLE/FORCE college_isolation RLS. Raw verification tokens exist transiently in the email/link; only SHA-256 digests are stored, expire in one hour, and are replaced on resend. The link uses a browser fragment, which is cleared from the address bar before verification. Requests are limited to one per minute and ten per account per day. Review actions require versions and reasons; history remains. There is no claim of absolute security, verified institutional partnership, delivered email before a real inbox check, or production operational certification.

Sources: [Gmail send API](https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.messages/send), [Google OAuth web server/refresh flow](https://developers.google.com/identity/protocols/oauth2/web-server), [refresh-token expiration](https://developers.google.com/identity/protocols/oauth2), [Render Free restrictions](https://render.com/docs/free).
