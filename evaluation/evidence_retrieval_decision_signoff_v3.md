# EVAL-DECISION SIGN-OFF

decision: Allow an isolated candidate deployment of CREST evidence synthesis at exact revision `83411399363434dca4d107bb2d35a913e708178e` because deterministic Project Meridian retrieval now meets its narrow subject-aware regression/abstention gate. This claim is limited to synthetic single-collection development behavior and is not a claim of real-world recall.

eval: `evaluation/evidence_retrieval_set_v1.json`, `evaluation/evidence_retrieval_set_v2.json`, `evaluation/evidence_retrieval_set_v3.json`, `evaluation/run_evidence_retrieval_eval.py`, `crest_app/retrieval.py`, and focused tests at `83411399363434dca4d107bb2d35a913e708178e`

verdict: **REJECTED**

gate 1 validity: **PASS** — The checkout was at the proposed exact revision. All three frozen fixtures executed successfully and every case reported `offsets_valid: true`. Python and required imports were available, `pip check` reported no broken requirements, and the focused retrieval/inquiry/API tests passed. The known-good answerable controls returned both decisive Vienna documents, so the run was not an unavailable or partial build.

gate 2 representativeness: **FAIL** — The v3 fixture truthfully says that it is synthetic and not blind. Its six negative questions all begin with one of the small forms recognized by `_query_focus_concepts`: `Which`, `What`, or `How many`. The implementation returns no focus requirement for ordinary `Did`, `Where`, `When`, `Was`, `How`, `Who`, `Can`, and conversational openings. Fresh runtime-only probes covered those missing forms while retaining Project Meridian, Vienna, and plausible incidentally matching context. All 6 fresh answerable role/date paraphrases passed, but 0 of 10 fresh absent-subject questions abstained. The frozen set therefore does not represent the demonstrated grammatical failure class even within this narrow synthetic collection.

gate 3 diagnosis: **PASS** — The class-level diagnosis is independently supported: context overlap can admit a chunk even when the requested subject is absent. The revision diff implements `_query_focus_concepts` and filters candidates only when that helper returns a nonempty focus. Source inspection and fresh execution agree that this targets the diagnosed mechanism for a small leading-question grammar, but deliberately falls back to context-only ranking for other forms. The diagnosis is class-level; the repair coverage is insufficient.

gate 4 generalization: **FAIL** — All v1/v2/v3 cases remained green and all 6 unseen answerable role/date probes returned both required documents without placing the Lisbon distractor in the top two. However, all 10 unseen contextual absent-subject probes returned one or more chunks. Examples include a satellite uplink, medical supplies, charter flight, biometric badge, telemetry encryption, catering, camera serial number, hotel checkout time, vehicle parking, and radio operator; none appears in the collection. Every returned chunk retained exact source offsets, but exact grounding of an irrelevant chunk does not satisfy abstention. The fix generalizes to the fixture's recognized leading forms, not the absent-subject class.

gate 5 decision: **FAIL** — A cheap empirical gate is justified for this narrow, reversible development decision, and the literal frozen runs are valid. The v3 decision rule additionally requires fresh unseen answerable and contextual absent-subject probes. Because fresh abstention generalization failed 10/10, the deployment decision does not fire at this revision.

rejections / required fixes: Do not allow the isolated candidate deployment on `83411399363434dca4d107bb2d35a913e708178e`. Replace the leading-form-only focus condition with a mechanism that requires evidence for the requested subject across ordinary question forms (or conservatively abstains when subject focus cannot be established), freeze representative form-diverse negatives before the next repair, rerun all three fixtures and focused tests, and obtain a new independent runtime-only sign-off. Preserve the narrow synthetic claim; do not infer real-world recall.

## Re-execution evidence

Revision and dependency readiness:

```text
$ git rev-parse HEAD
83411399363434dca4d107bb2d35a913e708178e

$ .venv/bin/python --version
Python 3.12.3

$ .venv/bin/python -c "import fastapi, httpx, pydantic, pytest; from crest_app.retrieval import evaluate_retrieval_fixture, rank_evidence; print({'imports': 'ok', 'fastapi': fastapi.__version__, 'httpx': httpx.__version__, 'pydantic': pydantic.__version__, 'pytest': pytest.__version__})"
{'imports': 'ok', 'fastapi': '0.141.1', 'httpx': '0.28.1', 'pydantic': '2.13.4', 'pytest': '9.1.1'}

$ .venv/bin/python -m pip check
No broken requirements found.
```

Frozen fixture reruns:

```text
$ .venv/bin/python evaluation/run_evidence_retrieval_eval.py --fixture evaluation/evidence_retrieval_set_v1.json
schema_version: crest-evidence-retrieval-eval/v1
passed: true
calibration-exact-vienna: passed=true ranked=[meridian-coordination, meridian-observation] offsets_valid=true
holdout-paraphrased-role-date: passed=true ranked=[meridian-observation, meridian-coordination] offsets_valid=true
holdout-absent-subject: passed=true ranked=[] offsets_valid=true

$ .venv/bin/python evaluation/run_evidence_retrieval_eval.py --fixture evaluation/evidence_retrieval_set_v2.json
schema_version: crest-evidence-retrieval-eval/v2
passed: true
calibration-exact-vienna: passed=true ranked=[meridian-coordination, meridian-observation] offsets_valid=true
regression-known-role-date: passed=true ranked=[meridian-observation, meridian-coordination] offsets_valid=true
regression-unseen-role-date: passed=true ranked=[meridian-observation, meridian-coordination] offsets_valid=true
negative-absent-no-context: passed=true ranked=[] offsets_valid=true
negative-absent-project-context: passed=true ranked=[] offsets_valid=true
negative-absent-project-location-context: passed=true ranked=[] offsets_valid=true

$ .venv/bin/python evaluation/run_evidence_retrieval_eval.py --fixture evaluation/evidence_retrieval_set_v3.json
schema_version: crest-evidence-retrieval-eval/v3
passed: true
canonical-role-date: passed=true ranked=[meridian-observation, meridian-coordination] offsets_valid=true
put-on-role-date: passed=true ranked=[meridian-observation, meridian-coordination] offsets_valid=true
institution-convened-days: passed=true ranked=[meridian-coordination, meridian-observation] offsets_valid=true
organization-competing-dates: passed=true ranked=[meridian-coordination, meridian-observation] offsets_valid=true
coordinator-conflicting-days: passed=true ranked=[meridian-observation, meridian-coordination] offsets_valid=true
body-arranged-launch-days: passed=true ranked=[meridian-observation, meridian-coordination] offsets_valid=true
absent-airline: passed=true ranked=[] offsets_valid=true
absent-fuel: passed=true ranked=[] offsets_valid=true
absent-encryption-algorithm: passed=true ranked=[] offsets_valid=true
absent-hotel-address: passed=true ranked=[] offsets_valid=true
absent-vehicle-count: passed=true ranked=[] offsets_valid=true
absent-radio-call-sign: passed=true ranked=[] offsets_valid=true
```

Focused tests:

```text
$ .venv/bin/python -m pytest -q tests/test_evidence_retrieval.py tests/test_evidence_inquiries.py tests/test_crest_app.py -k 'evidence or inquiry'
.......                                                                  [100%]
7 passed, 12 deselected, 1 warning in 1.05s
```

The warning was `StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead.` It did not invalidate the focused executions.

## Fresh adversarial probes

Before seeing any outputs, the verifier placed 6 new answerable role/date paraphrases and 10 new absent-subject questions in one in-memory Python process. The process loaded v3's documents, called `rank_evidence(question, documents, limit=4)`, required both decisive documents and no Lisbon distractor in the top two for answerable probes, required no chunks for absent-subject probes, and checked every returned substring with `body_text[start_char:end_char] == text`. No fresh probe was written to a fixture before execution.

Summary:

```json
{"all_passed": false, "answerable_passed": 6, "answerable_total": 6, "absent_passed": 0, "absent_total": 10, "all_offsets_exact": true}
```

Every fresh probe output:

```json
{"probe_id":"fresh-answerable-1","kind":"answerable","question":"Could you reconcile the Project Meridian Vienna kickoff by naming its organizer and the two dates reported for the opening?","expected_document_ids":["meridian-coordination","meridian-observation"],"passed":true,"ranked_document_ids":["meridian-coordination","meridian-observation"],"offsets_exact":true,"chunks":[{"rank":1,"document_id":"meridian-coordination","start_char":0,"end_char":254,"offset_exact":true,"score":5.87685697,"matched_terms":["project","meridian","vienna","its","organizer","date"]},{"rank":2,"document_id":"meridian-observation","start_char":0,"end_char":252,"offset_exact":true,"score":3.31699846,"matched_terms":["project","meridian","vienna","date"]}]}
{"probe_id":"fresh-answerable-2","kind":"answerable","question":"For the Austrian Project Meridian pilot, tell me who served as the convening institution and whether it opened on 14 or 16 May 1987.","expected_document_ids":["meridian-coordination","meridian-observation"],"passed":true,"ranked_document_ids":["meridian-observation","meridian-coordination"],"offsets_exact":true,"chunks":[{"rank":1,"document_id":"meridian-observation","start_char":0,"end_char":252,"offset_exact":true,"score":7.66091864,"matched_terms":["project","meridian","pilot","conven","institution","14","16","may","1987"]},{"rank":2,"document_id":"meridian-coordination","start_char":0,"end_char":254,"offset_exact":true,"score":7.18803066,"matched_terms":["project","meridian","pilot","conven","institution","14","may","1987"]}]}
{"probe_id":"fresh-answerable-3","kind":"answerable","question":"Was Harbor Institute or Eastbridge Laboratory responsible for organizing the Vienna exercise, and which source dates its start to 14 May versus 16 May 1987?","expected_document_ids":["meridian-coordination","meridian-observation"],"passed":true,"ranked_document_ids":["meridian-observation","meridian-coordination"],"offsets_exact":true,"chunks":[{"rank":1,"document_id":"meridian-observation","start_char":0,"end_char":252,"offset_exact":true,"score":11.20020825,"matched_terms":["harbor","institut","eastbridg","laboratory","organiz","vienna","exercis","date","14","may","16","1987"]},{"rank":2,"document_id":"meridian-coordination","start_char":0,"end_char":254,"offset_exact":true,"score":10.85741688,"matched_terms":["harbor","institut","eastbridg","laboratory","organiz","vienna","exercis","date","its","14","may","1987"]}]}
{"probe_id":"fresh-answerable-4","kind":"answerable","question":"Please summarize the Austrian field exercise's organizing body and reconcile its scheduled and observed start dates.","expected_document_ids":["meridian-coordination","meridian-observation"],"passed":true,"ranked_document_ids":["meridian-coordination","meridian-observation"],"offsets_exact":true,"chunks":[{"rank":1,"document_id":"meridian-coordination","start_char":0,"end_char":254,"offset_exact":true,"score":6.23485501,"matched_terms":["field","exercis","organiz","body","its","schedul"]},{"rank":2,"document_id":"meridian-observation","start_char":0,"end_char":252,"offset_exact":true,"score":4.7232779,"matched_terms":["field","exercis","organiz","body","schedul"]}]}
{"probe_id":"fresh-answerable-5","kind":"answerable","question":"The Project Meridian records disagree on when Vienna's pilot began; report the institution that convened it and both calendar dates.","expected_document_ids":["meridian-coordination","meridian-observation"],"passed":true,"ranked_document_ids":["meridian-coordination","meridian-observation","meridian-administration"],"offsets_exact":true,"chunks":[{"rank":1,"document_id":"meridian-coordination","start_char":0,"end_char":254,"offset_exact":true,"score":7.06089245,"matched_terms":["project","meridian","vienna","pilot","began","institution","conven"]},{"rank":2,"document_id":"meridian-observation","start_char":0,"end_char":252,"offset_exact":true,"score":6.1421662,"matched_terms":["project","meridian","vienna","pilot","began","institution","conven"]},{"rank":3,"document_id":"meridian-administration","start_char":0,"end_char":168,"offset_exact":true,"score":2.08914584,"matched_terms":["project","record"]}]}
{"probe_id":"fresh-answerable-6","kind":"answerable","question":"Between the preliminary schedule and the observer correction, who had the organizing role in the Project Meridian Vienna trial, and what were the respective May dates?","expected_document_ids":["meridian-coordination","meridian-observation"],"passed":true,"ranked_document_ids":["meridian-observation","meridian-coordination"],"offsets_exact":true,"chunks":[{"rank":1,"document_id":"meridian-observation","start_char":0,"end_char":252,"offset_exact":true,"score":11.7962104,"matched_terms":["preliminary","schedul","observer","correction","organiz","project","meridian","vienna","trial","may"]},{"rank":2,"document_id":"meridian-coordination","start_char":0,"end_char":254,"offset_exact":true,"score":6.93727718,"matched_terms":["schedul","organiz","project","meridian","vienna","trial","may"]}]}
{"probe_id":"fresh-absent-1","kind":"absent-subject","question":"Did Project Meridian use a satellite uplink for communications during the Vienna demonstration?","expected_document_ids":[],"passed":false,"ranked_document_ids":["meridian-lisbon-distractor"],"offsets_exact":true,"chunks":[{"rank":1,"document_id":"meridian-lisbon-distractor","start_char":0,"end_char":210,"offset_exact":true,"score":7.85673514,"matched_terms":["project","meridian","communication","during","vienna","demonstr"]}]}
{"probe_id":"fresh-absent-2","kind":"absent-subject","question":"Where did Project Meridian keep its medical supplies at the Vienna field site?","expected_document_ids":[],"passed":false,"ranked_document_ids":["meridian-coordination","meridian-observation"],"offsets_exact":true,"chunks":[{"rank":1,"document_id":"meridian-coordination","start_char":0,"end_char":254,"offset_exact":true,"score":5.85775402,"matched_terms":["project","meridian","its","vienna","field"]},{"rank":2,"document_id":"meridian-observation","start_char":0,"end_char":252,"offset_exact":true,"score":4.72318406,"matched_terms":["project","meridian","vienna","field","site"]}]}
{"probe_id":"fresh-absent-3","kind":"absent-subject","question":"When did Project Meridian's charter flight land in Vienna for the pilot?","expected_document_ids":[],"passed":false,"ranked_document_ids":["meridian-coordination","meridian-observation"],"offsets_exact":true,"chunks":[{"rank":1,"document_id":"meridian-coordination","start_char":0,"end_char":254,"offset_exact":true,"score":5.60267971,"matched_terms":["project","meridian","vienna","pilot","date"]},{"rank":2,"document_id":"meridian-observation","start_char":0,"end_char":252,"offset_exact":true,"score":5.22962738,"matched_terms":["project","meridian","vienna","pilot","date"]}]}
{"probe_id":"fresh-absent-4","kind":"absent-subject","question":"Was a biometric badge required at the Project Meridian Vienna field site?","expected_document_ids":[],"passed":false,"ranked_document_ids":["meridian-observation"],"offsets_exact":true,"chunks":[{"rank":1,"document_id":"meridian-observation","start_char":0,"end_char":252,"offset_exact":true,"score":5.22318406,"matched_terms":["project","meridian","vienna","field","site"]}]}
{"probe_id":"fresh-absent-5","kind":"absent-subject","question":"How did Project Meridian encrypt telemetry during the Vienna trial?","expected_document_ids":[],"passed":false,"ranked_document_ids":["meridian-lisbon-distractor"],"offsets_exact":true,"chunks":[{"rank":1,"document_id":"meridian-lisbon-distractor","start_char":0,"end_char":210,"offset_exact":true,"score":6.30737551,"matched_terms":["project","meridian","during","vienna","trial"]}]}
{"probe_id":"fresh-absent-6","kind":"absent-subject","question":"Who catered Project Meridian's Vienna launch-day briefing?","expected_document_ids":[],"passed":false,"ranked_document_ids":["meridian-lisbon-distractor","meridian-coordination","meridian-observation"],"offsets_exact":true,"chunks":[{"rank":1,"document_id":"meridian-lisbon-distractor","start_char":0,"end_char":210,"offset_exact":true,"score":5.86864763,"matched_terms":["project","meridian","vienna","brief"]},{"rank":2,"document_id":"meridian-coordination","start_char":0,"end_char":254,"offset_exact":true,"score":5.19833797,"matched_terms":["project","meridian","vienna","launch"]},{"rank":3,"document_id":"meridian-observation","start_char":0,"end_char":252,"offset_exact":true,"score":4.4598556,"matched_terms":["project","meridian","vienna","launch"]}]}
{"probe_id":"fresh-absent-7","kind":"absent-subject","question":"Could you provide the camera serial number used by Project Meridian in Vienna?","expected_document_ids":[],"passed":false,"ranked_document_ids":["meridian-observation"],"offsets_exact":true,"chunks":[{"rank":1,"document_id":"meridian-observation","start_char":0,"end_char":252,"offset_exact":true,"score":3.98992022,"matched_terms":["provid","project","meridian","vienna"]}]}
{"probe_id":"fresh-absent-8","kind":"absent-subject","question":"Tell me the hotel checkout time for Project Meridian staff after the Vienna demonstration.","expected_document_ids":[],"passed":false,"ranked_document_ids":["meridian-lisbon-distractor"],"offsets_exact":true,"chunks":[{"rank":1,"document_id":"meridian-lisbon-distractor","start_char":0,"end_char":210,"offset_exact":true,"score":5.26841447,"matched_terms":["project","meridian","staff","vienna","demonstr"]}]}
{"probe_id":"fresh-absent-9","kind":"absent-subject","question":"Were Project Meridian vehicles parked beside Eastbridge Laboratory during the Vienna exercise?","expected_document_ids":[],"passed":false,"ranked_document_ids":["meridian-coordination","meridian-observation","meridian-lisbon-distractor"],"offsets_exact":true,"chunks":[{"rank":1,"document_id":"meridian-coordination","start_char":0,"end_char":254,"offset_exact":true,"score":6.42810852,"matched_terms":["project","meridian","eastbridg","laboratory","vienna","exercis"]},{"rank":2,"document_id":"meridian-observation","start_char":0,"end_char":252,"offset_exact":true,"score":5.79353857,"matched_terms":["project","meridian","eastbridg","laboratory","vienna","exercis"]},{"rank":3,"document_id":"meridian-lisbon-distractor","start_char":0,"end_char":210,"offset_exact":true,"score":5.45023265,"matched_terms":["project","meridian","during","vienna","exercis"]}]}
{"probe_id":"fresh-absent-10","kind":"absent-subject","question":"Can you identify the radio operator assigned to Project Meridian in Vienna on 16 May 1987?","expected_document_ids":[],"passed":false,"ranked_document_ids":["meridian-observation","meridian-coordination"],"offsets_exact":true,"chunks":[{"rank":1,"document_id":"meridian-observation","start_char":0,"end_char":252,"offset_exact":true,"score":5.63235272,"matched_terms":["project","meridian","vienna","16","may","1987"]},{"rank":2,"document_id":"meridian-coordination","start_char":0,"end_char":254,"offset_exact":true,"score":4.9125542,"matched_terms":["project","meridian","vienna","may","1987"]}]}
```
