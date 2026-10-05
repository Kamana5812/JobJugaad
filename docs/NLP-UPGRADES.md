# NLP upgrades

All three upgrades were authorized on October 5, 2026. The default matching formula, hard eligibility rules, descending ranking, readiness bands and human overrides remain unchanged.

## Semantic evidence

Student opportunities and consenting application reviews have an optional **Compare semantic evidence** action. This uses the pretrained Sentence Transformers [all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) model, revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`. Its Apache-2.0 quantized ONNX artifact and tokenizer are pinned and checksummed in `backend/ml/semantic`. ONNX Runtime runs on the backend CPU without PyTorch, an external resume API or an LLM. This is a trained model; the other two upgrades below are deterministic text processing.

The comparison is the equal-weight mean of nonnegative cosine similarities between the description and recorded profile sections, multiplied by 100. Each section's contribution is displayed with the score and explanation. These contributions explain the aggregation, not the neural model's causal reasoning. The weights are unvalidated assumptions. The value is neither calibrated confidence nor probability of selection; semantic resemblance does not prove competence. It is separate from weighted matching and cannot promote or exclude anyone.

Processing is bounded to twelve profile sections, 1,000 characters per section and 1,200 description characters; each encoded excerpt is limited to 256 tokens. Context can be omitted. One comparison runs at a time per worker; saturation/model failure returns a retryable error without inventing a score. Authenticated quotas are thirty requests per account and six hundred per college per hour. Private text and vectors remain within the API process; no persistent embedding index, private-text cache or new tenant table is introduced. Therefore this pair-comparison release does not require pgvector. A future corpus-search upgrade would require its own architecture review.

Student access is limited to their own profile and an active approved college drive. Recruiters need an owned drive and an active consenting application; college administrators also require an active consenting application. Both application college filters and existing PostgreSQL FORCE RLS remain in effect. Withdrawal removes recruiter access.

## Keyword and TF-IDF evidence

Aliases such as PostgreSQL/SQL, RESTful API/REST API and C++/C# are normalized; TF-IDF uses unigram and bigram terms. Description review displays required, preferred, negated and mentioned clause hints with their source. Fully negated mentions are not proposed as requirements. These are heuristic hints: ambiguous clauses and negation scope need recruiter review. Keyword review and lexical similarity do not change the validated weighted matching formula.

## Resume suggestions

After PDF text extraction, choose **Preview extracted fields**. Review source-backed name, branch, explicit CGPA out of ten, skill mentions and project/certificate section blocks. Select only correct suggestions, enter proficiency yourself for each selected skill, then copy them into the unsaved profile editor. **Save profile & recalculate** is still required. Unknown assessments, ambiguous experience and grades on another scale are not inferred. Scanned/unreadable PDFs still require readable text; no OCR or trained field-extraction accuracy is claimed.

## Verification

Tests exercise the actual pinned encoder, controlled paraphrase ordering, reconciled contributions, unavailable/busy errors, aliases and source-backed extraction. HTTP tests check ownership, college isolation, consent withdrawal and unchanged stored profiles. These are correctness/synthetic sanity checks, not a benchmark or validated accuracy measurement. UI rendering checks and deployment verification are recorded separately; unobserved signed-in live actions must not be described as verified.

Release 302519f is live as API 0.20.0. Clean CI run 37333790316 passes the full backend regression, encrypted restore drill, frontend checks and build. All 51 public deployment checks pass, including all 34 FORCE-RLS policies. Eighteen live checks using previously authorized owned synthetic accounts in archived Demo College 1 verify actual model inference, reconciled contributions, source-backed resume suggestions and unchanged profile/readiness. Clearly labeled test drive #19 was closed with an audit reason; no applications, hiring decisions or emails were created. Evidence: evaluations/nlp-ci.json, evaluations/nlp-release.json and evaluations/nlp-live-inference.json. These checks do not establish model accuracy or owner acceptance of unrelated workflows.
