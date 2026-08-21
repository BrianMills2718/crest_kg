# EVAL-DECISION SIGN-OFF — CREST evidence retrieval v14

decision: Ship exact revision `d4b525591d64577b0c9484a581f1afb51a9352f6` as the deterministic passage retriever for small synthetic collections under the bounded contract below.

eval: frozen `evaluation/evidence_retrieval_set_v5.json` through `evaluation/evidence_retrieval_set_v14.json`, plus the precommitted fresh adversarial contract recorded here.

verifier: fresh independent Codex subagent; execution completed 2026-08-21 UTC.

verdict: **REJECTED**

## Bounded decision contract

The proposed capability is deterministic passage retrieval for small synthetic collections. It must retrieve context for answerable paraphrases and exact subjects, preserve exact source windows, use deterministic tie ordering, tolerate only bounded benign subject-name edits when separately anchored, and reject absent subjects even when generic relation or requested-detail vocabulary matches.

This decision does **not** claim answer classification, arbitrary semantic parsing, real-world recall, or production-scale retrieval.

Before the first fresh execution, the verifier fixed 19 probes over four new synthetic document scenarios. The contract was not changed after execution. The verifier-local runner SHA-256 was `83ced73e41ed306dbb4ff10db0fa3b0e134977cc0c6cb378703491991e0e8803`.

The new source identities and body bindings were:

| Document | Length | Body SHA-256 | Purpose |
| --- | ---: | --- | --- |
| `doc-sundial` | 302 | `31f5b8abf43d3a4bd44c6dc518ba32c29c66b1de4542ad2ea84f17c05e029c94` | Answerable paraphrases, structural subjects, new proper names, and subject-safety controls |
| `doc-telltale` | 433 | `c6dad2fff1063bb852a922eac954c7884b01c5d7bb876c5f8872cfa387aad133` | Three repeated 143-character paragraphs separated by two newlines; expected windows `(0,143)`, `(145,288)`, `(290,433)` |
| `tie-abel` | 75 | `599086e12bc44212a5cd01ee97bb56ab1299ffe4f360da10f0f331b6afa08c2e` | First member of an exact-score tie |
| `tie-baker` | 75 | `599086e12bc44212a5cd01ee97bb56ab1299ffe4f360da10f0f331b6afa08c2e` | Second member of an exact-score tie |

The `doc-sundial` body was:

> The Coppermeadowlark Committee coordinated Project Sundial in Valparaiso. The harbor rehearsal began on 8 September 1994. The dispatch catalogued indigo markers beside the north gate. Silverbell Office filed the logistics note for Project Sundial. Juniper Agency reviewed the note before the rehearsal.

Each `doc-telltale` paragraph was:

> Project Telltale ledger states the Bronze Wren Office coordinated the harbor rehearsal on 4 April 1996. Evidence remains archived in bay seven.

Both tie documents used:

> Project Equipoise began on 2 February 1997. The Rowan Office kept the card.

The exact fresh questions and fixed oracles were:

| ID / class | Exact question | Fixed oracle | Result |
| --- | --- | --- | --- |
| `p01-oov-discourse-and-verb` / answerable paraphrase + OOV | Parenthetically, who shepherded Project Sundial at Valparaiso, and when did the harbor drill get underway? | `doc-sundial` | PASS |
| `p02-possessive-subject` / possessive placement | Sundial's harbor drill: which body put it on and what date marks its beginning? | `doc-sundial` | PASS |
| `p03-for-relation` / `for` placement | Which office filed the logistics note for Sundial? | `doc-sundial` | PASS |
| `p04-associated-with-relation` / associated-with placement | Was the harbor rehearsal associated with Sundial? | `doc-sundial` | PASS |
| `p05-exact-subject-absent-three-details` / exact-subject context | Which ultraviolet badge, insurance carrier, and radio channel were assigned under Sundial? | `doc-sundial` | PASS |
| `p06-anchored-three-cycle-permutation` / benign name permutation | Did Coppermeadowarkl Committee coordinate Project Sundial? | `doc-sundial` | PASS |
| `p07-anchored-one-deletion` / benign name deletion | Did Silverbel Office file Project Sundial's logistics note? | `doc-sundial` | PASS |
| `p08-anchored-one-insertion` / benign name insertion | Did Juniperr Agency review Project Sundial's logistics note? | `doc-sundial` | PASS |
| `n01-lowercase-external-project-with-real-details` / absent external subject | which committee coordinated project frostmoth in Valparaiso on 8 September 1994? | `[]` | PASS |
| `n02-missing-actor-with-requested-detail-matches` / missing subject + detail matches | Did Marigold Committee catalogue indigo markers beside the north gate for Project Sundial? | `[]` | PASS |
| `n03-anchored-same-length-substitution` / substitution safety | Did Coppermeadowlars Committee coordinate Project Sundial? | `[]` | **FAIL: `doc-sundial`** |
| `n04-permutation-without-independent-anchor` / anchor safety | Did Coppermeadowarkl Committee coordinate the rehearsal? | `[]` | PASS |
| `n05-deletion-without-independent-anchor` / anchor safety | Did Silverbel Office file the logistics note? | `[]` | **FAIL: `doc-sundial`** |
| `n06-under-relation-missing-subject-with-details` / `under` negative | Which office catalogued indigo markers beside the north gate under Rainshadow? | `[]` | PASS |
| `n07-external-project-with-date-and-place` / absent external subject | What began on 8 September 1994 for Project Frostmoth in Valparaiso? | `[]` | PASS |
| `n08-unrelated-oov-control` / no support | Describe geothermal sonograms from Pelagic Observatory. | `[]` | PASS |
| `s01-leading-copula-exact-subject` / leading-copula placement | Was Coppermeadowlark responsible for Project Sundial? | `doc-sundial` | PASS |
| `t01-exact-score-tie-document-order` / tie ordering | When did Project Equipoise begin? | exact order `tie-abel`, `tie-baker`; equal score | PASS |
| `w01-three-exact-windows` / multi-window offsets | What does each Project Telltale ledger say about the harbor rehearsal? | offsets `(0,143)`, `(145,288)`, `(290,433)` | **FAIL: `[]`** |

## Gate assessment

gate 1 validity: **PASS** — The checkout was clean at exact revision `d4b525591d64577b0c9484a581f1afb51a9352f6` before the sign-off artifact. Python 3.12.3 loaded `RetrievalDocument` and `rank_evidence`; `pip check` reported no broken requirements. Frozen v5-v14 produced 91/91 passing cases on each of two executions, with every returned source slice exact. The repository suite reported `50 passed` and the JavaScript syntax check exited 0. The fresh suite's positive controls retrieved supported passages, so the component was built and responsive; the three failures are capability failures, not unavailable infrastructure.

gate 2 representativeness: **PASS** — The fresh contract uses names, documents, wording, and edit shapes absent from frozen v5-v14. It covers answerable paraphrases, absent external subjects, OOV discourse/verbs, possessive/`for`/`under`/`associated with`/leading-copula subject placements, a three-cycle name permutation, one deletion, one insertion, same-length substitution safety with an exact project anchor, exact-subject retrieval with three absent requested details, missing-subject rejection despite exact requested-detail matches, exact-score tie ordering, repeat determinism, and three explicit source windows. It is representative only of the stated small-synthetic-collection boundary.

gate 3 diagnosis: **PASS** — The three failures have class-level mechanisms:

1. Subject edit shape is checked after stemming. Surface `Coppermeadowlars` versus `Coppermeadowlark` is a same-length final-character substitution, but `_stem` strips the query's terminal `s`, producing `coppermeadowlar` versus `coppermeadowlark`; `_benign_named_variant` then misclassifies it as an allowed one-character deletion.
2. The independent-anchor rule admits generic capitalized structural heads. `_source_named_terms` retains `office`, so exact `Office` satisfies `exact_named_anchor_indexes` and allows unanchored `Silverbel` to match `Silverbell`.
3. Auxiliary-led structural extraction promotes ordinary intervening vocabulary to mandatory identity. For `What does each Project Telltale ...`, `_structural_subject_surfaces` emits `each`, `harbor`, and `telltale`; absent `each` rejects all three exact-subject windows.

gate 4 generalization: **FAIL** — The change from rejected revision `1e388eb` to `d4b5255` is mechanism-level rather than fixture-name hard-coding: it adds `_benign_named_variant`, applies an exact-subject one-match admission path, and distinguishes benign variants from substitutions. It clears frozen v5-v14 and fresh anchored three-cycle/insertion/deletion positives, exact-subject absent-detail retrieval, external-subject controls, detail-match negatives, and tie ordering. It does not generalize across the held-out edit and structural forms above. The fresh suite passed only 16/19. Both runs exited 1 and were byte-identical with SHA-256 `6deb6ae6510237cfe12f606624dfdf6c92dafac02e31fff2b19954178cd2a07f`. All 13 chunks that were returned had exact source slices, but the required three-window case returned no chunks and therefore did not produce the precommitted offsets.

gate 5 decision: **FAIL** — A cheap execution gate is justified for this deterministic, reversible retrieval mechanism, and the run is valid. The ship decision cannot fire because the held-out contract contains two false admissions and one exact-subject false abstention. Passing frozen regressions and the broad repository suite does not override failed fresh generalization.

## Execution evidence

Fresh contract, twice without modification:

```bash
sha256sum /home/brian/code/.crest_signoff_v14_fresh_contract.py
PYTHONPATH=. .venv/bin/python /home/brian/code/.crest_signoff_v14_fresh_contract.py > /tmp/crest_signoff_v14_fresh_run1.json
PYTHONPATH=. .venv/bin/python /home/brian/code/.crest_signoff_v14_fresh_contract.py > /tmp/crest_signoff_v14_fresh_run2.json
cmp -s /tmp/crest_signoff_v14_fresh_run1.json /tmp/crest_signoff_v14_fresh_run2.json
sha256sum /tmp/crest_signoff_v14_fresh_run1.json /tmp/crest_signoff_v14_fresh_run2.json
```

Observed: contract SHA-256 `83ced73e41ed306dbb4ff10db0fa3b0e134977cc0c6cb378703491991e0e8803`; exits `1/1`; `cmp` exit 0; both result files SHA-256 `6deb6ae6510237cfe12f606624dfdf6c92dafac02e31fff2b19954178cd2a07f`; 16/19 passed.

Frozen v5-v14, each executed twice and compared byte-for-byte:

```bash
for version in 5 6 7 8 9 10 11 12 13 14; do
  fixture="evaluation/evidence_retrieval_set_v${version}.json"
  PYTHONPATH=. .venv/bin/python evaluation/run_evidence_retrieval_eval.py --fixture "$fixture" > "/tmp/crest_v${version}_run1.json"
  PYTHONPATH=. .venv/bin/python evaluation/run_evidence_retrieval_eval.py --fixture "$fixture" > "/tmp/crest_v${version}_run2.json"
  cmp -s "/tmp/crest_v${version}_run1.json" "/tmp/crest_v${version}_run2.json"
done
```

| Fixture | Passed | Run-1/2 exits | Byte-identical | Invalid offsets | Output SHA-256 |
| --- | ---: | --- | --- | ---: | --- |
| v5 | 9/9 | 0/0 | yes | 0 | `2616edcc3b558191968f77e9bcd03ce23f371ea3faf8019b5380eb3f489f1ee6` |
| v6 | 5/5 | 0/0 | yes | 0 | `7066d2175797601cd8c2a134b62ed6a5e4fce69964a2c0b516fde2d5752325eb` |
| v7 | 6/6 | 0/0 | yes | 0 | `9db4b8f9e3f469a51bfefb2d78f7d72da0750680fc62cbf3f78642d90d503056` |
| v8 | 7/7 | 0/0 | yes | 0 | `0eb43041b9cde6ccc351b4d7e544280cbb1072473d16ee7250a04b6249d43aae` |
| v9 | 12/12 | 0/0 | yes | 0 | `877d656503d2a8d6061f7b6c9c30cd6f850a45bcfb838304d63a0fd74fcbc651` |
| v10 | 29/29 | 0/0 | yes | 0 | `ff76e61892876d28065405aa37c5ed1ab293ce23690421957db1de988fb8c0ed` |
| v11 | 13/13 | 0/0 | yes | 0 | `599b5a047f623a22630a825ecb23ba213fc5955b4da7dfdcb10f41a938c2d225` |
| v12 | 2/2 | 0/0 | yes | 0 | `8bd9861b4e7b36d3e955edb9965e5789708527dcc5ab7b89862a54b1ae5ee65f` |
| v13 | 3/3 | 0/0 | yes | 0 | `35ef1fc5db05f75e887a79f6958a53e0fd7567ca96020941db6e23a1768c0da9` |
| v14 | 5/5 | 0/0 | yes | 0 | `7098d28000e14543ef3ee4c443fc5bff29ce972167c2231a7587ebfcd342eead` |

Repository checks:

```bash
PYTHONPATH=. .venv/bin/python -m pytest -q
node --check web/app.js
```

Observed: `50 passed, 1 warning in 7.67s`; `node --check` exited 0 with no output. The warning is Starlette's deprecation notice for its `httpx` test-client import and did not affect this decision.

Mechanism inspection:

```bash
git diff --stat 1e388eb d4b525591d64577b0c9484a581f1afb51a9352f6
git diff --unified=100 1e388eb d4b525591d64577b0c9484a581f1afb51a9352f6 -- crest_app/retrieval.py
git diff --unified=80 1e388eb d4b525591d64577b0c9484a581f1afb51a9352f6 -- tests/test_evidence_retrieval.py evaluation/evidence_retrieval_set_v14.json
```

Observed implementation delta: 55 changed lines in `crest_app/retrieval.py`, adding `_benign_named_variant`, exact-subject minimum-match handling, and the new subject-variant admission branch; v14 is bound into the frozen test loop. No evaluated implementation or fixture was modified by this verifier.

## Limitations

- This is offline synthetic evidence for a small deterministic collection. It says nothing about real CREST corpus recall, answer correctness, or broad natural-language understanding.
- Exact offsets were proven for every returned chunk. The required multi-window offsets were not produced because that case false-abstained.
- JavaScript received a syntax check, not browser interaction testing; browser behavior is outside this retrieval decision.
- The full Python run emitted one dependency deprecation warning that is unrelated to retrieval behavior.

## Rejection and ship recommendation

Do **not** ship exact revision `d4b525591d64577b0c9484a581f1afb51a9352f6` under the stated retrieval contract.

Freeze the three exact fresh failures before repair. The next candidate should evaluate proper-name edit shape on unstemmed name surfaces (or otherwise prove that stemming cannot convert substitutions into insertions/deletions), exclude generic role/head words such as `Office` from independent named-anchor evidence, and prevent auxiliaries from promoting determiners/discourse words such as `each` into mandatory subjects. Then rerun frozen v5-v14 twice and obtain another materially new independent sign-off.
