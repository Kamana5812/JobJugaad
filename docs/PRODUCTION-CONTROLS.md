# Account security and responsible-data controls

This release adds persisted login/signup limits, server-side session revocation, owned exports and a human-reviewed account-closure workflow. It does not certify production security or complete legal erasure.

Login counts successful and failed attempts: eight per email per fifteen minutes, plus one thousand per college. Signup permits three attempts per email per hour and two hundred per college. Keys are HMAC hashes; application college filters and FORCE RLS apply to the counters. Fixed windows and rotating addresses remain limitations; there is no global network firewall claim. Test quota relaxation requires both an explicit test flag and a loopback database.

Sign out increments the user's session version, invalidating all previously issued sessions on subsequent authenticated requests. If the server cannot confirm this, the interface reports the failure and permits a clearly labeled browser-only sign-out. Password recovery preserves role and college and also revokes older sessions. Actual inbox receipt remains an owner acceptance check.

Account & data exports directly owned JSON records without passwords, authentication tokens or other candidates. Private PDFs use existing authenticated downloads. A deletion request requires a reason and explicit confirmation; pending requests can be withdrawn. Staff can reject with a reason or restrict the account, which blocks login, revokes sessions and opens a thirty-day erasure review. Restriction does not erase placement/audit records or backups. Administrator closure requires owner-managed succession. Final erasure, college-specific retention grounds and backup erasure remain administrative work; do not present restriction as completed deletion.

The public Privacy & retention page describes recorded data, access, purposes, providers, synthetic/scoring limitations and these controls. Expired security records are eligible for an explicit maintenance cleanup after seven days. No cleanup or real-account restriction was performed during implementation.

New tenant tables: auth_limits and data_requests. Both carry college_id, application filters, composite tenant ownership where applicable, and atomic ENABLE/FORCE college_isolation policies. Total schema inventory: 34 tenant tables.
