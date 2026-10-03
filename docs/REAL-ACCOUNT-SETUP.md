# Real college account setup

The requested college is **College of Engineering Bhubaneswar · BPUT code 219 · tenant ID 10219**. Its directory entry comes from BPUT’s 2022–23 snapshot; current affiliation and institutional authorization are not automatically certified by JobJugaad.

Real account flow: signup → verify inbox → submit affiliation reference with consent → administrator approves/rejects with reason → profile/company → drive → application → recruiter shortlist → administrator proposes/approves interview → recorded outcome → offer stages → analytics. The directory and matching suggestions alone never confer college membership or an offer.

## Gmail API setup: no domain purchase

For the requested no-payment setup, use **sunilagrawal63323@gmail.com** as the sender through Gmail API. This can send verification links to other students' email addresses, including Gmail addresses. Only the service owner authorizes Google; students/recruiters do not need Google Cloud projects or OAuth consent. No domain purchase, Google Workspace subscription, SMTP app password or Render upgrade is needed for this small-volume setup. Standard Gmail API use currently has no additional charge within Google's quotas; Gmail sending limits still apply. JobJugaad supports this transport when **EMAIL_PROVIDER=gmail**. The default remains Resend until you explicitly select Gmail in Render; it never falls back to another provider.

**Sender change (2026-10-03):** The owner requested sunilagrawal63323@gmail.com as the Gmail sender. Authorize that mailbox and use its refresh token; changing MAIL_FROM alone is insufficient. This does not change the college administrator allowlist or migrate any account. The existing college administrator remains kamnaa313@gmail.com.

### 1. Create/select the Google project

Open [Google Cloud Console](https://console.cloud.google.com/) as **sunilagrawal63323@gmail.com**. In the project selector at the top choose **New Project**, name it **JobJugaad**, then **Create**. Select that project. If you already made a JobJugaad project during the earlier setup, reuse it. Do not activate paid services or enable billing for this setup.

### 2. Enable Gmail API

Choose **APIs & Services → Library**, search for **Gmail API**, open it, and click **Enable**. Alternatively, search for Gmail API in the console search bar, ensuring the correct project is selected.

### 3. Configure owner authorization

Choose **Google Auth Platform → Branding → Get started** (older console: **APIs & Services → OAuth consent screen**). Set app name d**JobJugaa**, user support email **sunilagrawal63323@gmail.com**, audience **External**, and contact email **sunilagrawal63323@gmail.com**. Review the displayed Google policy yourself, then complete creation.

Under **Audience → Test users → Add users**, add **only sunilagrawal63323@gmail.com**. Sunil and other students are email recipients, not Google OAuth test users. Under **Data Access → Add or remove scopes**, add exactly **https://www.googleapis.com/auth/gmail.send**, then update/save. This is send-only permission. Do not select gmail.readonly, gmail.modify, gmail.compose or full mailbox permission.

### 4. Create your OAuth client

Go to **Google Auth Platform → Clients → Create client**. Choose **Web application**, name it **JobJugaad mail setup**, and add this exact **Authorized redirect URI**, without a trailing slash:

```text
https://developers.google.com/oauthplayground
```

Click **Create**. Keep the client ID and client secret privately; the secret is shown when the client is created. Store them outside the public repository and do not paste them into chat. No authorized JavaScript origin is needed for this owner-only setup flow.

### 5. Authorize your Gmail sender

Open [Google OAuth Playground](https://developers.google.com/oauthplayground/), click the settings gear, select **Use your own OAuth credentials**, and enter your client ID and secret there. Keep **OAuth endpoints: Google**, **OAuth flow: Server-side**, **Access type: Offline**, and **Force prompt: Consent Screen**. Close the settings panel.

In Step 1 enter **https://www.googleapis.com/auth/gmail.send** in **Input your own scopes**, then click **Authorize APIs**. Choose **sunilagrawal63323@gmail.com**, inspect the requested send-only permission, and approve it yourself. If Google shows an unverified-app warning, continue only after confirming this is your own project/client and only the expected sending permission is requested. A blocked screen is not the same as a warning; do not bypass an organization policy. In Step 2 click **Exchange authorization code for tokens**. Copy the **refresh token** privately, not the short-lived access token. Use your own OAuth client; the playground's shared-client refresh token can be revoked after 24 hours. Do not share the playground URL with credentials/tokens included.

### 6. Configure Render

Open [Render service Environment](https://dashboard.render.com/web/srv-daol1s5g1s2s738prvhg/env), choose **Edit**, and set:

| Key | Value |
|---|---|
| EMAIL_PROVIDER | gmail |
| MAIL_FROM | sunilagrawal63323@gmail.com |
| GMAIL_CLIENT_ID | Your own OAuth client ID |
| GMAIL_CLIENT_SECRET | Your own client secret (private) |
| GMAIL_REFRESH_TOKEN | Your refresh token (private) |

Keep DATABASE_URL, JWT_SECRET and ADMIN_ACCOUNTS. Resend variables are ignored in Gmail mode; they do not need to be deleted. Put no secrets in Vercel or VITE_ variables. Click **Save, rebuild, and deploy**. Gmail mode is supported from API **0.11.2**; code deployment alone does not configure these values.

### 7. Check a real verification email

Sign in/register at [student signup/login](https://jobjugaad.vercel.app/auth?role=student&mode=signup) using the correct college, then click **Send verification email** on the activation screen. Check inbox/spam and open the received link. A student such as **sunilagrawal63323@gmail.com** must register their own account and click their own link; never activate it merely because someone supplied that address in chat. Refresh the account, submit the college access request, then obtain administrator approval. Neither receipt nor verification is proof of enrollment. An API acceptance response does not establish inbox delivery; confirm the actual message and link.

**For continued use:** Google External projects in **Testing** issue Gmail refresh tokens that expire after seven days. Repeat Step 5 and update GMAIL_REFRESH_TOKEN while testing. Before sustained use, follow Google's app publishing/verification requirements as applicable; do not claim permanent delivery or skip required verification. Gmail account sending limits, token revocation and Render cold starts still apply. Gmail has no Resend-style idempotency key; the app does not automatically retry an ambiguous send timeout. This is account-verification mail only, with no password recovery or external hiring-notification delivery.

## Alternative: Resend connection (service owner)

Set **EMAIL_PROVIDER=resend** to use this alternative. The default when EMAIL_PROVIDER is absent remains Resend. Gmail settings are ignored in this mode.

The earlier setup selected Resend's **default test sender**, `onboarding@resend.dev`, with **kamnaa313@gmail.com** as the test recipient. That Gmail address must be the email on your Resend account. It is not the sender. This setup can activate only that inbox; it cannot yet onboard other students or recruiters. Use Resend's HTTPS API on the existing Render Free service; no Gmail OAuth or SMTP app password is needed.

1. Sign in to [Resend](https://resend.com/), open **API Keys → Create API Key**, and create a key with **Sending access**. Keep the real key private. The masked example in chat is not a usable key.
2. Open [Render service Environment](https://dashboard.render.com/web/srv-daol1s5g1s2s738prvhg/env), choose **Edit**, and add/update these values:

| Key | Value for the selected owner-only test |
|---|---|
| RESEND_API_KEY | Your real Resend API key (secret) |
| MAIL_FROM | onboarding@resend.dev |
| RESEND_TEST_RECIPIENT | kamnaa313@gmail.com |

Keep DATABASE_URL, JWT_SECRET and the existing ADMIN_ACCOUNTS configuration. Click **Save, rebuild, and deploy**. Never add the key to a VITE_ variable, source file or chat. Gmail credentials are ignored in Resend mode. SMTP_PASSWORD is unused in both modes.

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
- Hiring notifications are recorded in-app only; only account-verification email uses the selected Gmail API or Resend transport. Analytics describe recorded outcomes, not verified employment or real-data model accuracy.

## Technical safeguards and limits

account_access, account_access_events and email_verification_tokens each carry college_id, application filters, composite tenant foreign keys and ENABLE/FORCE college_isolation RLS. Raw verification tokens exist transiently in the email/link; only SHA-256 digests are stored, expire in one hour, and are replaced on resend. The link uses a browser fragment, which is cleared from the address bar before verification. Requests are limited to one per minute and ten per account per day. Review actions require versions and reasons; history remains. There is no claim of absolute security, verified institutional partnership, delivered email before a real inbox check, or production operational certification.

Sources: [Google Gmail setup](https://developers.google.com/workspace/gmail/api/quickstart/python), [Google authorization flow](https://developers.google.com/identity/protocols/oauth2/web-server), [send-only scope](https://developers.google.com/workspace/gmail/api/auth/scopes), [OAuth Playground own-client settings](https://developers.google.com/oauthplayground/), [token expiration](https://developers.google.com/identity/protocols/oauth2), [Gmail API quotas/pricing](https://developers.google.com/workspace/gmail/api/reference/quota), [Resend send API](https://resend.com/docs/api-reference/emails/send-email), [default sender recipient restriction](https://resend.com/docs/knowledge-base/403-error-resend-dev-domain), [domain verification](https://resend.com/docs/dashboard/domains/introduction), [idempotency keys](https://resend.com/docs/dashboard/emails/idempotency-keys), [Render Free restrictions](https://render.com/docs/free).
