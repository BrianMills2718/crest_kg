# Judge tier comparison — a stronger model does not help

**Date:** 2026-08-21
**Decision:** keep `fast_cheap_mid`. Do not raise the judge tier.

## What was tested

The v18 sign-off and the real-corpus validation both concluded that the
remaining errors were judge quality and that "the next lever is a stronger judge
tier". That recommendation was wrong, and this records the measurement that
overturned it.

All three tiers were scored on the same 20 real-corpus probes, same prompt, same
`reasoning_effort="high"`, same embeddings and chunking. Only the judge model
changed.

## Result

| judge tier | model | ranking recall | recall after gate | abstains when answer absent | balanced |
|---|---|---|---|---|---|
| **`fast_cheap_mid`** | deepseek-v4-flash | 85% | 70% | **85%** | **77.5%** |
| `fast_mid` | gpt-5.6-luna | 85% | **75%** | 60% | 67.5% |
| `fast_intelligent` | glm-5.2 | 85% | 70% | 75% | 72.5% |

Counted per probe rather than as rates:

| tier | leaks (failed to abstain) | over-abstains | fully correct |
|---|---|---|---|
| `fast_cheap_mid` | **3** | 3 | **11** |
| `fast_mid` | 8 | 2 | 10 |
| `fast_intelligent` | 5 | 3 | 11 |

## What it means

The tiers trade recall against abstention rather than improving both. The
stronger models are more willing to answer, which is precisely the wrong
disposition for an abstention gate: `fast_mid` buys one extra recalled document
and pays with five extra fabrications. No tier improves the joint count of
probes that are right on both axes — 11, 10, 11 — so the differences are a
disposition shift, not a capability gain.

The cheapest model is also the best one here, and it is best on the axis that
matters most for an evidence workbench.

## Caveats

20 probes: one probe is five percentage points. `fast_mid`'s 25-point abstention
drop is five probes and is a real signal; `fast_intelligent`'s 10-point drop is
two probes and is weak. The safe reading is that a stronger tier is **not** an
improvement, not that it is precisely this much worse.

## Where the recall gap actually is

Post-gate recall stays at 70% across all three tiers while ranking recall stays
at 85%, so the same three documents are dropped regardless of judge. That
consistency points at the prompt or at the multi-part-question framing rather
than at model capability — which is where the next attempt should go, if the
15-point recall cost is judged worth attacking at all.
