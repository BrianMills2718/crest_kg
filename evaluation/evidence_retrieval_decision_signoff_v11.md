# CREST evidence-retrieval decision sign-off v11

EVAL-DECISION SIGN-OFF

- decision: ship the retrieval repair at `19e4c347c9fe6f5e6d67bc8b8b1ae33fdd43df2f`
- evaluated code revision: `19e4c347c9fe6f5e6d67bc8b8b1ae33fdd43df2f`
- parent revision inspected: `eef0942`
- verifier: fresh independent `eval-decision-signoff` agent
- date: 2026-08-21
- verdict: **REJECT** (`REJECTED` under the sign-off skill vocabulary)
- ship recommendation: **DO NOT SHIP** this revision

## Gate result

| Gate | Result | Execution evidence |
| --- | --- | --- |
| 1. Validity | PASS | The exact requested SHA was checked before the fresh run. Frozen v5-v11 passed 81/81 twice; all 14 process exits were 0; stdout and stderr were byte-identical within every pair. The positive answerable controls returned both decisive sources. The complete test suite passed 50/50, and `node --check web/app.js` passed. |
| 2. Representativeness | PASS | The verifier froze 24 materially new queries before calling the ranker. They cover answerable paraphrases, absent external subjects, arbitrary OOV verbs/modifiers, possessive and `Project` adjacency, source/event heads, auxiliary/`who`/copula forms, `for`/`under`/`associated with` relations, typos, and grounded context with an absent requested detail. Separate equal-score and long-text probes cover ordering and exact offsets. |
| 3. Diagnosis | PASS | The failure is class-level and reproducible: the subject extractor recognizes `for X` and `associated with X`, but not `under X`. It therefore extracts only `vienna` from `Who organized the Vienna exercise under Borealis?`, never makes absent subject `Borealis` an admission requirement, and returns unrelated Meridian passages. |
| 4. Generalization | **FAIL** | Fresh probes passed 23/24. The held-out `under`-relation negative returned `meridian-coordination`, `meridian-observation`, and `meridian-lisbon-distractor` instead of no evidence. A required structural form therefore did not generalize beyond the frozen fixtures. |
| 5. Decision | **FAIL** | A ship decision cannot fire on a revision with a demonstrated held-out false-admission class, even though frozen regressions and the broad test suite are green. |

## Frozen evaluation reruns

Command (each fixture executed twice by `subprocess.run(..., capture_output=True)` and compared as raw `bytes`):

```bash
PYTHONPATH=. .venv/bin/python - <<'PY'
# For each version 5..11, run exactly:
# [sys.executable, "evaluation/run_evidence_retrieval_eval.py",
#  "--fixture", str(Path.cwd() / "evaluation" /
#                    f"evidence_retrieval_set_v{version}.json")]
# Execute twice; compare CompletedProcess.stdout and .stderr byte-for-byte.
PY
```

| Fixture | Pass | Offset checks | Pair exits | Byte-identical stdout/stderr | stdout SHA-256 |
| --- | ---: | ---: | --- | --- | --- |
| v5 | 9/9 | 9/9 | 0, 0 | yes / yes | `2616edcc3b558191968f77e9bcd03ce23f371ea3faf8019b5380eb3f489f1ee6` |
| v6 | 5/5 | 5/5 | 0, 0 | yes / yes | `7066d2175797601cd8c2a134b62ed6a5e4fce69964a2c0b516fde2d5752325eb` |
| v7 | 6/6 | 6/6 | 0, 0 | yes / yes | `9db4b8f9e3f469a51bfefb2d78f7d72da0750680fc62cbf3f78642d90d503056` |
| v8 | 7/7 | 7/7 | 0, 0 | yes / yes | `0eb43041b9cde6ccc351b4d7e544280cbb1072473d16ee7250a04b6249d43aae` |
| v9 | 12/12 | 12/12 | 0, 0 | yes / yes | `877d656503d2a8d6061f7b6c9c30cd6f850a45bcfb838304d63a0fd74fcbc651` |
| v10 | 29/29 | 29/29 | 0, 0 | yes / yes | `ff76e61892876d28065405aa37c5ed1ab293ce23690421957db1de988fb8c0ed` |
| v11 | 13/13 | 13/13 | 0, 0 | yes / yes | `599b5a047f623a22630a825ecb23ba213fc5955b4da7dfdcb10f41a938c2d225` |
| **Total** | **81/81** | **81/81** | **14 zero exits** | **all pairs identical** | — |

This establishes deterministic frozen output and valid exact source slices for every frozen case. It does not establish held-out generalization.

## Fresh probe contract and results

The following contract was authored and frozen in verifier analysis before the first call to `rank_evidence`. It was not added to any product fixture. For answerable cases, `both` means that `meridian-coordination` and `meridian-observation` must both appear within `limit=4`, with `meridian-lisbon-distractor` absent from the top two. For absent-subject cases, `[]` means no evidence. Contextual absent-detail cases require both grounded sources but deliberately make no answerability/synthesis claim.

Command:

```bash
PYTHONPATH=. .venv/bin/python - <<'PY'
# Construct RetrievalDocument objects from v11's unchanged document corpus.
# Execute the 24 predeclared rows below twice with rank_evidence(..., limit=4).
# Grade expected IDs/empty output, top-two distractor rule where applicable,
# and body_text[start_char:end_char] == text for every returned chunk.
# Serialize both complete result lists with sorted keys and compact separators,
# then compare the resulting bytes.
PY
```

| ID | Fresh query | Declared expectation | Actual IDs | Result |
| --- | --- | --- | --- | --- |
| answerable-possessive-oov | Obliquely, who masterminded Meridian's Vienna undertaking, and which pair of May days bounded its kickoff? | both | coordination, observation, Lisbon | PASS |
| answerable-project-following | Project Meridian: which outfit helmed the Vienna rehearsal, and what were its proposed and actual inception days? | both | observation, coordination, Lisbon | PASS |
| answerable-project-preceding | For Meridian Project records, who shepherded the Austrian exercise and on which May days did it open? | both | coordination, observation, Lisbon | PASS |
| answerable-source-head | Across the Meridian source file, what body convened the Vienna pilot and which opening dates disagree? | both | observation, coordination, Lisbon | PASS |
| answerable-event-head | The Meridian Vienna event was assembled by whom, and what two May starts are in its accounts? | both | coordination, observation, Lisbon | PASS |
| answerable-who | Who shepherded Meridian in Vienna, and which preliminary and corrected May starts apply? | both | observation, coordination, Lisbon | PASS |
| answerable-copula | Was Meridian the project behind the Vienna pilot, and what two opening days are recorded? | both | coordination, observation, Lisbon | PASS |
| answerable-for | What two opening days and convening body are recorded for Meridian? | both | coordination, observation, Lisbon | PASS |
| answerable-associated-with | Which organizer and start dates were associated with Meridian in the Vienna records? | both | coordination, observation, Lisbon | PASS |
| negative-possessive | Cygnus's Vienna exercise had which coordinator and opening date? | `[]` | `[]` | PASS |
| negative-project-following | Project Saffron held a Vienna pilot; who arranged it? | `[]` | `[]` | PASS |
| negative-project-preceding | For Borealis Project records, who supervised the Austrian demonstration? | `[]` | `[]` | PASS |
| negative-source-head | What does the Zephyr coordination note say about the Vienna opening? | `[]` | `[]` | PASS |
| negative-event-head | Who coordinated the Calypso Vienna event, and when was its debut? | `[]` | `[]` | PASS |
| negative-auxiliary-did | Did Juniper schedule the Vienna pilot for May? | `[]` | `[]` | PASS |
| negative-who | Who convened Solstice in Vienna? | `[]` | `[]` | PASS |
| negative-copula | Was Borealis the organizer of the Vienna exercise? | `[]` | `[]` | PASS |
| negative-for | What opening date is listed for Cinder? | `[]` | `[]` | PASS |
| **negative-under** | **Who organized the Vienna exercise under Borealis?** | **`[]`** | **coordination, observation, Lisbon** | **FAIL** |
| negative-associated-with | Which committee was associated with Cinder? | `[]` | `[]` | PASS |
| typo-viena-answerable | For Meridian's Viena trial, which body convened and which two May starts conflict? | both | observation, coordination, Lisbon | PASS |
| typo-merdian-answerable | Who organized Merdian's Vienna pilot, and did it start on 14 or 16 May 1987? | both | observation, coordination, Lisbon | PASS |
| context-absent-badge | What badge color did Project Meridian use at its Vienna pilot? | both, no synthesis claim | coordination, Lisbon, observation | PASS |
| context-absent-insurer | Which insurer issued coverage for Meridian's Vienna demonstration? | both, no synthesis claim | coordination, Lisbon, observation | PASS |

Fresh query result: **23/24 passed; one failure**. All 42 returned evidence chunks round-tripped to their exact source offsets. The complete fresh result serialization was byte-identical across two executions, with SHA-256 `1ca7de761cbd2c10c03ec9da0a77b6f18235daef825b501ad7e36e150e9d2723`.

## Dedicated ordering and offset probes

An equal-score two-document corpus was supplied in reverse lexical order (`zeta-source`, then `alpha-source`). Both executions returned `alpha-source`, `zeta-source`; all offsets round-tripped. This directly exercises the documented document-ID tie-break, not just repeated execution of unequal scores.

A whitespace-bearing long document was queried with `max_chunk_chars=260` and `overlap_chars=60`. Four returned chunks had ranges `[3,257]`, `[1368,1619]`, `[2925,2998]`, and `[2730,2984]`. Every `body_text[start:end]` equaled emitted `text`, and the two complete serialized outputs were byte-identical with SHA-256 `dfcc4f9635057cdd54eee589ea402fd6ad6458b43af8b9db8f8e7a5d96c9ee47`.

## Broader execution

Commands and results:

```bash
PYTHONPATH=. .venv/bin/python -m pytest -q
# 50 passed, 1 Starlette/httpx deprecation warning in 6.32s

node --check web/app.js
# exit 0, no output
```

## Diff and generalization judgment

Command:

```bash
git diff --find-renames eef0942 19e4c347c9fe6f5e6d67bc8b8b1ae33fdd43df2f -- crest_app/retrieval.py tests evaluation/evidence_retrieval_set_v11.json
```

The production change is mechanism-oriented rather than a literal fixture lookup: it adds generic subject-head vocabulary, structural subject extraction, surface-token identity checks, named-anchor admission, and iterative stemming. A zero-context grep of added production lines found none of `Meridian`, `Borealis`, `Vienna`, `Horizon`, `Harbor`, or `Eastbridge`. That is evidence against direct string memorization.

It is nevertheless incomplete and therefore not generalizable enough to ship. The function docstring claims the grammar handles structural relations, and `under` was added to `STOP_WORDS`, but the relation loop only handles literal `for` and `associated`/`affiliated`/`connected`/`linked with`. The runtime diagnostic was:

```text
under_external       ['vienna']
for_external         ['cinder']
associated_external  ['cinder']
```

Because `Borealis` is never extracted for the `under` form, exact Vienna/event/function matches admit Meridian evidence. This is not an anecdotal ranking miss; it is a missing structural-relation branch that applies to arbitrary external subjects.

## Limits

- The corpus and frozen fixtures are synthetic and small; this sign-off makes no human-gold, real-world recall, multilingual, or semantic-answer-quality claim.
- The contextual absent-detail probes grade retrieval routing only. Whether a downstream LLM correctly labels the result partial/insufficient was outside this ranker-only decision.
- Typo coverage is two held-out spellings, not an exhaustive edit-distance study.
- Determinism was checked within one environment and process stack, not across Python versions or platforms.
- Passing the broad suite does not cover the demonstrated `under <external subject>` admission class.

## Rejection and required repair

Do not ship `19e4c347c9fe6f5e6d67bc8b8b1ae33fdd43df2f`. Repair structural subject extraction so `under X` establishes the same subject requirement as the intended identity relations, add the exact failure as a frozen regression only after the mechanism is chosen, and obtain another independent held-out sign-off. The next verifier should vary relation words and placement rather than merely restating this sentence.
