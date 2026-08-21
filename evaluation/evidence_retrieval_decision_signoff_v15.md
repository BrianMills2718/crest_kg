# EVAL-DECISION SIGN-OFF — REJECTED

- decision: Ship exact revision `c73e14ca3d44ed8e5251d8ed1a0ecbadfaa0f424` as the deterministic passage retriever for small synthetic collections under the bounded contract below.
- eval: frozen `evaluation/evidence_retrieval_set_v5.json` through `evaluation/evidence_retrieval_set_v15.json`, plus the pre-execution fresh adversarial contract recorded here.
- verifier: fresh independent Codex verifier; execution completed `2026-08-21T08:55:26Z`.
- verdict: **REJECTED**.
- ship recommendation: **DO NOT SHIP this revision as the accepted retrieval boundary.** Preserve the demonstrated raw-surface, anchor-safety, chunk-boundary, and offset gains, but repair the paired `neither … nor` structural grammar and obtain another fresh independent sign-off.

The proposed capability is deterministic passage retrieval over small synthetic
collections. It must retrieve context rather than classify whether a proposition
is true. Thus the held-out question “Did neither Cedarbrook Committee nor
Foxglove Agency appear in Project Bluejay's record?” must retrieve the exact
Bluejay passage that names both subjects; the answer layer, not retrieval, would
decide how to answer the negative construction. The candidate reproducibly
returned no passage.

## Pre-execution fresh contract

Before the first fresh execution, the verifier fixed 45 checks over novel
entities, sentences, and queries not copied from frozen v5-v15 or earlier
sign-off contracts. The verifier-local runner was never added to a product
fixture, was not changed after execution, and had SHA-256
`61581cc3faddd5aaed481e53dc91813f2a2c648030281dde5f6f511f8ca3a700`.
It executed every retrieval case twice internally, checked exact document order,
compared complete evidence records, and verified every returned source slice.

| Contract class | Passed | Total |
| --- | ---: | ---: |
| Ordinary answerable paraphrases | 4 | 4 |
| Exact structural subjects across Project, possessive, `for`, `under`, `associated with`, auxiliary, `who`, and leading-copula placements | 8 | 8 |
| Absent structural subjects in the paired placements | 8 | 8 |
| OOV modifiers and verbs | 3 | 3 |
| Anchored raw-surface permutation, insertion, and deletion; same-length substitution rejection; unanchored variant rejection with generic heads | 6 | 6 |
| Auxiliary/determiner forms beyond `each` (`any`, `either`, `both`, `every`, `several`, `all`, `neither … nor`) | 6 | 7 |
| Exact-subject context with requested details absent | 2 | 2 |
| Absent subject despite matching requested details | 2 | 2 |
| Deterministic equal-score tie ordering | 1 | 1 |
| Exact three-window retrieval and offsets | 1 | 1 |
| Paragraph, sentence, and word chunk-boundary priority | 3 | 3 |
| **Total** | **44** | **45** |

The contract was executed twice without modification:

```bash
sha256sum evaluation/.evidence_retrieval_v15_fresh_contract.py
PYTHONPATH=. .venv/bin/python evaluation/.evidence_retrieval_v15_fresh_contract.py > /tmp/crest_retrieval_v15_fresh_run1.json
PYTHONPATH=. .venv/bin/python evaluation/.evidence_retrieval_v15_fresh_contract.py > /tmp/crest_retrieval_v15_fresh_run2.json 2> /tmp/crest_retrieval_v15_fresh_run2.err
cmp -s /tmp/crest_retrieval_v15_fresh_run1.json /tmp/crest_retrieval_v15_fresh_run2.json
sha256sum /tmp/crest_retrieval_v15_fresh_run1.json /tmp/crest_retrieval_v15_fresh_run2.json
```

Both executions exited `1`, both emitted byte-identical stdout with SHA-256
`907947675cfc3bbf64da091d2df8e1d15f59134d486d4214520497ba96019aff`,
the second emitted zero stderr bytes, and all 45 in-contract repeated checks were
internally deterministic. All 31 returned retrieval chunks and all six chunks
from the three direct boundary probes reproduced exact source slices.

The one fixed failure was:

| Case | Expected | Actual | Repeat |
| --- | --- | --- | --- |
| `determiner-neither-nor-did` — `Did neither Cedarbrook Committee nor Foxglove Agency appear in Project Bluejay's record?` | `doc-bluejay` | `[]` | identical in both complete runs and both in-process rankings per run |

The equal-score tie returned `a-equal`, then `z-equal`, both at score
`5.72928623`. The exact multi-window case returned the one Starling source at
`[0,150)`, `[152,302)`, and `[304,454)`, each at score `5.5009903`. The direct
boundary probes selected paragraph `[0,130)` over a later sentence and word,
sentence `[0,175)` over a later word, and word fallback `[0,220)`; their second
windows were `[132,310)`, `[177,300)`, and `[221,301)` respectively.

## Frozen regressions, twice

For every version from 5 through 15, the following runner was executed twice
with stdout and stderr captured separately and compared byte-for-byte:

```bash
PYTHONPATH=. .venv/bin/python evaluation/run_evidence_retrieval_eval.py \
  --fixture evaluation/evidence_retrieval_set_v${version}.json
```

| Fixture | Passed per run | Exits | stdout/stderr byte-identical | Invalid offset cases | stdout SHA-256 |
| --- | ---: | --- | --- | ---: | --- |
| v5 | 9/9 | 0/0 | yes/yes | 0 | `2616edcc3b558191968f77e9bcd03ce23f371ea3faf8019b5380eb3f489f1ee6` |
| v6 | 5/5 | 0/0 | yes/yes | 0 | `7066d2175797601cd8c2a134b62ed6a5e4fce69964a2c0b516fde2d5752325eb` |
| v7 | 6/6 | 0/0 | yes/yes | 0 | `9db4b8f9e3f469a51bfefb2d78f7d72da0750680fc62cbf3f78642d90d503056` |
| v8 | 7/7 | 0/0 | yes/yes | 0 | `0eb43041b9cde6ccc351b4d7e544280cbb1072473d16ee7250a04b6249d43aae` |
| v9 | 12/12 | 0/0 | yes/yes | 0 | `877d656503d2a8d6061f7b6c9c30cd6f850a45bcfb838304d63a0fd74fcbc651` |
| v10 | 29/29 | 0/0 | yes/yes | 0 | `ff76e61892876d28065405aa37c5ed1ab293ce23690421957db1de988fb8c0ed` |
| v11 | 13/13 | 0/0 | yes/yes | 0 | `599b5a047f623a22630a825ecb23ba213fc5955b4da7dfdcb10f41a938c2d225` |
| v12 | 2/2 | 0/0 | yes/yes | 0 | `8bd9861b4e7b36d3e955edb9965e5789708527dcc5ab7b89862a54b1ae5ee65f` |
| v13 | 3/3 | 0/0 | yes/yes | 0 | `35ef1fc5db05f75e887a79f6958a53e0fd7567ca96020941db6e23a1768c0da9` |
| v14 | 5/5 | 0/0 | yes/yes | 0 | `7098d28000e14543ef3ee4c443fc5bff29ce972167c2231a7587ebfcd342eead` |
| v15 | 5/5 | 0/0 | yes/yes | 0 | `03738084e669f002f522287f4334c63ebf692357fb2f32d26cab0ba29d3132ec` |
| **Total** | **96/96** | **all 0/0** | **yes/yes** | **0** | — |

The frozen fixtures returned 111 chunks per run; every case-level source-offset
check passed.

## Build and repository checks

```bash
PYTHONPATH=. .venv/bin/python -m pytest -q
node --check web/app.js
.venv/bin/python -m pip check
```

- `pytest`: exit `0`, `51 passed`, one third-party Starlette/httpx deprecation warning.
- `node --check`: exit `0`.
- `pip check`: exit `0`, `No broken requirements found.`

## Mechanism and generalization inspection

The exact compared revisions were resolved and inspected with:

```bash
git rev-parse d4b5255
git rev-parse c73e14c
git log --oneline d4b5255..c73e14c
git diff --stat d4b5255..c73e14c
git diff --unified=100 d4b5255..c73e14c -- crest_app/retrieval.py
git diff --unified=60 d4b5255..c73e14c -- \
  tests/test_evidence_retrieval.py evaluation/evidence_retrieval_set_v15.json \
  evaluation/run_evidence_retrieval_eval.py
```

The rejected base resolves to
`d4b525591d64577b0c9484a581f1afb51a9352f6`; the candidate resolves to
`c73e14ca3d44ed8e5251d8ed1a0ecbadfaa0f424`. The change is mechanism-level:
it validates benign name edit shapes on raw surfaces rather than stems, excludes
generic structural heads from exact named anchors, adds common determiners to
stop words, and changes chunk selection from the latest boundary to explicit
paragraph/sentence/word priority. The frozen v15 and fresh passing cases show
those mechanisms generalize across new names, all three permitted edit shapes,
same-length substitution safety, unanchored generic-head safety, exact-subject
absent-detail context, deterministic ties, and exact windows.

The auxiliary/determiner repair is incomplete as a class. Runtime diagnosis of
the exact failure produced:

```text
tokens: ('cedarbrook', 'committ', 'nor', 'foxglov', 'agency', 'project', 'bluejay', 'record')
structural_subject_surfaces: ['bluejay', 'cedarbrook', 'nor']
ranked: []
```

`neither` was added to `STOP_WORDS`, but `nor` was added to neither `STOP_WORDS`
nor `_structural_subject_surfaces.boundary_terms`. When the noun-phrase scan
walks backward from `Agency`, it crosses `nor` and promotes it instead of
`Foxglove` as the structural subject. Because the source has no `nor` identity,
subject admission rejects the otherwise exact passage. The paired held-out
`either … or` query extracted `bluejay`, `cedarbrook`, and `foxglove` and
retrieved `doc-bluejay`; the held-out `both … and` query did the same. This is a
bounded grammar-class miss, not an entity-specific failure, nondeterminism, or
unavailable component.

## Integrity gates

- gate 1 validity: **PASS** — The checkout was clean at the exact requested SHA before the verifier-local contract. Four of four fresh ordinary positive controls retrieved their expected passages. Frozen v5-v15 passed 96/96 twice, the repository passed 51 tests, Node parsed the web entrypoint, dependencies were consistent, and all returned source slices were exact. The fresh failure is a responsive capability failure, not an unavailable build, index, or service.
- gate 2 representativeness: **PASS** — The fixed 45-check contract used new entities and source sentences and covered every requested positive, negative, OOV, structural-placement, raw-edit, determiner, detail, tie, boundary-priority, and exact-window class within the stated small-synthetic-collection boundary.
- gate 3 diagnosis: **PASS** — The failure is explained at the class mechanism: incomplete paired-conjunction grammar lets `nor` become a mandatory structural identity after the repair recognized `neither`.
- gate 4 generalization: **FAIL** — Raw-surface edit safety, generic-head anchor safety, chunk priority, offsets, and six auxiliary/determiner forms generalized, but the auxiliary/determiner repair failed the materially different held-out `neither … nor` form. Passing the single frozen `each` case and the broad repository suite does not override a reproducible in-boundary false abstention.
- gate 5 decision: **FAIL** — A cheap deterministic sign-off is justified for this reversible local retrieval boundary, and the run is valid. The ship decision cannot fire on a fixed 44/45 fresh contract with a byte-identical exact-subject false abstention.

## Required disposition and limitations

Do not ship `c73e14ca3d44ed8e5251d8ed1a0ecbadfaa0f424` as the accepted
small-synthetic-collection retriever. Freeze the exact `neither … nor` failure,
make paired conjunctions terminate or skip structural noun-phrase scanning
without converting either conjunction into an identity, retain the passing
`either … or`, `both … and`, raw-edit, anchor-safety, boundary, and offset
behavior, rerun frozen v5-v15, and require another materially new independent
sign-off.

This sign-off covers deterministic passage admission, rank order, chunk-boundary
selection, and exact offsets over small synthetic collections. It does not
establish real-corpus recall, answer correctness or answer-status classification,
arbitrary semantic parsing, multilingual behavior, or production performance.
Those limitations do not soften the rejection because the failed exact-subject
retrieval lies inside the narrower proposed ship boundary.
