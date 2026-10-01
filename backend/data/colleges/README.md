# BPUT institutional directory

Source: [BPUT official website](https://www.bput.ac.in/index1.php), whose affiliated-colleges link opens the [public institutional spreadsheet](https://docs.google.com/spreadsheets/d/10dYEIBxKmSYQFH5GspqzsVCylfChE6er/edit). The official link labels this list **2022–23**. Retrieved 2026-10-02. This is a dated directory snapshot, not a verified 2026 affiliation register. Some institutions may have subsequently changed name or university status.

169 rows retain official college code, name, category, courses and district. No personal records, enrollment lists, university logos or student information are imported. Public institutional facts are used for account college selection; no partnership or institution endorsement is implied. The source does not supply an explicit redistribution license. Original source links and snapshot date remain visible.

`bput.json` records the SHA-256 of the exact downloaded CSV. Rebuild backend/frontend copies together with `backend/venv/Scripts/python.exe scripts/import-bput-colleges.py .local/bput-colleges-source.csv`. Raw download is ignored. Stable tenant IDs are `10000 + numeric college code`; existing Demo College 1/2 retain IDs 1/2. Never remap existing tenant IDs by sorting or refreshing the source. Institutional facts are public static reference data, not tenant-owned records. Every private table retains college filters and FORCE RLS.

Enrollment remains self-selected and unverified. Directory inclusion creates no accounts, recruiter drives, placement statistics or authority to administer a college. Administrators still require server-side allowlisting; production onboarding needs institution-controlled verification. New college workspaces begin empty rather than inheriting demonstration records.
