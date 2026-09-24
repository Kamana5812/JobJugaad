# Landing and role-selection preview

Status: local review preview on `feature/role-navigation`; not a production release.

1. Open http://127.0.0.1:5174/ and scroll through the hero, before/after, three portals, and explained synthetic matching example.
2. Click **Get Started** or **Login**. Three role cards appear before any form fields.
3. Choose **Student**, **Recruiter** or **Admin**. The selected portal stays visible beside the form. Students/recruiters can toggle login/signup; admin can only log in.
4. Click **Choose a different role** to return to the three cards. Each landing **Sign in as…** link preselects its role.
5. Existing authenticated accounts open their verified portal: `/student`, `/recruiter`, `/admin`. Role selection grants no permissions. Existing `/student/profile`, `/login`, `/signup`, and recruiter signup links redirect compatibly.

The preview uses the existing Render API through Vite's optional development proxy. Data submitted in forms goes to that existing backend. Production CORS is unchanged. Existing dashboard content is preserved pending visual approval; no new backend features or signup permissions were introduced.

## Validation

- `node frontend/scripts/check-navigation.mjs`: 18 checks covering initial role screen, role-specific form fields, admin signup denial, request endpoint/payload wiring, returned-role destinations, wrong-role/anonymous guards and saved example fidelity.
- Vite production build passes.
- Browser automation fails kernel initialization on this machine; these are component-rendering and request-wiring checks, not simulated browser clicks or visual screenshots.

## Next after review

Generate the remaining three requested hero illustrations and apply approved visual patterns to existing dashboards, preserving full score explanations, model limitations and access controls. This preview intentionally stops before that work.
