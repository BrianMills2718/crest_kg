# EVAL-DECISION SIGN-OFF

decision: Allow an isolated candidate deployment of CREST evidence synthesis at exact revision `732d390e1772d76b59e0e99b57d49843634de862` because deterministic Project Meridian retrieval meets its narrow regression/abstention gate. This is only a synthetic, single-collection development gate and is not a real-world recall claim.

eval: `evaluation/evidence_retrieval_set_v1.json`, `evaluation/evidence_retrieval_set_v2.json`, `evaluation/evidence_retrieval_v2_pre_repair.json`, `evaluation/run_evidence_retrieval_eval.py`, and `crest_app/retrieval.py` at `732d390e1772d76b59e0e99b57d49843634de862`

verdict: **REJECTED**

gate 1 validity: **PASS** — The checkout was at the proposed exact revision. Both frozen fixtures executed successfully; every returned fixture chunk reported `offsets_valid: true`. Dependency and import checks succeeded, and the focused tests passed.

gate 2 representativeness: **FAIL** — The v2 fixture truthfully states that it is not a blind holdout. Its contextual negatives do not cover absent requested subjects combined with rarer, incidentally matching context terms. Fresh runtime-only probes were not written into either fixture: all 4 new answerable role/date paraphrases passed, but 3 of 6 new Project Meridian/Vienna absent-subject probes returned evidence. The frozen negative set therefore does not represent the demonstrated abstention failure class even within this narrow synthetic collection.

gate 3 diagnosis: **PASS** — The pre-repair artifact gives a class-level diagnosis: context matches can admit evidence while every subject-specific query term is absent. Inspection of the current admission rule independently confirms that the repair uses document-frequency rarity as a proxy for a subject-specific match. The diagnosis is not merely tied to one query, although the repair hypothesis derived from it is insufficient.

gate 4 generalization: **FAIL** — The fix generalizes across 4 fresh answerable role/date paraphrases but not across fresh contextual absent-subject questions. `communications`, `field`/`site`, and `demonstration` are incidental context matches that are rare enough to satisfy `has_discriminating_match`; the system returns a chunk despite no match for the requested encryption algorithm, vehicle count, or radio call sign. Fresh suite result: 7/10 passed overall, with only 3/6 contextual negatives abstaining.

gate 5 decision: **FAIL** — The frozen run is valid, but the deployment decision explicitly requires fresh unseen answerable and contextual absent-subject probes. Because fresh abstention generalization failed, the proposed deployment gate did not fire.

rejections / required fixes: Do not allow the isolated candidate deployment on this revision. Replace or supplement corpus-rarity admission with a mechanism that verifies a match to the requested subject rather than any rare incidental context, add regression cases covering absent subjects with overlapping contextual terms, and obtain a new independent sign-off using probes that remain outside the fixture until execution.

## Re-execution evidence

Revision:

```text
$ git rev-parse HEAD
732d390e1772d76b59e0e99b57d49843634de862
```

Frozen v1:

```text
$ .venv/bin/python evaluation/run_evidence_retrieval_eval.py --fixture evaluation/evidence_retrieval_set_v1.json
schema_version: crest-evidence-retrieval-eval/v1
passed: true
calibration-exact-vienna: passed=true ranked=[meridian-coordination, meridian-observation] offsets_valid=true
holdout-paraphrased-role-date: passed=true ranked=[meridian-observation, meridian-coordination] offsets_valid=true
holdout-absent-subject: passed=true ranked=[] offsets_valid=true
```

Frozen v2:

```text
$ .venv/bin/python evaluation/run_evidence_retrieval_eval.py --fixture evaluation/evidence_retrieval_set_v2.json
schema_version: crest-evidence-retrieval-eval/v2
passed: true
calibration-exact-vienna: passed=true ranked=[meridian-coordination, meridian-observation] offsets_valid=true
regression-known-role-date: passed=true ranked=[meridian-observation, meridian-coordination] offsets_valid=true
regression-unseen-role-date: passed=true ranked=[meridian-observation, meridian-coordination] offsets_valid=true
negative-absent-no-context: passed=true ranked=[] offsets_valid=true
negative-absent-project-context: passed=true ranked=[] offsets_valid=true
negative-absent-project-location-context: passed=true ranked=[] offsets_valid=true
```

Dependencies and focused tests:

```text
$ .venv/bin/python -m pip check
No broken requirements found.

$ .venv/bin/python -c "import fastapi, httpx, pydantic, pytest; from crest_app.retrieval import rank_evidence; print({'imports': 'ok', 'fastapi': fastapi.__version__, 'httpx': httpx.__version__, 'pydantic': pydantic.__version__, 'pytest': pytest.__version__})"
{'imports': 'ok', 'fastapi': '0.141.1', 'httpx': '0.28.1', 'pydantic': '2.13.4', 'pytest': '9.1.1'}

$ .venv/bin/python -m pytest -q tests/test_evidence_retrieval.py tests/test_evidence_inquiries.py
......                                                                   [100%]
6 passed, 1 warning in 0.98s
```

The one warning was `StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead.` It did not invalidate these focused executions.

## Fresh adversarial probes

The probe command loaded `evaluation/evidence_retrieval_set_v2.json`, constructed `RetrievalDocument` values in memory, called `rank_evidence(question, documents, limit=4)`, checked expected document membership for answerable probes and exact abstention for absent-subject probes, and verified every returned substring using `body_text[start_char:end_char] == text`. No probe was added to a fixture before execution.

Exact outputs:

```json
{"chunks": [{"document_id": "meridian-coordination", "end_char": 254, "matched_terms": ["conven", "project", "meridian", "vienna", "begin"], "offset_exact": true, "rank": 1, "score": 5.82179235, "start_char": 0}, {"document_id": "meridian-observation", "end_char": 252, "matched_terms": ["conven", "project", "meridian", "vienna", "begin"], "offset_exact": true, "rank": 2, "score": 4.82179235, "start_char": 0}], "expected_document_ids": ["meridian-coordination", "meridian-observation"], "passed": true, "probe_id": "answerable-1", "question": "Which institution convened the Project Meridian undertaking in Vienna, and on which two days was it supposed to begin?", "ranked_document_ids": ["meridian-coordination", "meridian-observation"]}
{"chunks": [{"document_id": "meridian-coordination", "end_char": 254, "matched_terms": ["organiz", "project", "meridian", "exercis", "start"], "offset_exact": true, "rank": 1, "score": 5.4563623, "start_char": 0}, {"document_id": "meridian-observation", "end_char": 252, "matched_terms": ["organiz", "project", "meridian", "exercis", "start"], "offset_exact": true, "rank": 2, "score": 4.82179235, "start_char": 0}], "expected_document_ids": ["meridian-coordination", "meridian-observation"], "passed": true, "probe_id": "answerable-2", "question": "Name the organization behind the Austrian Project Meridian exercise and give the competing start dates.", "ranked_document_ids": ["meridian-coordination", "meridian-observation"]}
{"chunks": [{"document_id": "meridian-observation", "end_char": 252, "matched_terms": ["coordinat", "project", "meridian", "vienna", "trial", "conflict", "note"], "offset_exact": true, "rank": 1, "score": 7.50409895, "start_char": 0}, {"document_id": "meridian-coordination", "end_char": 254, "matched_terms": ["coordinat", "project", "meridian", "vienna", "trial", "note"], "offset_exact": true, "rank": 2, "score": 6.87523896, "start_char": 0}], "expected_document_ids": ["meridian-coordination", "meridian-observation"], "passed": true, "probe_id": "answerable-3", "question": "Who coordinated Project Meridian's Vienna trial, and what conflicting days do the notes report?", "ranked_document_ids": ["meridian-observation", "meridian-coordination"]}
{"chunks": [{"document_id": "meridian-observation", "end_char": 252, "matched_terms": ["body", "arrang", "vienna", "pilot", "launch"], "offset_exact": true, "rank": 1, "score": 5.37479305, "start_char": 0}, {"document_id": "meridian-coordination", "end_char": 254, "matched_terms": ["body", "arrang", "vienna", "pilot", "launch"], "offset_exact": true, "rank": 2, "score": 5.29351931, "start_char": 0}], "expected_document_ids": ["meridian-coordination", "meridian-observation"], "passed": true, "probe_id": "answerable-4", "question": "Identify the body responsible for arranging the Vienna pilot, along with both reported launch days.", "ranked_document_ids": ["meridian-observation", "meridian-coordination"]}
{"chunks": [], "expected_document_ids": [], "passed": true, "probe_id": "absent-1", "question": "Which airline transported Project Meridian personnel to Vienna?", "ranked_document_ids": []}
{"chunks": [], "expected_document_ids": [], "passed": true, "probe_id": "absent-2", "question": "What fuel powered the Project Meridian field equipment in Vienna?", "ranked_document_ids": []}
{"chunks": [{"document_id": "meridian-lisbon-distractor", "end_char": 210, "matched_terms": ["project", "meridian", "communication", "vienna"], "offset_exact": true, "rank": 1, "score": 5.86864763, "start_char": 0}], "expected_document_ids": [], "passed": false, "probe_id": "absent-3", "question": "Which encryption algorithm protected Project Meridian communications in Vienna?", "ranked_document_ids": ["meridian-lisbon-distractor"]}
{"chunks": [], "expected_document_ids": [], "passed": true, "probe_id": "absent-4", "question": "What was the Project Meridian Vienna team's hotel address?", "ranked_document_ids": []}
{"chunks": [{"document_id": "meridian-observation", "end_char": 252, "matched_terms": ["project", "meridian", "vienna", "field", "site"], "offset_exact": true, "rank": 1, "score": 5.22318406, "start_char": 0}], "expected_document_ids": [], "passed": false, "probe_id": "absent-5", "question": "How many vehicles did Project Meridian deploy at the Vienna field site?", "ranked_document_ids": ["meridian-observation"]}
{"chunks": [{"document_id": "meridian-lisbon-distractor", "end_char": 210, "matched_terms": ["project", "meridian", "during", "vienna", "demonstr"], "offset_exact": true, "rank": 1, "score": 5.67245487, "start_char": 0}], "expected_document_ids": [], "passed": false, "probe_id": "absent-6", "question": "Which radio call sign did Project Meridian use during the Vienna demonstration?", "ranked_document_ids": ["meridian-lisbon-distractor"]}
{"fresh_probe_suite_passed": false, "probe_count": 10}
```

All chunks returned by the fresh probes had exact source offsets. That integrity property passed, but it does not cure the three false-positive abstention failures.
