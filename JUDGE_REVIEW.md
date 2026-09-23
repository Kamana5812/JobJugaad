# JobJugaad — judge preparation

Lead with: **JobJugaad is an explainability-first campus placement workflow: every readiness, matching and support result shows its evidence and leaves the decision with a person.**

| Judge question | Implementation-grounded answer |
|---|---|
| Where is the AI? | No trained model or LLM exists in this prototype. pdfplumber extracts text, weighted rules score profiles and a greedy checker proposes interview slots. The user-specified Run AI Matching label has an adjacent no-trained-model disclosure. |
| Why these weights? | Readiness uses the requested 30/20/15/15/10/10 proposal. Matching defaults to 40/20/20/15/5 with configurable role weights and normalized 0–100 inputs. These are unvalidated assumptions. |
| Why exclude a candidate? | CGPA/branch/backlog rules and the default 60 threshold are shown with factors, missing requirements, fixed explanations and a next step. There is no numeric confidence score. |
| Can a recruiter disagree? | Promote or reject with a reason; original scoring evidence, reviewer and time remain in audit history. |
| What is the support score? | A count of three indicators: at least three skill gaps, known interview score below 40, fewer than two completed interviews in 30 days. All three must hold to flag. It is not a probability; factors and interventions support human review. |
| How was accuracy evaluated? | The synthetic check reproduced 25/30 expected matches. Readiness/support agreed on 10/10 reviewed profiles each. Expectations were assistant-authored against our assumptions; five matching misses are preserved. No independent or real-world accuracy percentage is justified. |
| Is scheduling optimized? | The greedy checker skips recorded student/venue/panel conflicts within seven days and rechecks on approval. It does not optimize a global timetable or model campus working hours. |
| How are colleges isolated? | All 17 tenant tables have application filters plus ENABLE/FORCE RLS on reads/writes. Role/ownership checks restrict access within a college. Real institutions still need controlled enrollment instead of self-selected demo colleges. |
| Does Selected mean placed? | No. Letter, documents, verification, acceptance and joining are distinct stages. Accepted offers and recorded joining are counted separately. |
| Are documents validated and messages delivered? | No. Stages declare external document exchange; notifications stay in the in-app feed. |
| Are you first? | No. Competitors exist. Demonstrate consistent factor-level evidence and human review, without exclusivity claims. |
| How would a trained support model be added? | Only with explicit authorization, suitable real labeled data, SMOTE or class weighting in leakage-safe training splits and independent evaluation. Synthetic demo data cannot validate real-world predictions. |

Read [the demo guide](DEMO_GUIDE.md), [evaluation limitations](evaluations/phase4-report.md), [security audit](PHASE5_AUDIT.md) and [Architecture Section 9](ARCHITECTURE.md#9-dataset--evaluation). This is a new implementation-grounded sheet; missing historical research documents were not reconstructed or claimed as reviewed. The presenter should rehearse aloud and warm the live app before the actual demo slot; automated checks cannot perform those actions.
