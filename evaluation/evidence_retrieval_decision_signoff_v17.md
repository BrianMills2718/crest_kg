# CREST evidence-retrieval decision sign-off v17

## Decision under review

- Candidate revision: `d884f493a73bc289bcbbc72399294aa77cdd4ce4`
- Proposed decision: ship the deterministic small-synthetic-collection passage-retrieval revision.
- Comparison base: rejected revision `6469e7c`.
- Verifier posture: fresh, adversarial, execution-based. Earlier sign-off prose and fixture contents were not read before this contract was frozen.
- Scope: passage admission, ranking, deterministic chunking, and exact source offsets in small synthetic collections. Arbitrary natural-language parsing and downstream answer classification are explicitly out of scope.

## Frozen pre-execution contract

This contract was authored before running any frozen fixture, fresh probe, test suite, or mechanism diff. It is intentionally bounded to 12 cases (8 retrieval, 4 chunking) and uses fresh names and wording.

### Retrieval cases

| Case | Fresh input | Frozen expectation |
| --- | --- | --- |
| R1 ordinary positive | One source says `Project Saffron's harbor rehearsal was organized by the Northwind Institute`; ask who organized Project Saffron's rehearsal. | Return only `v17-saffron`; every returned slice must exactly equal the source bytes at its offsets. |
| R2 absent subject | Use the R1 source; ask who organized `Project Juniper's` harbor rehearsal. | Return no evidence despite shared predicate/detail words. |
| R3 exact subject, OOV absent detail | Use the R1 source; ask for Project Saffron's `aquamarine indemnity code`, terms absent from the collection. | Return `v17-saffron` as subject context; retrieval does not classify whether the detail is answered. |
| R4 varied conjunction positive | A source says Project Alder was coordinated by Copper Vale Office, while Lumen Forge Laboratory supplied instruments; query uses `while`. | Return only `v17-paired`. |
| R5 varied conjunction negative | Use R4 source; ask who coordinated Project Briar `and` which laboratory supplied instruments. | Return no evidence because the structural subject is absent even though the paired predicates/details are present. |
| R6 permitted raw-name variant | An Austria source names Project Mariner; ask about Project `Marienr` in Austria. | Return only `v17-mariner`; the transposition is permitted only with the independent exact Austria anchor. |
| R7 substitution safety | Use R6 source; ask about Project `Marinor` in Austria. | Return no evidence: a same-length one-character substitution must not be accepted as a benign name variant. |
| R8 deterministic tie | Two byte-identical Project Quartz sources have document IDs `tie-alpha` and `tie-zulu`; request both. | Scores tie exactly; order is `tie-alpha`, then `tie-zulu`; two independent runs serialize identically. |

### Chunking and source-byte cases

All probes use `max_chunk_chars=200` and `overlap_chars=0`.

| Case | Frozen construction | Frozen expectation |
| --- | --- | --- |
| C1 paragraph outranks later sentence/word | `P*105 + "\\n\\n" + S*30 + ". " + W*50 + " " + T*30` | Exact windows `[(0,105), (107,220)]`; the paragraph boundary at 105 wins over the later sentence and word boundaries in the first hard window. |
| C2 sentence outranks later word and preserves separator bytes | `A*120 + ". " + B*40 + " " + C*70` | Exact windows `[(0,121), (122,233)]`; first text ends in `.`, second starts with `B`, the sole uncovered source slice is exactly one ASCII space at `[121:122]`, and both chunk texts equal their source slices. |
| C3 word fallback | `D*130 + " " + E*90` | Exact windows `[(0,130), (131,221)]`; without paragraph or sentence boundaries, the ordinary word boundary is used and exact source slices are preserved. |
| C4 exact multi-window offsets | `M*105 + "\\n\\n" + N*105 + "\\n\\n" + O*105` | Exact windows `[(0,105), (107,212), (214,319)]`; each text equals exactly `body[start:end]`, with only the two paragraph separators outside the trimmed windows. |

### Pass/fail rule

`SIGNED-OFF` requires all of the following without expectation changes: frozen fixtures v5-v16 pass twice with byte-identical aggregate output; all 12 fresh cases pass twice with byte-identical output; the complete pytest suite passes; JavaScript syntax and Python dependency checks pass; the diff from `6469e7c` is a class-level mechanism rather than instance branching; and the evaluated checkout remains the exact clean candidate revision apart from this sign-off artifact. Any real failure yields `REJECTED`.

## Execution evidence

Execution completed at `2026-08-21T09:15:14Z`. `git rev-parse HEAD` remained
`d884f493a73bc289bcbbc72399294aa77cdd4ce4`; before the artifact was created the
worktree was clean, and afterward `git status --short` listed only this v17
artifact.

### Commands

```bash
git rev-parse HEAD
git status --short

# Run the repository evaluator directly over every frozen fixture. The same
# in-memory Python body was invoked twice, once per output path.
PYTHONPATH=. .venv/bin/python - <<'PY' > /tmp/crest_v17_frozen_run1.json
import json
from pathlib import Path
from crest_app.retrieval import evaluate_retrieval_fixture
root = Path.cwd()
results = {
    f"v{version}": evaluate_retrieval_fixture(
        root / "evaluation" / f"evidence_retrieval_set_v{version}.json"
    )
    for version in range(5, 17)
}
print(json.dumps(results, sort_keys=True, separators=(",", ":")))
if not all(item["passed"] for item in results.values()):
    raise SystemExit(1)
PY
# Repeated verbatim with output redirected to /tmp/crest_v17_frozen_run2.json.
cmp -s /tmp/crest_v17_frozen_run1.json /tmp/crest_v17_frozen_run2.json
sha256sum /tmp/crest_v17_frozen_run1.json /tmp/crest_v17_frozen_run2.json

# `fresh_suite` was an in-memory Python script implementing the 12 frozen cases
# above with direct assertions; no repository fixture or helper was written.
printf '%s\n' "$fresh_suite" | PYTHONPATH=. .venv/bin/python - > /tmp/crest_v17_fresh_run1.json
printf '%s\n' "$fresh_suite" | PYTHONPATH=. .venv/bin/python - > /tmp/crest_v17_fresh_run2.json
cmp -s /tmp/crest_v17_fresh_run1.json /tmp/crest_v17_fresh_run2.json
sha256sum /tmp/crest_v17_fresh_run1.json /tmp/crest_v17_fresh_run2.json

PYTHONPATH=. .venv/bin/python -m pytest -q
node --check web/app.js
.venv/bin/python -m pip check

git diff --name-status 6469e7c d884f493a73bc289bcbbc72399294aa77cdd4ce4
git diff --unified=80 6469e7c d884f493a73bc289bcbbc72399294aa77cdd4ce4 -- crest_app/retrieval.py
git diff --unified=50 6469e7c d884f493a73bc289bcbbc72399294aa77cdd4ce4 -- tests/test_evidence_retrieval.py
```

### Results

- Frozen v5-v16: **12/12 fixtures and 99/99 cases passed** on both runs;
  `offsets_valid` was true for all 99 cases. Both aggregate outputs had SHA-256
  `0823a9e79c91402bdc74eaa7090291261a556555015cd1ab20471518bb98b59c` and
  were byte-identical.
- Fresh retrieval: **8/8 passed** on both runs. Returned IDs were exactly:
  R1 `[v17-saffron]`, R2 `[]`, R3 `[v17-saffron]`, R4 `[v17-paired]`,
  R5 `[]`, R6 `[v17-mariner]`, R7 `[]`, and R8
  `[tie-alpha, tie-zulu]`.
- Fresh deterministic tie: both tied scores were exactly `6.22928623`; the two
  independent rankings and the two complete fresh-run serializations were
  identical.
- Fresh chunking: **4/4 passed** with exact offsets C1
  `[(0,105), (107,220)]`, C2 `[(0,121), (122,233)]`, C3
  `[(0,130), (131,221)]`, and C4
  `[(0,105), (107,212), (214,319)]`.
- C2 retained the sentence period at offset 120 in the first chunk, began the
  second chunk at the first `B`, identified the intentionally trimmed separator
  as the exact source slice `[121:122] == " "`, and reconstructed the complete
  source byte-for-byte from the exact chunk slices plus that source gap. C4 did
  the same across both exact `"\n\n"` source gaps.
- Both complete fresh outputs had SHA-256
  `0db37752e992b6768bc68737ce3c94a17e58f3f1778747ed689b7e3af353bf1a`
  and were byte-identical.
- Repository regression suite: **51 passed** in 13.42 seconds. The only warning
  was an existing Starlette `httpx` deprecation warning from the virtualenv.
- `node --check web/app.js`: exit 0 with no output.
- `.venv/bin/python -m pip check`: exit 0, `No broken requirements found.`

### Mechanism and generalization inspection

The range from rejected `6469e7c279d01d79a59f9069eed56bd7ec61f99e` to the
candidate contains one production change, in `chunk_document`, plus its focused
test and the prior sign-off artifact. The rejected code represented paragraph,
sentence, and word boundaries only as integer candidates and advanced the end
offset by one only when the byte *at* the selected boundary was a space. A
sentence search returns the index of `.`, so that generic rule excluded the
punctuation byte.

The candidate replaces that ambiguous adjustment with explicit class rules:
paragraph ends at the separator, sentence ends at `sentence_boundary + 1`, and
word ends at `word_boundary + 1`. The existing trimming and next-window logic
then omit separator whitespace while retaining punctuation and exact source
offsets. This is a boundary-class mechanism with no query, document, fixture,
or named-entity branching.

The repository's focused sentence probe uses different lengths from fresh C2.
Fresh C2 additionally checked the second-window start and byte-exact full-source
reconstruction, while C1/C3/C4 exercised the adjacent boundary classes and
multi-window behavior. Those held-out probes passed without regressions in the
99 frozen cases, the other seven fresh retrieval cases, or the complete suite.
Per the instruction to evaluate the exact candidate checkout only, the rejected
revision was inspected but not checked out or executed.

## Five-gate decision record

- **Gate 1 — validity: PASS.** Known-good controls R1, R4, and R6 returned their
  exact sources; the negative controls remained empty; all exact-offset checks
  passed. The repository test environment, JavaScript parser, and installed
  Python dependency graph were available and healthy.
- **Gate 2 — representativeness: PASS for the stated bounded scope.** The frozen
  set plus fresh cases cover ordinary positive/absent subjects, exact-subject
  context with absent OOV details, varied paired conjunctions, a permitted name
  transposition and unsafe substitution, a deterministic tie, all three
  boundary priorities, sentence-separator preservation, and three exact
  windows. The decision is not generalized beyond small synthetic collections.
- **Gate 3 — diagnosis: PASS.** The rejected mechanism's class-level defect is
  the mismatch between the sentence search's `.` index and the former generic
  `body[boundary] == " "` increment rule. It is not tied to one fixture string.
- **Gate 4 — generalization: PASS.** The fresh C2 same-class probe was frozen
  before diff inspection and differs from the repository test in lengths and
  assertions. C1/C3/C4 checked neighboring boundary behavior, while 99 frozen
  and seven other fresh retrieval cases supplied the regression control. All
  repeated identically.
- **Gate 5 — decision: PASS.** Exact delimiter retention, offsets, and
  determinism are empirical properties for which this bounded execution was
  cheaper and more decisive than inspection alone. The ship recommendation is
  conditioned on the exact passing revision and the declared retrieval scope.

### Limitations

- This does not certify arbitrary question grammar, broad language coverage,
  large/live corpora, retrieval quality beyond the synthetic contract, latency,
  or downstream answer-status classification.
- Whitespace separators are intentionally trimmed from chunk text; the checks
  prove exact source slices, retention of the non-whitespace sentence delimiter,
  and byte-exact reconstruction using the recorded gaps, not contiguous coverage
  of separator whitespace by chunk text.
- The rejected revision was not executed because the task constrained execution
  to the exact candidate; its failure mechanism is established by the inspected
  source diff.

## Verdict

**PASS — SIGNED-OFF.** Ship
`d884f493a73bc289bcbbc72399294aa77cdd4ce4` for deterministic passage retrieval
over small synthetic collections. Do not cite this sign-off as evidence for the
out-of-scope parsing, classification, scale, or live-corpus claims listed above.
