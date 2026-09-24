# Approved portal navigation

The user approved the landing and role-selection design on 2026-09-24. All three dashboard updates are deployed in application release 4b58105/API 0.9.0 at https://jobjugaad.vercel.app. All 55 backend tests, 18 navigation checks, 19 dashboard rendering checks and 16 live checks passed; public evidence is in `evaluations/navigation-live-security.json`.

## Flow

1. Open JobJugaad and scroll through the hero, before/after, three portals and explained synthetic matching example.
2. Click **Get Started** or **Login**. Three role cards appear before any form fields.
3. Choose **Student**, **Recruiter** or **Admin**. The portal identity remains visible beside the form. Student/recruiter signup reuse their existing endpoints; admin is sign-in only.
4. Successful login opens the verified account role's dashboard, regardless of the selected card. Wrong-role routes redirect to the authorized portal. Legacy links remain compatible.
5. **Career Copilot** (`/student`): profile summary → explained readiness → selected-drive skill gaps → ranked opportunities → resume/profile editor → separately explained BTech/MBA models. Save profile changes to refresh comparisons. The excluded view names gaps; comparisons do not submit applications or change recruiter decisions.
6. **Talent Finder** (`/recruiter`): choose a drive → Run AI Matching (explicit keyword/weighted-rule disclosure) → review ranked explanations/overrides. Use section links to create another drive or edit company details.
7. **Placement Command Center** (`/admin`): KPI tiles, current conflict summaries, branch/skill charts, offer outcomes and placement-support evidence. Scheduling / Placement support / Offers remain dedicated sections with existing approval/audit flows.

All three pages scroll normally and have a role-specific banner and shared role navigation/logout. Generated illustrations are decorative, not results. All four assets and prompts are in `frontend/src/assets/hero/README.md`.

## Checks

- `node frontend/scripts/check-navigation.mjs`: role selection, form scope, admin restrictions, existing request payloads, server-role destinations and route guards.
- With the existing localhost test database environment (`ALLOW_TEST_DATABASE=yes`), run `backend/venv/Scripts/python.exe backend/tests/export_dashboard_fixture.py`, then `node frontend/scripts/check-dashboards.mjs` for rendering checks using actual saved synthetic records. The exported fixture stays in ignored `.local/` and cannot be generated from production by this helper.
- Backend opportunity tests verify rule parity, pagination, exclusions, missing evidence, ownership/role/college checks, unchanged recruiter snapshots and independent RLS.
- Browser automation cannot initialize on this machine. Component rendering and API tests are not browser click/visual verification.
