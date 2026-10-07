# Recruiter college workspaces

A recruiter needs one home account, not a new registration for every campus. Each college still approves its own affiliation request. Existing separately registered accounts are not merged automatically.

## Use the workflow

1. Open the recruiter signup portal. Select your **Home college**, enter your company name/industry, email and password, and create the account once. Existing recruiters can use their current real-college account as home.
2. In Activate your college workspace, send the verification email, open its link, and refresh the account. Inbox verification does not prove company affiliation.
3. Submit the home college affiliation reference/consent; that college's administrator reviews it through Command Center → Accounts.
4. Click **Your college workspaces** in onboarding, **Manage college workspaces** in Account & data, or **Switch college / request access** in Talent Finder. Home college approval does not need to finish before requesting another college, but your email must be verified.
5. Under Request a college workspace, select the campus, enter your company affiliation reference and supporting context, tick consent, and submit. A local company profile is copied from the home name/industry. No second password or email verification is needed.
6. That campus administrator opens Command Center → Accounts, reviews the pending recruiter affiliation, and records approval/rejection with a reason. They see only their college's request.
7. Refresh approvals in Your college workspaces. Click **Open Talent Finder** on an approved college. The header identifies the current college; all drives, students, matches and applications remain scoped there.
8. Return to the workspace page to switch colleges or return home. Company profiles are campus-specific snapshots, not automatically synchronized.
9. Always sign in and request password recovery with your **home college**. Password reset or server logout revokes existing sessions across workspaces. A college rejection blocks only that college's workflow.

## Existing accounts and data controls

If the same email already has an account at another college, the request stops without changing that account. A proof-of-ownership migration is required before linking historical accounts; this release deliberately does not merge them. Archived demo accounts cannot request additional campuses. Exports include locally owned workspace directory/binding rows. Download each college's owned records separately. Recruiter deletion needs a coordinated, approved retention/succession review across its linked campuses.

## Verification

The disposable integration suite checks independent approval, audited administrator review, RLS denial without tenant scope and under the wrong tenant, owner-only workspace listing/switching, target company isolation, denial of standalone linked credentials/tokens, college rejection, disabled home accounts, home/target logout, and home password recovery. Verification-email receipt is not inferred from these simulated tests. Backup/restore coverage must include all linked colleges; restored users precede workspace references across the selected tenant set.
