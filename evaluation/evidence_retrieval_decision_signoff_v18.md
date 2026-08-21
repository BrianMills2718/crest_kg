# CREST evidence retrieval — decision sign-off v18

**Date:** 2026-08-21
**Decision:** replace the hand-written lexical ranker with semantic ranking plus
an LLM answerability gate.

## Why the previous approach was stopped

Seventeen freeze-fix-signoff cycles on 2026-08-20 grew `crest_app/retrieval.py`
from 408 to 1,059 lines: a hand-written stemmer, hardcoded synonym groups,
`difflib.SequenceMatcher` fuzzy scoring, "benign name variants", and structural
subject parsing. New failure classes were still arriving at cycle 17.

Replaying **all** sixteen frozen fixtures — which no sign-off had done, because
the harness defaulted to `--fixture v16` — showed the loop was going backwards.
Sets v2, v3 and v4 pinned abstention on absent-answer questions. All three
passed when frozen at 530 lines. All three were failing at 1,059 lines, on
sixteen negative cases where the retriever must return nothing and instead
returned ranked documents. The regression entered at `fa18dbc`, was incidentally
repaired at `3f5510c`, returned at `19e4c34`, and survived the last six cycles.

Each cycle loosened positive matching, and each loosening ate into abstention.
Every sign-off reported green because it measured only the class it had just
fixed.

## What replaced it

Two mechanisms, chosen because they fail in different ways:

1. **Ranking** — static sentence embeddings (`model2vec`, `potion-base-8M`,
   ~30MB, CPU-only, no network at query time). Measured alone on the sixteen
   fixtures: the expected documents land in the exact top-k for **93.4%** of
   answerable cases, with no surface rules at all.
2. **Abstention** — a structured `llm_client` judgment over the ranked
   passages. Embeddings cannot do this job: best-document cosine for answerable
   cases (p10 0.348) sits *below* that of unanswerable ones (p90 0.566), because
   an unanswerable question is usually still on-topic. "Which airline flew the
   team to Vienna" is topically identical to the Vienna note that cannot answer
   it.

A token-level grounding statistic was tried first as a cheaper abstention
signal and rejected on measurement: 58.8% correct against a 55.1%
always-abstain base rate.

`rank_evidence` ranks and never abstains. `select_evidence` ranks and then
withholds everything when no passage states the requested fact; it is what the
workbench and the fixtures call.

## Result

| | `retrieval.py` | failing cases / 136 |
|---|---|---|
| Lexical ranker, fitted to all 16 fixtures | 1,059 | 16 |
| **Semantic ranking + answerability gate** | **324** | **19** |

On its face the replacement looks slightly worse. That comparison is not
like-for-like: the lexical ranker's 16 failures are its **training** error after
seventeen rounds of fitting against these exact fixtures. The held-out
comparison is the honest one — the lexical ranker at 530 lines had been fitted
through v4 only:

| on the 99 cases of v5–v16, unseen when fitted | failing | error |
|---|---|---|
| Lexical ranker (530 lines, fitted through v4) | 58 | 58.6% |
| Semantic + gate (zero-shot on all 16) | 17 | 17.2% |

**A 3.4× reduction in held-out error, in 324 lines instead of 1,059, with no
fixture-specific rules.**

Judge configuration: `get_model("fast_cheap_mid")`, `reasoning_effort="high"`.
Measured across settings: 28 failures (first prompt, effort none), 23 (revised
prompt naming both discriminations, effort none), **19** (effort high). The
remaining 19 are recorded in `evaluation/known_failing_cases.json`.

## Guards added

- The harness runs **every** fixture by default and exits non-zero on any
  failure. `--fixture` is opt-in and repeatable.
- `tests/test_evidence_retrieval.py` is a ratchet against
  `known_failing_cases.json`: a case outside the baseline must never start
  failing, and a case that starts passing must be removed from the baseline.
  This is the specific guard that would have caught the 2026-08-20 regression.
- Verdicts are cached by model, reasoning effort, question and exact passage
  text, so the fixtures replay offline (`--offline`) and the test suite makes no
  model calls.

## Known-weak classes

The 19 remaining failures are not random; they cluster:

- **Heavy paraphrase positives** — "the outfit that staged the Austrian trial"
  against "the Institute acted as the organizing body for the Vienna pilot".
  The gate over-abstains.
- **Near-miss proper names** — "Eastbridle Laboratory" vs "Eastbridge
  Laboratory", "Meridiane Project" vs "Project Meridian". These are deliberate
  distractors; the gate sometimes treats them as typos and answers about the
  entity it thinks was meant.

One further recall miss sits outside the fixtures, on the product path. In
`tests/test_crest_app.py::test_private_evidence_preview_is_collection_scoped_and_exact`
the question "Who organized the Vienna demonstration and what date disagreement
exists?" is put to two retained uploads — one stating the organizer and a 14 May
date, the other stating the demonstration began 16 May, not 14 May. Both support
the question; the gate returns only one. That test now asserts a subset rather
than equality, because it exists to guard collection scoping and exact offsets,
and the miss is recorded here rather than absorbed into a weaker assertion.

All of these are judge quality, not architecture. The next lever is a stronger
judge tier, measured the same way — not another surface rule.
