# CREST evidence retrieval — independent decision sign-off v16

EVAL-DECISION SIGN-OFF

decision: Ship exact revision `6469e7c279d01d79a59f9069eed56bd7ec61f99e` only if frozen fixtures v5-v16 and a fresh representative/adversarial suite establish deterministic passage admission, ranking, chunk-boundary priority, and exact offsets for small synthetic collections.

eval: `evaluation/evidence_retrieval_set_v5.json` through `evaluation/evidence_retrieval_set_v16.json`, plus the pre-execution contract below.

verdict: **REJECTED**

## Pre-execution fresh contract

This contract was authored and frozen before the first call to `rank_evidence`, `chunk_document`, any retrieval fixture runner, or the repository test suite in this independent verification. The cases use new entities and wording rather than copying frozen v5-v16 cases. Expectations will not be changed after execution.

The graded boundary is deterministic passage retrieval for small synthetic collections. A positive must return exactly the listed document IDs in order; a negative must return `[]`; every returned passage must be an exact source slice. Exact-subject absent-detail positives require only retrieval of subject context and make no claim that the absent detail is answered. The contract does not test arbitrary language understanding or answer classification.

| Check | Fresh query/input | Fixed expectation |
| --- | --- | --- |
| ordinary-role | `Who organized Project Sable's shoreline trial?` | `[doc-sable]` |
| ordinary-date | `When did Project Sable's shoreline trial open?` | `[doc-sable]` |
| oov-discourse-modifiers | `Briefly, amid sleet, can you sketch who orchestrated Project Sable's shoreline trial?` | `[doc-sable]` |
| exact-structural-subject | `Did Briarhaven Office organize Project Sable's trial?` | `[doc-sable]` |
| absent-structural-subject | `Did Blackmarsh Office organize Project Sable's trial?` | `[]` |
| neither-nor-leading-copula | `Were neither the Dovetail Bureau nor the Mosswick Committee listed for Project Rowanfall?` | `[doc-rowanfall]` |
| neither-nor-no-auxiliary | `Neither Dovetail Bureau nor Mosswick Committee was absent from Project Rowanfall's ledger.` | `[doc-rowanfall]` |
| either-or-tail-marker | `Did Project Rowanfall list the Dovetail Bureau or the Mosswick Committee, either one?` | `[doc-rowanfall]` |
| both-and-trailing-marker | `Were the Dovetail Bureau and the Mosswick Committee both listed in Project Rowanfall?` | `[doc-rowanfall]` |
| paired-absent-second-subject | `Were neither the Dovetail Bureau nor the Ravenmere Committee listed for Project Rowanfall?` | `[]` |
| anchored-raw-transposition | `Did Project Piengrove list Silvercrest Bureau?` | `[doc-pinegrove]` |
| anchored-raw-deletion | `Did Project Pinegrov list Silvercrest Bureau?` | `[doc-pinegrove]` |
| anchored-raw-substitution | `Did Project Pinegruve list Silvercrest Bureau?` | `[]` |
| unanchored-raw-transposition | `Did Project Piengrove stage the winter trial?` | `[]` |
| exact-subject-absent-insurer | `Which insurer guaranteed Project Pinegrove's winter trial?` | `[doc-pinegrove]`; context only |
| exact-subject-absent-radio-detail | `What radio frequency did Project Pinegrove's trial use?` | `[doc-pinegrove]`; context only |
| absent-subject-matching-badge-details | `Which amber badge did Project Nightglass issue?` | `[]` |
| absent-subject-matching-insurer-details | `Which insurer covered Project Nightglass's winter trial with Atlas Mutual?` | `[]` |
| exact-score-tie | two byte-identical Emberfall documents with IDs `doc-emberfall-a`, `doc-emberfall-b` | IDs in lexical order and equal scores |
| paragraph-priority | 120 `P`s, paragraph break, later sentence break before char 200 | first window `(0, 120)` |
| sentence-priority | 120 `A`s, sentence break, later word break before char 200 | first window `(0, 121)` |
| word-priority | 130 `D`s, ordinary space, no stronger boundary before char 200 | first window `(0, 130)` |
| exact-multi-window-offsets | three 125-character paragraphs separated by `\n\n`, `max_chunk_chars=200`, `overlap_chars=0` | `[(0,125), (127,252), (254,379)]` and every text equals its exact source slice |

Synthetic sources are fixed as follows:

- `doc-sable`: title `Project Sable coordination file`; body `The Briarhaven Office organized Project Sable's shoreline trial. The team opened it on 9 September 1994.`
- `doc-rowanfall`: title `Project Rowanfall participant ledger`; body `Project Rowanfall's participant ledger lists Dovetail Bureau and Mosswick Committee. The archived entry says both organizations attended the summit.`
- `doc-pinegrove`: title `Project Pinegrove registry`; body `Project Pinegrove's registry lists Silvercrest Bureau as organizer of the winter trial.`
- absent-detail safety source `doc-cedarwake`: title `Project Cedarwake supply ledger`; body `Project Cedarwake issued an amber badge and Atlas Mutual covered its winter trial.`
- the tie sources share title `Project Emberfall coordination record` and body `Coveglass Office organized Project Emberfall's harbor trial.`

## Execution evidence

All commands ran from `/home/brian/code/crest_kg/worktrees/codex-crest-evidence-synthesis-week` at exact clean code revision `6469e7c279d01d79a59f9069eed56bd7ec61f99e`. The only working-tree addition during verification was this sign-off artifact.

### Frozen fixtures, twice

Exact runner command for each pass:

```bash
for version in $(seq 5 16); do
  .venv/bin/python evaluation/run_evidence_retrieval_eval.py \
    --fixture "evaluation/evidence_retrieval_set_v${version}.json"
done
```

The complete stdout from pass one and pass two compared byte-identically. Canonical evidence:

- 12/12 fixtures passed;
- 99/99 cases passed;
- 99/99 cases reported exact valid offsets;
- stdout size: 28,074 bytes after shell trailing-newline removal;
- SHA-256 of either aggregate stdout: `d87d9f7c6ef3fb45bdcfda82a62d10816f5899a6f9f20f9e21bc63eb107c60ce`.

### Fresh contract, twice

Exact invocation for each pass:

```bash
PYTHONPATH=. .venv/bin/python - <<'PY'
# Inline deterministic runner encoding the 23 fixed rows and five fixed
# synthetic sources above. It called rank_evidence for the 19 rank rows and
# chunk_document(max_chunk_chars=200, overlap_chars=0) for the four boundary
# rows, checked exact source slices, and emitted json.dumps(...,
# sort_keys=True, separators=(",", ":")).
PY
```

The inline runner was invoked twice without modification; the two complete JSON outputs compared byte-identically. Canonical evidence:

- 22/23 checks passed;
- all 19/19 ranking/admission checks passed;
- 13/13 fresh ranking positives returned exactly the expected IDs and order;
- 6/6 fresh ranking negatives returned `[]`;
- all returned ranking passages were exact source slices;
- exact-score tie: `doc-emberfall-a`, then `doc-emberfall-b`, both score `6.29765681`, both offsets `(0,60)`;
- `doc-sable` positives returned `(0,104)`, `doc-rowanfall` positives returned `(0,148)`, and `doc-pinegrove` positives returned `(0,87)`;
- paragraph priority passed with first window `(0,120)`;
- word priority passed with first window `(0,130)`;
- exact multi-window offsets passed as `[(0,125), (127,252), (254,379)]`, with every text equal to its source slice;
- stdout size: 4,232 bytes after shell trailing-newline removal;
- SHA-256 of either complete JSON stdout: `861584894ebec9ee615cede68920dddb10267a3a7141ec5916e5bc63cf0d0f67`.

One fixed expectation failed identically on both runs:

```text
case: sentence-priority
input around boundary: body[118:123] == "AA. B"
fixed expected first window: (0,121)
actual windows: [(0,120), (122,253)]
actual first text ends with period: false
all emitted texts are exact source slices: true
```

The sentence candidate is found at the period's index, `120`, but the first half-open window ends at `120`, excluding the period. The next window begins at `122`, after the following space. Thus the terminal period is omitted from every chunk. This is a real failure of the fixed sentence-boundary offset contract; exact slicing of each retained range does not repair the source-byte gap between ranges.

The focused runtime diagnosis was reproduced with:

```bash
PYTHONPATH=. .venv/bin/python - <<'PY'
from crest_app.retrieval import RetrievalDocument, chunk_document
body = "A" * 120 + ". " + "B" * 50 + " " + "C" * 80
doc = RetrievalDocument("doc-sentence-priority", "bundled-crest", "Boundary probe", body)
chunks = chunk_document(doc, max_chunk_chars=200, overlap_chars=0)
print([(item.start_char, item.end_char) for item in chunks])
print(chunks[0].text.endswith("."))
print(all(body[item.start_char:item.end_char] == item.text for item in chunks))
PY
```

It printed `[(0, 120), (122, 253)]`, `False`, and `True`.

### Repository and build adequacy

```bash
PYTHONPATH=. .venv/bin/python -m pytest -q
node --check web/app.js
.venv/bin/python -m pip check
git diff --check
```

Results:

- pytest: `51 passed, 1 warning in 8.19s`; the warning is the existing Starlette `httpx` deprecation warning;
- JavaScript syntax check: exit 0, no output;
- dependency check: `No broken requirements found.`;
- diff whitespace check: exit 0, no output.

### Mechanism and comparison with rejected revision

Exact comparison commands:

```bash
git diff --name-status c73e14c..6469e7c
git diff --unified=12 c73e14c..6469e7c -- crest_app/retrieval.py
git show --stat --oneline 6469e7c
```

The rejected base resolves to `c73e14ca3d44ed8e5251d8ed1a0ecbadfaa0f424`. Across that base and the evaluated revision, the retrieval mechanism changes only by adding `nor` to two domain-neutral sets:

1. `STOP_WORDS`, so `nor` cannot become an independent query concept whose absence suppresses a relevant passage; and
2. `_structural_subject_surfaces.boundary_terms`, so the backward short-noun-phrase scan cannot cross `nor` and merge the two sides of a paired subject.

The repository delta also freezes v16, points the fixture runner default at v16, and includes v16 in the fixture test. The fresh paired checks all pass across leading-copula, no-auxiliary, tail-marker, trailing-marker, and absent-second-subject forms. That is credible same-class generalization and is not tied to fixture entity names.

The decisive failure is separate and pre-existing, not introduced by the `nor` repair: `chunk_document` selects `. ` as the strongest available boundary, then line 681 computes `end = boundary + (1 if body[boundary] == " " else 0)`. At a sentence boundary `body[boundary]` is `.`, so the end remains at the period's index and omits it. Source inspection agrees with the fresh runtime result.

## Gate assessment

- gate 1 validity: **PASS** — ordinary positive controls, exact structural positives, paired-conjunction positives, exact-subject context positives, tie ordering, and three boundary controls execute successfully. The required environment is adequate: 51 tests pass, JavaScript parses, and dependencies are consistent. No component is unavailable or partial.
- gate 2 representativeness: **PASS** — the 23-check contract was fixed before execution, uses fresh entities and wording, and covers the requested compact cross-section: ordinary positives, exact/absent structural subjects, OOV wording, varied paired conjunctions, permitted raw variants plus substitution/unanchored safety, exact-subject absent details, absent-subject detail matches, tie order, boundary priority, and exact multi-window offsets. It is expressly limited to small synthetic deterministic retrieval.
- gate 3 diagnosis: **PASS** — the failure is class-level and directly reproduced. Sentence boundary discovery returns the period index, while the end calculation includes a delimiter only when the delimiter itself is a literal space; it therefore drops sentence-final punctuation at every such split rather than failing only this string.
- gate 4 generalization: **FAIL** — the `nor` repair itself generalizes across all five fresh paired-conjunction probes, all 19 fresh ranking/admission checks pass, and frozen v5-v16 has no regression. However, the complete held-out contract required for this ship decision is not green: the independent sentence-boundary/offset class fails reproducibly. A passing sub-mechanism does not license the wider exact-revision ship claim.
- gate 5 decision: **FAIL** — this cheap empirical gate is warranted because the decision depends on interacting deterministic admission and chunk-offset rules. The valid run produced a stable failure inside the precommitted contract, so the ship decision must not fire.

rejections / required fixes: Do not ship exact revision `6469e7c279d01d79a59f9069eed56bd7ec61f99e` under the proposed contract. Preserve the domain-neutral `nor` repair, but retain the sentence delimiter in the first window (or otherwise define and freeze an explicit no-byte-loss boundary contract), freeze this exact failure before repair, rerun v5-v16 and the focused chunk tests, and obtain another fresh independent sign-off. Narrowing the advertised decision to omit sentence-boundary offsets would be a different claim, not a reinterpretation of this run.

## Limitations and recommendation

This sign-off covers only deterministic passage retrieval and exact chunk offsets for small synthetic collections. It does not establish arbitrary language understanding, answer extraction or classification, multilingual behavior, real-corpus recall, semantic answer correctness, or production-scale performance. Exact-subject absent-detail positives establish context retrieval only.

Recommendation: **REJECT shipment of this exact revision under the stated contract.** The paired-conjunction repair is well targeted and generalizes in the fresh ranker checks, but the independently frozen sentence-boundary offset requirement fails twice with byte-identical evidence.
