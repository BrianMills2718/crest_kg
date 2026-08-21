# CREST evidence-retrieval decision sign-off v13

## Decision

EVAL-DECISION SIGN-OFF

- decision: ship the small-collection evidence-retrieval behavior at revision `1e388eb0daf5f3fc8d9c0c485d171ff5274a7fe0`
- rejected base inspected: `f56456ab93510753f964b1a4b7a7881301cb6ffb`
- verifier: fresh independent Codex verifier; no code or frozen fixture changes
- execution date: 2026-08-21 UTC
- verdict: **REJECTED**
- ship recommendation: **DO NOT SHIP this revision as the accepted retrieval boundary.** Freeze both fresh failures, repair the false-admission mechanism without suppressing benign anchored variants or OOV context retrieval, and require another independent held-out sign-off.

The decisive failure is not a score interpretation: an absent structural name at `0.9230769230769231` similarity returned evidence when an unrelated exact project anchor was present. The same absent name without that anchor correctly returned no evidence. This is the exact false-admission seam created by using an independent named anchor as permission for a fuzzy structural subject.

## Pre-execution fresh contract

The contract was authored completely before its first execution at `/tmp/crest_retrieval_signoff_v13_contract.py`.

- contract SHA-256: `9db6f52bb56561e8ca60e789e1f4e6d0285a6e821b166b8fba772a580fbf81e9`
- size and pre-run modification time: `14295` bytes; `2026-08-21 01:22:39.811891099 -0700`
- revision declared inside the contract: `1e388eb0daf5f3fc8d9c0c485d171ff5274a7fe0`
- bounded scope: deterministic passage admission, rank order, and exact source offsets over a four-document synthetic collection; no answer extraction, answer classification, arbitrary semantic parsing, or real-world recall claim
- novelty: new Azimuth/Halyard/Lattice/Ember/Zephyr documents and Winterharborn variants; a pre-run search found none of those distinctive names in `evaluation/`, `tests/`, `crest_app/`, `web/`, or `README.md`. I did not read frozen fixture bodies or prior sign-off artifacts before fixing the contract.

The 29 fixed checks were:

| Category | Checks | Fixed contract |
| --- | ---: | --- |
| Answerable paraphrases | 4 | Relevant passage must rank first for `put ... together`, `commence`, `got ... set`, and `supplied` paraphrases. |
| Absent external subjects | 4 | An absent project, `under` subject, or possessive subject must return no evidence even when a real place or project is also named. |
| OOV discourse/modifiers/verbs | 3 | Unknown discourse, adverbs, modifiers, and verbs must not suppress passages with structural exact anchors. |
| Structural subjects/relation placement | 6 | Project adjacency, possessive, `under`, and `associated with` placements must admit exact subjects and reject an absent one. |
| Anchored benign named variants | 2 | A declared adjacent transposition at `0.9` plus exact `Project Lattice`, and an exact case/possessive variant, must rank Lattice first. |
| False-admission safety around `0.85` | 5 | Threshold must be exactly `0.85`; a below-boundary absent name (`0.8461538461538461`) must be rejected with and without an exact anchor; an above-boundary absent name (`0.9230769230769231`) must also be rejected with and without an exact anchor. |
| Context-rich absent requested details | 3 | Exact structural subject context must remain retrievable when the requested insurance rider, badge pattern, or checksum is absent; this asks only for the relevant passage, not an answer. |
| Deterministic equal-score ordering | 1 | Reversed input documents with identical scores must order by `document_id`: `a-equal`, then `z-equal`. |
| Exact multi-window offsets | 1 | A later overlapping window must reproduce the exact source slice and stable result. |

No threshold or expected result was changed after execution.

## Execution evidence

### Exact revision and clean starting state

```bash
git status --short
git branch --show-current
git rev-parse HEAD
git rev-parse --verify 1e388eb0daf5f3fc8d9c0c485d171ff5274a7fe0^{commit}
```

The initial status was empty; branch was `codex/crest-evidence-synthesis-week`; both revision commands returned `1e388eb0daf5f3fc8d9c0c485d171ff5274a7fe0`. The remote branch also resolved to that SHA before the artifact was written.

### Fresh contract, twice

```bash
PYTHONPATH=. .venv/bin/python /tmp/crest_retrieval_signoff_v13_contract.py > /tmp/crest-v13-fresh-run-1.json
PYTHONPATH=. .venv/bin/python /tmp/crest_retrieval_signoff_v13_contract.py > /tmp/crest-v13-fresh-run-2.json
cmp -s /tmp/crest-v13-fresh-run-1.json /tmp/crest-v13-fresh-run-2.json
sha256sum /tmp/crest-v13-fresh-run-1.json /tmp/crest-v13-fresh-run-2.json
```

- both runs exited `1` because the fixed contract failed
- `cmp` exited `0`; outputs were byte-identical
- both output SHA-256 values: `e42a05e08fde33529583bf2583cfc6c8039ea6a1e3895579cdcb4775b5304494`
- result: **27/29 passed, 2/29 failed** on each run
- all 28 in-contract repeated ranking comparisons were deterministic
- all 40 returned-chunk slice checks across the paired in-contract rankings had exact offsets

Category results:

| Category | Result |
| --- | ---: |
| Answerable paraphrase | 4/4 |
| Absent external subject | 4/4 |
| OOV discourse/modifier/verb | 3/3 |
| Structural subject/relation placement | 6/6 |
| Anchored benign named variant | 2/2 |
| False-admission safety around `0.85` | **4/5** |
| Context-rich absent requested detail | **2/3** |
| Deterministic equal-score order | 1/1 |
| Exact multi-window offsets | 1/1 |

Failures, unchanged across both runs:

1. `fuzzy-above-absent-with-anchor`: query `What did Winterharborm file for Project Lattice?` was fixed to expect no evidence because `Winterharborm` is absent. It instead returned `doc-lattice`. The source contains `Winterharborn`; their similarity is `0.9230769230769231`. The paired query without `Project Lattice` correctly returned `[]`, proving that the independent exact anchor caused admission. The benign anchored transposition `Winterhabrorn` at `0.9` also correctly returned `doc-lattice`; the problem is not loss of benign-variant recall.
2. `missing-detail-badge`: query `Which ultraviolet badge pattern was assigned under Halyard?` was fixed to retrieve `doc-halyard` as subject context, but returned `[]`. `Halyard` was correctly extracted as the only structural subject and matched exactly. The passage says it carried cobalt flags; the three absent detail terms plus `assigned` left only one lexical concept match, below the global two-match admission minimum. This is a passage-retrieval miss and does not require classifying or answering the requested detail.

The deterministic tie probe returned `a-equal`, `z-equal` with identical scores `5.91160778`. The multi-window probe returned the exact source slice `[838:1075]` on both in-contract rankings.

### Frozen v5-v13, twice

For each `version` in `5 6 7 8 9 10 11 12 13` and each `round` in `1 2`:

```bash
PYTHONPATH=. .venv/bin/python evaluation/run_evidence_retrieval_eval.py --fixture "evaluation/evidence_retrieval_set_v${version}.json" > "$frozen_run_dir/$round/v${version}.json"
cmp -s "$frozen_run_dir/1/v${version}.json" "$frozen_run_dir/2/v${version}.json"
```

All 18 runner invocations exited `0`; all nine output pairs were byte-identical.

| Fixture | Cases passed per run | Output SHA-256 for both runs |
| --- | ---: | --- |
| v5 | 9/9 | `2616edcc3b558191968f77e9bcd03ce23f371ea3faf8019b5380eb3f489f1ee6` |
| v6 | 5/5 | `7066d2175797601cd8c2a134b62ed6a5e4fce69964a2c0b516fde2d5752325eb` |
| v7 | 6/6 | `9db4b8f9e3f469a51bfefb2d78f7d72da0750680fc62cbf3f78642d90d503056` |
| v8 | 7/7 | `0eb43041b9cde6ccc351b4d7e544280cbb1072473d16ee7250a04b6249d43aae` |
| v9 | 12/12 | `877d656503d2a8d6061f7b6c9c30cd6f850a45bcfb838304d63a0fd74fcbc651` |
| v10 | 29/29 | `ff76e61892876d28065405aa37c5ed1ab293ce23690421957db1de988fb8c0ed` |
| v11 | 13/13 | `599b5a047f623a22630a825ecb23ba213fc5955b4da7dfdcb10f41a938c2d225` |
| v12 | 2/2 | `8bd9861b4e7b36d3e955edb9965e5789708527dcc5ab7b89862a54b1ae5ee65f` |
| v13 | 3/3 | `35ef1fc5db05f75e887a79f6958a53e0fd7567ca96020941db6e23a1768c0da9` |

Aggregate per run: **86/86 cases passed**, including 86/86 case-level checks that every returned passage reproduced its exact source slice.

### Repository checks

```bash
PYTHONPATH=. .venv/bin/python -m pytest -q
node --check web/app.js
```

- pytest: `50 passed, 1 warning in 9.18s`; the warning is Starlette's `httpx` deprecation notice
- Node syntax check: exit `0`, no output

### Mechanism and generalization inspection

```bash
git log --oneline --no-merges f56456a..1e388eb0daf5f3fc8d9c0c485d171ff5274a7fe0
git diff --find-renames f56456a..1e388eb0daf5f3fc8d9c0c485d171ff5274a7fe0 -- crest_app/retrieval.py tests/test_evidence_retrieval.py evaluation/evidence_retrieval_set_v13.json
```

The production mechanism change is global: define `FUZZY_MATCH_THRESHOLD = 0.85` and replace all four prior `0.86` comparisons used for match admission, structural-subject admission, fuzzy-match counting, and scoring. Frozen v13 adds only:

- the previously observed `Lantner`/`Lantern` anchored acceptance;
- the same variant without an independent exact anchor;
- an unrelated absent `Nimbus` subject with a real location.

It does **not** test an absent name that is itself above the new fuzzy threshold and shares an independent exact anchor. The fresh `Winterharborm` failure therefore follows the changed class mechanism rather than a special fixture instance: any structural lookalike above `0.85` can be admitted when another named query term matches exactly. The threshold cannot distinguish a benign misspelling from an absent near-name.

The context-rich absent-detail miss is a second class-level limitation in the unchanged global two-match minimum: an exact structural subject does not suffice when requested-detail vocabulary is absent and the relation wording is also outside the configured lexical family.

## Integrity gates

EVAL-DECISION SIGN-OFF

- gate 1 validity: **PASS** — the clean requested SHA existed and ran; 4/4 fresh answerable paraphrase controls passed; all v5-v13 fixtures passed; 50 repository tests passed; Node parsed the web entrypoint; no dependency, index, or service was unavailable for this deterministic local boundary.
- gate 2 representativeness: **PASS** — the fresh contract was fixed before execution, used novel held-out entities and phrasings, covered all requested positive/negative, OOV, structural, fuzzy-boundary, detail, ordering, and offset classes, and remained bounded to the claimed small synthetic collection boundary.
- gate 3 diagnosis: **PASS** — failures are explained at class/mechanism level: fuzzy structural-subject admission plus any independent exact named anchor causes false admission; exact-subject context can be suppressed by the global two-match minimum when detail/relation vocabulary is absent.
- gate 4 generalization: **FAIL** — the frozen gain reproduces on v13 and the benign held-out transposition, but safety does not generalize to an above-threshold absent lookalike with an exact anchor. A separate required absent-detail class also failed. Passing frozen cases and repository tests do not override held-out class failures.
- gate 5 decision: **FAIL** — the evaluation was cheap, deterministic, decision-relevant, and valid, but the proposed ship decision cannot fire on 27/29 held-out checks with a reproducible false admission. Decision: reject this revision for shipment.

## Required fixes and limitations

Required before another ship sign-off:

1. Freeze the above-threshold absent-name-with-anchor failure and change structural-subject admission so a different exact named anchor cannot, by itself, license every fuzzy structural name above the global threshold. Preserve the passing benign anchored variant in a principled bounded class.
2. Freeze the exact-`under Halyard` absent-detail miss and restore relevant subject-context retrieval without broadly admitting unrelated passages. Keep requested-detail words from being mistaken for external subjects.
3. Re-run frozen v5 onward plus a new independent contract that again includes near-looking absent names on both sides of the fuzzy threshold, with and without independent exact anchors.

Limitations: this sign-off covers a small deterministic synthetic collection and passage retrieval only. It does not establish real-corpus recall, semantic answer correctness, answer-status classification, or production performance. Those limitations do not soften the rejection because the false admission occurs inside the narrower boundary claimed for shipment.
