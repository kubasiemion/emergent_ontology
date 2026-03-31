# cap4_succession_scorers

**Claim:** The succession rank crossing — ghost leads stage 1, native leads stage 2 — is robust
to the choice of scoring function.

## Setup

Same models and sequences as `cap4_succession`, incremental wiring (cap3 → cap4), scored under
deficit, tiered, and cross_entropy.

## What to look at

Stage-1 and stage-2 leaders across scorers:

| Scorer | Stage-1 winner | Stage-1 deficit | Stage-2 winner | Stage-2 deficit |
|---|---|---|---|---|
| deficit | ghost | 0.0000 | native | 0.0400 |
| tiered | ghost | 0.0000 | native | 1.80 |
| cross_entropy | ghost | 374.0 | native | 382.1 |

The rank crossing is present in all three. The succession event is scorer-independent.

**Tiered:** Both ghost wirings (canonical and reverse-canonical) score 0.0000 at stage 1 —
both are within the eps=0.02 tolerance. This produces more stage-1 contenders than deficit,
but the stage-2 outcome is unchanged.

**Cross-entropy:** The stage-1 gap between ghost (374.0) and native (386.8) is small — the
cross-entropy baseline dominates and compresses the spread. But the stage-2 crossing is
unambiguous: native 382.1 vs ghost 537.9. The structure survives even when the scorer is
least sensitive to the home-world distinction.

## Connection to the paper

The succession event does not depend on where the deficit scorer places its threshold or how
it penalises underperformance. The crossing is in the data, not in the scoring function.
