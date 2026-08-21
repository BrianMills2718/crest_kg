# Real-corpus validation of the semantic ranker

**Date:** 2026-08-21
**Question:** do the sixteen frozen fixtures proxy real CREST retrieval at all?

## Why this was needed

The fixtures that justified replacing the lexical ranker are 13 synthetic
documents of about 210 characters each, authored in one night by the very loop
being replaced. The real corpus in `cia_documents/` is 40 OCR'd government
memoranda with a median length of 6,931 characters — roughly 33x longer, far
noisier, and multi-chunk per document. A result measured only on the fixtures
could not be trusted to transfer, and continuing to tune the judge against them
would have been optimising a toy.

## Protocol

No hand-authored ground truth. Each probe question is generated from one exact
passage, so the document that passage came from is by construction the document
that answers it (`evaluation/build_real_corpus_probe.py`, fixed seed 20260821).
Two runs per probe:

- **recall** — ask against the whole corpus; the source document must return.
- **abstention** — ask against the corpus with the source document removed;
  nothing else states that fact, so the correct result is to return nothing.

Ranking is scored separately from the gate, so a miss is attributable. Five of
the 25 generated questions referred to their own source ("according to this
passage") and were skipped: once the source is removed such a question has no
stable answer, so it cannot score abstention. 20 probes scored.

## Result

| on 20 real CREST probes | ranking recall @4 | abstains when the answer is absent |
|---|---|---|
| Lexical ranker, 1,059 lines | 80.0% | **10.0%** |
| Semantic ranking + gate, 326 lines | **85.0%** (70.0% after the gate) | **85.0%** |

The abstention gap is the finding. On real documents the lexical ranker returns
confident evidence for **90%** of questions the corpus cannot answer. For an
evidence workbench that is the cardinal failure: it manufactures support for
whatever it is asked. The replacement withholds correctly on 85%.

The gate costs 15 points of recall (85.0% → 70.0%) to buy 75 points of
abstention. For this product that is plainly the right trade.

## What this settles

The fixture numbers **transfer directionally**. The dominant error on the real
corpus is the same one the fixtures show — the gate over-abstains on multi-part
and heavily paraphrased questions — so "the next lever is a stronger judge tier"
is now a conclusion about real data, not about 210-character synthetic notes.

It also re-scopes the earlier held-out comparison. On the fixtures the
replacement looked marginally worse than a ranker fitted to them (19 failures vs
16); on the real corpus, against the same incumbent, it is better on both axes
at once and decisively better on abstention.

## Reproducing

```
python evaluation/build_real_corpus_probe.py --count 25   # regenerate probes
python evaluation/run_real_corpus_probe.py                # score them
python evaluation/run_real_corpus_probe.py --offline      # replay from cache
```
