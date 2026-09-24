# JobJugaad — Design Guide

Brand identity, visual system, and voice guidelines for UI work across all three portals.

---

## 1. Brand

**Name:** JobJugaad
**Tagline:** "Placement ka Jugaad, AI ke Saath."
**Personality:** Smart · Friendly · Indian · Practical · Confident · Slightly playful · Professional underneath

The Indian identity should feel modern and authentic — not like an Independence Day poster. Avoid excessive tricolor usage; use the palette below with restraint.

---

Current navigation preview uses the user-supplied light/dark wordmarks in `frontend/src/assets/brand/`, the supplied favicon in `frontend/public/`, and a generated mascot journey in `frontend/src/assets/hero/`. Original root logos remain available. Dashboard illustration work waits for approval of the landing and role-selection preview.

## 2. Color Palette

| Color | Hex | Usage |
|---|---|---|
| Deep Navy | `#0F2A4A` | Primary brand color — headers, nav, trust/technology elements |
| Navy Dark | `#081B30` | Gradients, dark backgrounds (cover screens, hero sections) |
| Saffron Orange | `#F2802E` | Accent — CTAs, highlights, energy, key numbers |
| Saffron Deep | `#D9660F` | Hover states, secondary accents |
| Subtle Green | `#3F9166` | Success states, growth indicators, "on track" pills |
| White | `#FFFFFF` | Backgrounds, cards, simplicity |
| Paper (off-white) | `#FBFAF7` | Page background (softer than pure white) |
| Ink (text) | `#1C2733` | Body text |
| Muted (secondary text) | `#5B6B7D` | Captions, labels, metadata |
| Line (borders) | `#E2E6EC` | Dividers, table borders, card outlines |

**Status colors** (for pills/badges):
- Green (`#3F9166` on `#E2F3E9`) — on track / success / completed
- Amber (`#D9660F` on `#FDF0E3`) — warning / gap / pending
- Red (`#C53D3D` on `#FBE6E6`) — critical / high risk / rejected

---

## 3. Typography

- **Primary font:** A clean sans-serif (DejaVu Sans / system sans-serif stack — Inter or similar is a good web equivalent).
- **Headings:** Bold, Navy. Section titles use a numbered prefix in Saffron (e.g. `01 Executive Summary`).
- **Body:** Ink color, comfortable line-height (1.5) for readability on data-dense screens.
- **Monospace:** Used only for routes, code, and IDs (e.g. `/student/readiness`).

---

## 4. Core UI Components

### Score Card
Large number (Navy, bold) + small label. Used for readiness score, match %, KPI totals.

### Factor Breakdown Table
Every score-producing feature must render a table or list of contributing factors — never a lone number. This is a hard requirement, not a style preference (see `RULES.md` §3).

### Status Pills
Rounded, small, colored by status (green/amber/red) — used for skill status, interview status, offer stage.

### Flow Diagram
Horizontal step sequence with arrows (`→`), used to visualize pipelines (e.g. Resume Upload → Parsing → Structured Profile). Rendered as simple text/box rows, not heavy graphics — keep it fast to build.

### Card
White background, subtle border, light shadow, small uppercase label at top (e.g. "PROFILE GENERATED — EXAMPLE"). Used for examples, summaries, and grouped data.

### Priority Tags
Colored rectangular labels for P0/P1/P2 (red/amber/green) — used in planning docs and admin roadmap views.

---

## 5. Portal-Specific Layout Notes

### 🎓 Student — Career Copilot
- Lead with the Readiness Score at the top of the dashboard — it's the emotional anchor of the student experience.
- Skill-gap table directly below, sorted by severity (Critical → Gap → On Track).
- Opportunities shown as ranked cards with match % and quick eligibility checklist (✅/⚠).

### 🏢 Recruiter — Talent Finder
- Drive creation should feel like a short form, not a wizard — CTC, min CGPA, branches, required skills, one screen.
- "Run AI Matching" is the primary action — make it a prominent Saffron button.
- Candidate ranking table always shows rank + name/ID + match % + link to full breakdown.

### 🏛️ Admin — Placement Command Center
- Top of dashboard: 4 KPI tiles (Students, Placement %, Recruiters, Drives).
- Below: conversion tables (branch/skill), package stats, placement-support list (students who may need help), conflict alerts pending approval.
- Simulator (P2) gets its own dedicated screen — inputs on the left, projected outcome on the right. Always label output as "projected from our synthetic dataset," never as a validated forecast.

---

## 6. Voice & Terminology (Hinglish Layer)

Use these product-facing labels instead of generic AI/SaaS terms — this is what makes the brand memorable. Keep the underlying UI professional; the playfulness lives in labels and micro-copy only, not in critical data or legal/formal screens (e.g. offer letters stay formal).

| Instead of | Use |
|---|---|
| AI Recommendations | "Your Next Jugaad" |
| Skill Gap Analysis | "Kahan Kami Hai?" |
| Recommended Jobs | "Aapke Liye Sahi Jobs" |
| Conflict Resolved | "Jugaad Ho Gaya ✓" |
| Placement Readiness | "Kitne Ready Ho?" |
| AI Career Assistant | "Jugaad Dost 🤝" — **implement as a static FAQ/help panel with this label, not a built LLM chatbot** (see `PHASES.md` scope exclusions) |
| Placement Support Priority | "Thoda Aur Jugaad Chahiye" (needs a bit more support) — used only alongside the full factor breakdown, never as a standalone label |

---

## 7. Explainability as a Design Principle

Every screen that shows a score or a decision must visually answer "why," not just "what":
- Readiness Score → breakdown table + one-sentence explanation
- Match Score → factor contribution table + missing-requirement callout
- Support-priority flag → contributing factors list + recommended interventions, always framed as evidence for a human reviewer, never a verdict
- Scheduling conflict → what clashed + how it was resolved

This is both a UX principle and a hackathon judging requirement (see `PRD.md` §7).

---

## 8. Accessibility & Practicality Notes

- Maintain sufficient contrast between text and background (avoid light text on light backgrounds, or the reverse — this was an early cover-page mistake, corrected by placing the logo on a white card against the navy hero).
- Don't rely on color alone for status — always pair a pill color with a label or icon (✅ ⚠ ❌).
- Keep charts simple (bar/line/pie via Recharts) — avoid overly dense visualizations under demo time pressure.
