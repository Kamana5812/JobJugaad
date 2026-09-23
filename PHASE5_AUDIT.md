# Phase 5 final audit

Date: 2026-09-23. Release `c3d7a57` is deployed on Vercel and Render (API 0.6.0). Live verification completed at **2026-09-23T15:19:27.317217+00:00**; [machine-readable public evidence](evaluations/phase5-security.json). This is a correctness/configuration audit, not a production security certification or predictive accuracy assessment.

## Tenant isolation: actual PostgreSQL catalog

| Multi-tenant table | college_id | RLS | Policy | USING / WITH CHECK | Evidence status |
|---|---|---|---|---|---|
| `users` | Present | ENABLE + FORCE | `college_isolation` | Scoped / scoped | Verified local + live |
| `students` | Present | ENABLE + FORCE | `college_isolation` | Scoped / scoped | Verified local + live |
| `student_skills` | Present | ENABLE + FORCE | `college_isolation` | Scoped / scoped | Verified local + live |
| `projects` | Present | ENABLE + FORCE | `college_isolation` | Scoped / scoped | Verified local + live |
| `certifications` | Present | ENABLE + FORCE | `college_isolation` | Scoped / scoped | Verified local + live |
| `companies` | Present | ENABLE + FORCE | `college_isolation` | Scoped / scoped | Verified local + live |
| `jobs` | Present | ENABLE + FORCE | `college_isolation` | Scoped / scoped | Verified local + live |
| `matches` | Present | ENABLE + FORCE | `college_isolation` | Scoped / scoped | Verified local + live |
| `match_overrides` | Present | ENABLE + FORCE | `college_isolation` | Scoped / scoped | Verified local + live |
| `schedules` | Present | ENABLE + FORCE | `college_isolation` | Scoped / scoped | Verified local + live |
| `interviews` | Present | ENABLE + FORCE | `college_isolation` | Scoped / scoped | Verified local + live |
| `schedule_events` | Present | ENABLE + FORCE | `college_isolation` | Scoped / scoped | Verified local + live |
| `risk_predictions` | Present | ENABLE + FORCE | `college_isolation` | Scoped / scoped | Verified local + live |
| `support_reviews` | Present | ENABLE + FORCE | `college_isolation` | Scoped / scoped | Verified local + live |
| `offers` | Present | ENABLE + FORCE | `college_isolation` | Scoped / scoped | Verified local + live |
| `offer_events` | Present | ENABLE + FORCE | `college_isolation` | Scoped / scoped | Verified local + live |
| `notifications` | Present | ENABLE + FORCE | `college_isolation` | Scoped / scoped | Verified local + live |

The runtime role is neither superuser nor BYPASSRLS. Each table has exactly one ALL-command, public-role policy with both predicates equal to `college_id = NULLIF(current_setting('app.college_id', true), '')::integer`. The catalog audit rejects missing/extra tenant tables, missing or additional policies, weakened predicates and disabled/unforced RLS. Startup verifies before committing schema initialization; `/health` repeats the read-only catalog check and returns 503 on failure. No tenant records or credentials are exposed.

Application filtering remains in auth.py, admin_access.py, routers/auth.py and routers/recruiters.py, plus engines/profile.py, talent.py, scheduling.py, support.py, offers.py, notifications.py and analytics.py. Every tenant query retains college scope; writes carry tenant IDs, and relationship constraints include the college. Ownership and role checks are additional restrictions within a college. Schema/catalog operations and deliberately unfiltered local RLS tests are documented exceptions to tenant-data query syntax.

Independent local integration tests omit application filters to prove database enforcement, reject cross-college writes/references and verify context resets. Phase 1 live cross-college blocking was independently confirmed by the user. The new drift test temporarily weakens local test policies inside rolled-back transactions and verifies rejection; it does not change production policies.

## CORS

The only allowed production origin is `https://jobjugaad.vercel.app`. Explicit methods: GET, POST, PUT, OPTIONS. Explicit request headers: Authorization, Content-Type (the middleware also handles standard CORS safelisted headers). Credentials/cookies are disabled. No wildcard remains in the runtime middleware. Exact-origin, foreign-origin, lookalike-domain and localhost checks pass locally and live: Vercel preflight returns 200 with its exact origin; the other three return 400 with no allow-origin header. Disallowed-method checks pass locally. Local Vite uses `/api` proxying to port 8000; preview origins are not implicitly trusted. CORS is not authentication.

## Score-producing screens

| Screen/component | Visible evidence with the number | Result |
|---|---|---|
| Student profile / ReadinessCard | Six factors, normalized inputs, weights, points, missing evidence, band, sentence, next step and rule methodology | Pass |
| Recruiter shortlisted/excluded candidate / CandidateCard + FactorTable | Five factors and contributions, explanation, missing requirements, skill comparison, next step and rule methodology | Pass |
| Recruiter override history / Evidence at decision time | Historical score, sentence and complete factor table in the same expanded section | Pass |
| Admin Placement support / SupportCard | Count out of three, all named factors/thresholds/contributions, explanation, interventions and non-probability disclosure | Pass |
| Admin analytics | Descriptive counts and accepted-offer/shortlist percentages explain numerator, denominator and limitations; no prediction score | Pass |

**Failing score screens found: none.** Support review history does not display a separate bare historical score; the current support card carries full evidence. Input score fields and configurable thresholds are inputs, not generated predictions. Expandable skill/audit sections keep each historical score and its factors together.

## UI, positioning and scope

Palette tokens use DESIGN.md's navy/saffron/green, paper/ink/muted/line and semantic status colors; replaced off-palette text shades. Numbered shared headings use a saffron prefix. Typography uses Inter/DejaVu/system sans, navy bold headings and readable body spacing. Statuses retain text labels; declined/rejected outcomes use critical styling. Existing supplied logos remain unchanged in navigation and landing/login. Hinglish labels stay in readiness, skill help, next steps, support and conflict feedback; offer actions stay formal.

No AI Mock Interview feature, route, page or engine exists. Existing interview-score inputs record assessments taken elsewhere. Jugaad Dost appears only as static FAQ/help content in student, recruiter and admin portals; there is no live chatbot or conversational endpoint. No trained classifier, LLM client, sentence-transformers or pgvector dependency is present.

Current product/pitch copy leads with explainability-first or names weighted rules/keyword matching. The explicitly user-requested **Run AI Matching** label and supplied logo tagline are preserved; the button immediately explains that it runs no trained model. Official problem-statement titles and historical decision-log quotations are source/history, not product capability claims. Removed unsupported first-mover/exclusive-feature and general-ML claims from active planning copy. Competitors exist; no uniqueness survey is claimed.

## Verification and limits

The initial complete run passed 36/37 tests; the notification test incorrectly counted another test's separately confirmed interview. Its assertion now targets the baseline interview ID; all 12 affected scheduling/support tests passed on retest, so all 37 checks have passed across the complete run and targeted retest. The final frontend production build and actual-data offer/analytics rendering passed. Security/CORS tests passed locally. Actual saved data rendered successfully for readiness, 10 candidate cards and 94 support cards with factors/explanations. A fresh browser-tool attempt failed before session creation (missing runtime assets). No browser-interaction or screenshot audit is claimed: the browser automation environment was unavailable during the earlier workflow. The user accepted Phase 4's live end-to-end behavior.

See [DEMO_GUIDE.md](DEMO_GUIDE.md), [JUDGE_REVIEW.md](JUDGE_REVIEW.md), [scalability statement](ARCHITECTURE.md#scalability--deployment-approach) and [evaluation report](evaluations/phase4-report.md). The presenter still needs to rehearse aloud and warm the app before the actual demo. Scores use unvalidated rules and synthetic data; notification delivery is simulated; document stages are human declarations; no first-mover, calibrated confidence or real-world accuracy claim is made.

## Deployed result

- [Frontend](https://jobjugaad.vercel.app): HTTP 200, Vercel reports successful deployment, production bundle targets the live Render API and contains Phase 5 status styles.
- [Backend health / policy report](https://jobjugaad-api.onrender.com/health): connected, all 17 policies verified, restricted runtime role. [API docs](https://jobjugaad-api.onrender.com/docs) identify version 0.6.0.
- Admin analytics, student readiness, recruiter company and notifications each return 401 without authentication.
- No failing score screen was found; no prohibited interview/chatbot feature was found. No new live demo records were created during Phase 5; synthetic account reads confirmed the named guide fixtures.
- Remaining presenter actions: read the judge sheet aloud, rehearse the exact clicks in your browser, and warm the service before the actual presentation. Browser automation failed before session creation, so no independent visual/browser-interaction completion is claimed.
