# JobJugaad — Technical Validation
### Phases 5–6, 10–16 | Companion to RESEARCH_AUDIT.md

---

## PHASE 5 — Research Papers (15+)

All entries below were retrieved via live search. Fields marked "Not stated in available abstract" reflect genuine gaps in what's publicly accessible, not omissions on our part.

| # | Title | Authors | Year | Venue | URL | Method | Relevance to JobJugaad |
|---|---|---|---|---|---|---|---|
| 1 | Job Description and Resume Matching System Using NLP | Not fully listed in snippet | 2025/2026 | IEEE Xplore | ieeexplore.ieee.org/document/11085197 | Fine-tuned BERT for resume-JD semantic scoring; reports 97% similarity on closest match | Directly supports semantic matching layer (P2) |
| 2 | Improved Candidate-Career Matching Using Comparative Semantic Resume Analysis | Not fully listed | 2024 (282 days old at search time) | ASTESJ | astesj.com/v09/i01/p03 | NER + TF-IDF cosine similarity, RankSVM for ranking | Supports weighted-ranking design in Matching Engine |
| 3 | Career-Aware Resume Tailoring via Multi-Source RAG with Provenance Tracking | Not fully listed | 2026 | arXiv | arxiv.org/pdf/2605.05257 | Retrieval-augmented generation for resume tailoring; surveys resume-job matching evolution (lexical → embeddings → transformers) | Useful literature-review backbone; confirms embeddings are the current state of the art |
| 4 | Smart-Hiring: An Explainable End-to-End Pipeline for CV–Job Matching | Not fully listed | 2025 | arXiv | arxiv.org/pdf/2511.02537 | Document parsing + NER + contextual embeddings in shared vector space; explicitly designed for explainability, inspectable matching rationale | **Best base paper for the Matching Engine** — closest architectural analogue to JobJugaad's design |
| 5 | AI-Powered Automated Resume Screening and Job Matching System Using NLP and ML | Khatri et al. | Oct 2025 | Int'l J. of Research in Engineering, Science and Management | researchgate.net/publication/398895882 | S-BERT sentence embeddings + cosine similarity + classification rules | Supports hybrid rule+embedding design |
| 6 | CareerBERT: Matching Resumes to ESCO Jobs in a Shared Embedding Space | Not fully listed | 2025 | arXiv | arxiv.org/pdf/2503.02056 | Shared embedding space between resumes and a standardized job taxonomy (ESCO) | Model for how to structure a skill taxonomy — relevant if skill-gap analysis is formalized beyond a flat list |
| 7 | AI Resume Screening and Job Description Matching System | Bhupesh, Ravi Kumar, Rajendra Singh | 2025 | JATIR (Raffles University) | jatir.org/publishedpapers/140621_PAPER.pdf | NLTK/spaCy pipeline, TF-IDF cosine similarity, produces "match percentage + skill gap" output | Near-identical output shape to JobJugaad's proposed match score + skill gap combo — strong precedent |
| 8 | Developing Classifiers through Machine Learning Algorithms for Student Placement Prediction Based on Academic Performance | Laxmi Shanker Maurya, Shadab Hussain, Sarita Singh | 2021 | Applied Artificial Intelligence, 35(6), 403–420 | Semantic Scholar / T&F | Logistic Regression, Random Forest, KNN, SVM compared on 10th/12th/graduation marks + backlog | Directly validates Readiness/Risk scoring inputs (academic history, backlogs) |
| 9 | A Machine Learning Framework for Predicting Student Placement Outcomes | Abhinav Pathak, Murali Matcha, Manikanta Gopisetti, Shubham Joshi | 2025 | IIETA (ISI journal) | doi.org/10.18280/isi.300704 | ML framework on a public Kaggle placement dataset | Confirms public Kaggle placement datasets exist (see Phase 15) |
| 10 | Predicting College Students' Placements Based on Academic Performance Using Machine Learning Approaches | Mukesh Kumar, Nidhi Walia, Sushil Bansal, Girish Kumar, Korhan Cengiz | 2023 | Int'l J. Modern Education and Computer Science, 15(6), 1–13 | DOI 10.5815/ijmecs.2023.06.01 | Compares Logistic Regression, Gaussian Naive Bayes, Random Forest, SVM, KNN | **Best base paper for Readiness/Risk Engine** — Random Forest reported as most effective; directly transferable methodology |
| 11 | Dropout Early Warning Systems for High School Students Using Machine Learning | Not fully listed | ~2018 | ScienceDirect | sciencedirect.com/science/article/abs/pii/S0190740918309721 | Random Forest on attendance/activity data (Korea NEIS, national dataset) | Best-precedent model for At-Risk Engine's underlying technique (adapted from dropout to placement risk) |
| 12 | The Machine Learning-Based Dropout Early Warning System for Improving the Performance of Dropout Prediction | Not fully listed | 2019 | ResearchGate | researchgate.net/publication/334818622 | Addresses class imbalance via SMOTE + ensemble methods; evaluates with ROC and Precision-Recall curves | **Critical methodological citation** — explains exactly why a naive at-risk classifier will underperform, and how to fix it (see Phase 13) |
| 13 | BIAS DETECTION AND MITIGATION USING EXPLAINABLE AI IN INTELLIGENT RECRUITMENT AUTOMATION | Not fully listed | 2025 (209 days old at search) | Academia.edu | academia.edu/164630697 | SHAP for interpreting model decisions; fairness-aware pre/in-processing correction | Supports explainability + fairness claims in Matching Engine |
| 14 | Mitigating Bias in AI Model Using eXplainable AI in Terms of Hiring Process in the Industry | Noir Alsubaie, Noura Aleisa | 2024 | IEEE Access, DOI 10.1109/ACCESS.2024.0429000 | SHAP-based "glass-box" transition from black-box models; reports demographic parity improving 0.70→0.90 | Strong citation for "why explainability, not black-box ML" architectural decision |
| 15 | Explainable AI in Employment Decision-Making: A Systematic Review of Transparency Methods in Hiring Algorithms | Stephen Fabeyo | 2025 | Issues in Information Systems, 26(3), 127–135, DOI 10.48009/3_iis_2025_2025_110 | Systematic review of SHAP, LIME, decision trees, counterfactuals in hiring | Best literature-review anchor for the "Explainability" section of final documentation |
| 16 | Automated Application Processing (interview scheduling as graph coloring) | Not fully listed | 2022 | arXiv | arxiv.org/pdf/2204.08695 | Reduces interview scheduling to Graph Coloring Problem (NP-complete); compares Chaitin's algorithm, genetic algorithm, ant colony optimization | **Best base paper for Scheduling Engine** — formally validates the conflict-detection approach and names concrete algorithms to reference |
| 17 | A Model for Competence Gap Analysis | Juri L. De Coi, Eelco Herder, Arne Koesling, Christoph Lofi | ~2007 | ResearchGate | researchgate.net/publication/228873702 | IEEE Reusable Competency Definitions-based model for semi-automatic competence matching, with proficiency-level subsumption | Formal precedent for Skill Gap Engine's proficiency-level comparison logic |
| 18 | Skills Gap Analysis Model (SGAM) | Not fully listed (ODU thesis) | Not stated | Old Dominion University Digital Commons | digitalcommons.odu.edu (emse_etds/1168) | Design Science Research method; single taxonomy for position requirements + worker qualifications, quantifiable gap scoring | Direct methodological backbone for the Skill Gap Engine — "single shared taxonomy" is the key design principle to adopt |

### Determinations

1. **Best base paper overall:** *Smart-Hiring* (arXiv 2511.02537) for the Matching Engine's architecture — its explicit design for explainability and inspectability is the closest published analogue to JobJugaad's stated requirements.
2. **Best base paper for Readiness/Risk:** Kumar et al. 2023 (IJMECS) for methodology, combined with the dropout early-warning literature (#11, #12) for the at-risk-specific adaptation and the class-imbalance warning.
3. **Best base paper for Scheduling:** arXiv 2204.08695 — formally frames interview scheduling as graph coloring, which validates (and should be cited alongside) your existing rule-based/CSP design.
4. **Research gap these collectively expose:** every paper above studies one module in isolation (matching, OR readiness, OR risk, OR scheduling). None studies an integrated pipeline across all four for campus placement specifically — this is the gap JobJugaad's *combination* fills (see Phase 8 in `RESEARCH_AUDIT.md`).
5. **What existing documentation can now cite:** the Matching Engine's factor-breakdown design (papers #4, #7), the Readiness Engine's use of academic/backlog inputs (paper #8, #10), the At-Risk Engine's core technique and its known failure mode (papers #11, #12), the Scheduling Engine's CSP framing (paper #16), and the Skill Gap Engine's taxonomy approach (papers #17, #18).

---

## PHASE 6 — GitHub Implementation Research (summary; full table in RESEARCH_AUDIT.md)

Key finding, stated plainly per your instruction not to assume READMEs reflect working features: of the ~10 campus-placement repos surveyed, the overwhelming majority (Placement-Manager, campus-hire, PMS, Campus Recruitment Management System) implement **CRUD placement portals with no matching, scoring, or scheduling intelligence at all**, despite some carrying "AI" or "smart" in their names or descriptions. Only two repos (`27px/Placement-Prediction-and-Management-System` using brain.js, and `chawthinn/campus-placement-prediction` with a genuine multi-algorithm Jupyter comparison) show actual implemented prediction logic, and neither integrates it with a full placement lifecycle (scheduling, offers, etc.).

**Conclusion:** the "build everything" instinct in student hackathon/capstone projects consistently produces either (a) a well-built CRUD app with an AI feature claimed but not built, or (b) a working isolated ML notebook with no product around it. JobJugaad's P0/P1/P2 discipline (Phase 10 below) exists specifically to avoid landing in either failure mode.

---

## PHASE 10 — Refined Feature Set (P0 / P1 / P2)

Evaluated against: judge impact, user value, technical difficulty, research value, demo value, implementation time, reliability.

### 🔴 P0 — Must Build

| Feature | Why P0 |
|---|---|
| Student profile + resume parsing | Foundational; every downstream feature depends on it |
| Readiness Score with breakdown + explanation | Core explainability requirement; low technical risk (weighted formula), high judge/demo value |
| Skill Gap Analysis | Directly required by problem statement; low technical risk |
| Drive/JD creation + eligibility filtering | Foundational for recruiter side |
| Explainable Matching Engine (rule-based: eligibility + keyword skill match + weighted score + generated explanation) | **Highest judge-impact item.** Matches the exact "Below Threshold: ..." format the problem statement demands. Achievable without embeddings for MVP. |
| Conflict-aware scheduling (rule-based CSP) | Required deliverable; well-scoped, deterministic, low implementation risk per research (Phase 14) |
| Offer & documentation tracking | Required deliverable; simple state-machine, low risk |
| Placement analytics dashboard (descriptive) | Required deliverable; straightforward to build with synthetic data |

### 🟡 P1 — Should Build

| Feature | Why P1, not P0 |
|---|---|
| At-Risk Student Intelligence (rule-based thresholds, or simple Random Forest if time allows) | High research value and genuinely differentiated (Phase 4), but not required for the "minimum 3 capabilities" bar — build after P0 is solid |
| Notifications (simulated in-app) | Required deliverable but low technical risk/low judge differentiation — can slot in late |
| Recruiter/package/skill-conversion analytics | Extends the P0 analytics dashboard; incremental effort |
| Embedding-based semantic matching (sentence-transformers + pgvector) | Real differentiator per Phase 4, but adds infra complexity (vector DB, embedding model hosting) — attempt only after the rule-based Matching Engine works end-to-end |

### 🟢 P2 — Optional / Future

| Feature | Why De-Prioritized |
|---|---|
| Jugaad Simulator | Genuinely differentiated (Phase 4/8) but has no dependency from P0/P1 — build only if time remains, since a broken or fake-looking simulator is worse for credibility than not having one |
| AI Career Chatbot ("Jugaad Dost") | **Explicitly de-emphasize.** Academically validated as tractable (Campus-Connect, 78% accuracy) but commercially crowded and adds zero differentiation over what a judge has likely already seen |
| AI Mock Interview | **Explicitly de-emphasize — recommend dropping entirely for this hackathon.** The competitive research found 10+ dedicated products in this exact space (Eklavvya, Interview Pilot, Final Round AI, Google Interview Warm-Up). Building a mediocre version of a category with mature, well-funded competitors actively work against you in judging — better to have zero mock-interview feature than a visibly worse one |
| Gamified preparation | Low research value, low judge impact, purely cosmetic |
| PWA/mobile experience | Zero differentiation, pure engineering overhead for a hackathon timeframe |

**Feature to simplify, not remove:** the "AI Career Assistant" branding can remain as a UI label (per `DESIGN.md`'s Hinglish voice), but should not be built as an actual LLM-backed chatbot for this hackathon — it can be a static FAQ/help panel styled as "Jugaad Dost" without the backend complexity or the competitive exposure of a real chatbot.

---

## PHASE 11 — AI/ML Architecture Validation

Existing documentation's hybrid pipeline concept is directionally correct. Validated and refined below.

```
Hard Eligibility (deterministic rules)
CGPA + branch + backlog + graduation year
        ↓
Semantic Matching (embeddings — P1/P2 only)
Resume/profile ↔ JD via sentence-transformers + pgvector
        ↓
Weighted Feature Scoring (deterministic, P0)
Skills (keyword match) + Projects + Certifications + Academics + Assessments
        ↓
Final Ranking (deterministic sort)
        ↓
Explanation Generation (template-based, P0)
        ↓
Human Approval (TPO override — P0 UI affordance, even if simple)
```

| Component | Technique | Justification | Where LLM is NOT needed |
|---|---|---|---|
| Eligibility | Deterministic rules | No ambiguity in "CGPA ≥ 7.5" — an LLM here would be slower, less reliable, and unauditable for zero benefit | Always |
| Skill matching (P0) | Keyword/weighted overlap | Cheap, fast, fully explainable, sufficient for structured skill lists | Yes — unnecessary for MVP |
| Semantic matching (P1/P2) | Sentence-transformers (e.g., S-BERT) + pgvector, **not** a full LLM | Papers #4, #5, #6 all use embedding models, not generative LLMs, for this task — an LLM call per match is unnecessary latency/cost when an embedding similarity search does the same job | Yes — embeddings suffice; an LLM adds cost without improving matching quality here |
| Readiness/Risk scoring (P0/P1) | Weighted rules (P0) → Random Forest (P1, per paper #10) | Research shows Random Forest outperforming rules on structured/tabular data — the honest path is to state P0 uses rules and P1 *could* upgrade to Random Forest, not to call the weighted formula "AI" | Always — this is a classic tabular ML task, not a language task |
| Explanation generation | Template-based string construction (P0), not an LLM | The "Below Threshold: ..." format is a fixed template with variable slots (missing skill, benchmark gap) — an LLM call here would be slower and riskier (could hallucinate a wrong reason) for a task a template does perfectly and deterministically | Yes — this is the single most important place to explicitly reject LLM use, since a hallucinated explanation would be actively harmful to trust |
| Scheduling | Constraint satisfaction / rule-based (per paper #16) | Formally NP-complete graph-coloring problem — CSP solvers or even a well-written greedy+backtrack algorithm are the textbook-correct tool, not ML or an LLM | Always |
| At-risk classification (P1) | Rule-based thresholds (P0-lite) → simple classifier with SMOTE for class imbalance (P1, per paper #12) | Must explicitly handle class imbalance (few "at risk" students in any dataset) or the model will trivially predict "not at risk" for everyone and look accurate while being useless | LLM not applicable — tabular classification task |
| Simulator (P2) | Deterministic scenario recalculation over the synthetic dataset (per workforce-planning what-if pattern) | This is arithmetic over adjusted input distributions, not a predictive model — must be labeled honestly as a "what-if recalculation," not a forecast | Always |

**Where LLM use would be honestly justified, if attempted:** parsing unstructured, free-text resume sections into structured fields (education/experience extraction) can benefit from an LLM's flexibility over brittle regex — this is the one place in the entire pipeline where generative AI has a defensible edge over rules or embeddings, because resume formats are genuinely unstructured and varied.

---

## PHASE 12 — Matching Model Validation

Refined, technically defensible methodology (P0, no embeddings required):

```
Eligibility Score      (pass/fail gate — CGPA, branch, backlog)
        +
Skill Match Score      (weighted overlap: required vs. possessed skills)
        +
Project Relevance      (keyword overlap between project descriptions and role)
        +
Academic Fit           (CGPA normalized against role's stated minimum)
        +
Certification Fit      (binary/weighted presence of named certifications)
        +
Assessment Fit         (aptitude/mock-interview score normalized)
        ↓
Final Match Score (0–100, normalized sum of weighted components)
```

- **Normalization:** each component should be scaled to a common 0–100 range before weighting, to prevent a component measured in different units (e.g., raw CGPA out of 10 vs. a percentage skill overlap) from silently dominating the sum.
- **Weighting:** start with equal or hand-tuned weights (as in the existing docs' 32/24/15/12/8/5 example) and **state explicitly that these are unvalidated starting weights**, not empirically derived — this is honest and defensible; claiming otherwise without a labeled dataset to tune against is not.
- **Threshold:** define a minimum eligible score (e.g., 60/100) below which a candidate is auto-excluded from the ranked list, with the exclusion reason surfaced via the same explanation template.
- **Ranking:** simple descending sort on final score; no additional algorithm needed at P0 scale.
- **Confidence:** at P0, do not report a numeric "confidence" — you have no calibration data to justify one. If added later, calibrate it against how close the score is to the decision threshold, not as a separate invented metric.
- **Explanation:** template-driven, listing the top contributing and top missing factors — matches papers #4 and #7's approach.
- **Human override:** the TPO/recruiter must be able to manually promote or reject a candidate regardless of score, with that override logged — this directly answers the "can TPO override AI decisions" judge question (see `JUDGE_REVIEW.md`) and reflects the human-in-the-loop principle found throughout the fairness literature (papers #13, #14, #15).

**On accuracy:** do not invent a number. Define the evaluation protocol instead — e.g., "for a labeled subset of synthetic profiles where we define the 'expected' top-5 matches ourselves, report precision@5 and recall@5 against that self-defined ground truth," and clearly label this as a **sanity check against a synthetic ground truth**, not a real-world accuracy claim, since no real hiring outcome data exists to validate against.

---

## PHASE 13 — Readiness / Risk Model Validation

| Model | Current Approach | Should Use | Rationale |
|---|---|---|---|
| Student Readiness Score | Weighted rule (30/20/15/15/10/10) | **Keep as weighted rule for P0.** Do not call it "AI." | Fully explainable, zero training data needed, matches the "Not Ready → Developing → Ready → Highly Employable" banding requirement directly |
| Skill Gap Score | Per-skill proficiency delta vs. target role | **Keep as deterministic delta calculation**, structured per the SGAM shared-taxonomy approach (paper #18) | No ambiguity requiring ML; a shared skill taxonomy makes this comparable and auditable |
| Placement Risk Score | Not yet specified in existing docs beyond "AI recommendation" | **Hybrid: rule-based thresholds for P0 (e.g., 3+ skill gaps AND low mock score AND low activity → flag), upgrade to a Random Forest or Logistic Regression classifier for P1** trained on the synthetic dataset, using SMOTE or class weighting to address the class imbalance problem documented in paper #12 | A pure black-box classifier at P0 would be unauditable and untrainable without real historical placement outcomes; rules are honest and sufficient for a first pass. If upgraded, the class-imbalance handling is not optional — it's the single most commonly cited failure mode in this literature |
| Intervention Recommendation | Rule-based mapping from risk factors to suggested actions (e.g., "3 skill gaps → recommend training") | **Keep rule-based.** This is a lookup/mapping task, not a prediction task | No research found frames intervention *recommendation* (as opposed to risk *prediction*) as requiring ML — it's a decision table |

**Input → Processing → Model → Output → Evaluation (Readiness):**
`Academic + skill + project + assessment data → normalize each component → weighted sum → 0–100 score + band → evaluate via face validity against manually reviewed sample profiles (not a statistical accuracy claim)`

**Input → Processing → Model → Output → Evaluation (Risk):**
`Skill gaps + mock scores + drive participation + application activity → threshold rules (P0) or classifier with class-imbalance handling (P1) → risk level + contributing factors → evaluate via precision/recall on a synthetic labeled subset, explicitly caveated as synthetic-only`

**Explicit honesty required in final docs:** neither Readiness nor the P0 Risk score is "AI" in the sense a judge asking "why is AI required?" would mean — they are transparent weighted/rule systems, chosen *because* the explainability requirement makes black-box ML actively undesirable here. Only the P1 Risk classifier and P1/P2 semantic matching involve trained models, and both should be labeled as such precisely.

---

## PHASE 14 — Scheduling Validation

Per paper #16, interview scheduling is formally reducible to the **Graph Coloring Problem** (NP-complete). For a hackathon prototype:

**Recommended approach:** a rule-based/greedy constraint-checker, **not** a full metaheuristic solver (genetic algorithm, ant colony optimization, simulated annealing — all mentioned in paper #16 as approaches for large-scale/production settings). At hackathon scale (dozens to low hundreds of interviews, not enterprise-scale scheduling), a straightforward greedy algorithm that:

1. Checks each new interview request against existing bookings for student/venue/panel overlap,
2. Rejects on conflict with a stated reason, and
3. Proposes the next open slot that satisfies all constraints simultaneously

...is provably correct for this problem size and is dramatically less implementation risk than a genetic algorithm or CSP solver library, which existing docs already correctly avoided ("Technically, this can be implemented using a constraint-based scheduling engine rather than forcing an LLM to perform deterministic scheduling" — keep this framing, it is correct).

**Do not over-engineer:** do not implement ant colony optimization or genetic algorithms for a hackathon demo — cite paper #16 to show awareness of the formal problem class and the more sophisticated options that exist, while explicitly justifying the simpler greedy approach as appropriate for the demonstrated scale.

---

## PHASE 15 — Dataset Review

| Category | Status | Notes |
|---|---|---|
| **REAL DATA** | Not used, not claimed | Correctly avoided per existing docs — no real student/recruiter data available for a hackathon, and using it without consent would be an ethical/privacy problem |
| **PUBLIC DATA** | Available but not currently used | Paper #9 confirms a public Kaggle student-placement dataset exists and has been used in peer-reviewed research — **recommend incorporating it** for the Readiness/Risk model's initial weight-tuning or validation, since it is the only source in this entire research pass that provides real (if limited) ground truth |
| **SYNTHETIC DATA** | Used for the ~4,820-student demo dataset | Appropriate for demoing UI/scale, but must never be described as validating model accuracy — a model "trained" or "tested" only on data you generated to match your own assumptions cannot demonstrate real predictive validity, only internal consistency |
| **SIMULATED DATA** | Used for the Jugaad Simulator's what-if projections | Correctly labeled in existing docs as "generated from the prototype's synthetic dataset/model, not presented as hard factual claims" — **keep this exact caveat**, it is the single most important honesty statement in the entire existing documentation and should not be watered down under pitch pressure |

**Recommendation:** explicitly cite the public Kaggle placement dataset (referenced via paper #9) as a real, if small, empirical anchor for the Readiness Engine's weight choices — even lightly checking that your chosen weights produce a plausible score distribution against real historical placement/non-placement labels is more defensible than weights chosen with no empirical reference at all.

**Update — dataset now identified by name:** direct GitHub inspection (see `RESEARCH_AUDIT.md` Phase 6 addendum) confirms the specific public dataset in question is `Placement_Data_Full_Class.csv` (Ben Roshan's "Campus Recruitment" dataset on Kaggle), independently used across at least 5 separate student projects found in this research pass. Cite it by name, not generically as "a public Kaggle dataset." One inspected repo using this exact file (`SahilChachra/Campus-Placement-Prediction`) explicitly warns in its own README that "due to very small dataset, the accuracy is not guaranteed" — this is direct, citable evidence for why JobJugaad should not report a fabricated or over-confident accuracy figure even if this dataset is used for weight validation.

---

## PHASE 16 — Architecture Review

| Layer | Existing Choice | Verdict | Change? |
|---|---|---|---|
| Frontend | React + TypeScript, Tailwind, Framer Motion, Recharts | **Keep** | None — appropriate, matches team skill (per `/profile.md`) |
| Backend | FastAPI, Python | **Keep** | None — correct choice; auto-generated docs materially help demo credibility |
| Database | PostgreSQL | **Keep** | None |
| pgvector | Listed as core stack | **Reclassify to P1/P2-conditional** | Only add pgvector infrastructure once/if semantic matching (P1) is actually attempted — installing it for a feature that stays P0-rule-based the whole hackathon is unnecessary operational complexity per the "don't over-engineer" principle applied consistently across Phases 10, 14 |
| AI/ML: scikit-learn | Listed | **Keep, scope to Risk Engine P1 only** | Correct tool for the one genuinely tabular-ML task (at-risk classification with class-imbalance handling) |
| AI/ML: embeddings | Listed | **Keep, scope to Matching Engine P1/P2 only, use sentence-transformers not a full LLM** | Per Phase 11 — an embedding model is sufficient and cheaper than an LLM call for similarity scoring |
| AI/ML: "LLM where justified" | Listed generically | **Narrow the justification** | Per Phase 11, the *only* well-justified LLM use case found is free-text resume section extraction — state this specifically rather than leaving "where justified" open-ended, which invites the judge question "why is AI required?" without a ready answer |
| Auth | JWT + RBAC | **Keep** | Correct, standard, matches multi-tenancy design |
| Deployment | Vercel + Render, Postgres on Render | **Keep** | Consistent with `ARCHITECTURE.md` and `TECHNICAL_DOCUMENTATION`; no change needed |

**What should be added:** a documented evaluation protocol (Phases 12–13) and an explicit, one-paragraph statement of which components are rule-based vs. ML vs. (narrowly) LLM-based — this single addition pre-empts several of the hardest judge questions in `JUDGE_REVIEW.md`.

**What should be simplified:** remove pgvector and full embedding infrastructure from the "must-have" stack list and move it to a clearly-labeled "P1/P2, only if time allows" note — this is the one place existing documentation risked over-engineering relative to what P0 actually requires.

**What should be strengthened (new finding):** direct inspection of `codeecoffee/SmartCampus` — a real, actively-built academic-platform repo — shows a concrete, implemented solution to exactly the multi-tenancy risk JobJugaad's `college_id` design addresses in principle but doesn't yet specify an enforcement mechanism for: that repo's README explicitly documents using **PostgreSQL Row-Level Security (RLS) policies**, not just application-layer `WHERE college_id = ...` filtering, to guarantee one student's (or in our case, one college's) data cannot leak into another's query results even if an application bug forgets the filter. This is a stronger, defense-in-depth version of what `ARCHITECTURE.md` currently describes as "every query filters by this column." **Recommend adding a Postgres RLS policy on every multi-tenant table as a second enforcement layer beneath the application-level filter** — cheap to add, and directly pre-empts the judge question "how is student privacy protected?" with a technically deeper answer than application-level filtering alone.

---
*Continues in `REVISED_DOCUMENTATION.md` (Phases 17–18) and `JUDGE_REVIEW.md` (Phase 19 + Final Output).*
