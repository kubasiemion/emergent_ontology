# cap5_retention_sweep

**Claim:** The cliff pruning strategy is the minimum retention policy that preserves
the correct answer through all three stages. Fixed thresholds fail in one of two
directions: too strict eliminates the eventual winner before the decisive stage;
greedy single-path search locks onto a local optimum that cannot be extended correctly.

## Setup

Same three cap5 models and cap3→cap4→cap5 three-stage incremental wiring as
`cap5_incremental`.  Four pruning policies are applied at each intermediate stage
(cap3→cap4, cap4→cap5).  Stage-1 scores are computed once and shared; only the
pruning decisions differ per policy.

| Policy | Strategy | Key parameter |
|---|---|---|
| threshold=0.05 | fixed threshold | keep deficit ≤ 0.05 |
| cliff (current) | largest-gap cut | gap ≥ 0.1, min 1 contender |
| threshold=2.0 | fixed threshold | keep deficit ≤ 2.0 |
| topk=1 | greedy single path | keep exactly 1 contender |

## What to look at

**Summary: native acc80 survives to the final under all policies except one**

| Policy | cap3 native | cap3 ghost | cap4 native | cap4 ghost | Final winner | Deficit |
|---|---|---|---|---|---|---|
| threshold=0.05 | 2 | 2 | **0** | 1 | ghost | 2.8887 |
| cliff (current) | 2 | 6 | 2 | 12 | **native** | 0.0391 |
| threshold=2.0 | 3 | 8 | 4 | 4 | **native** | 0.0391 |
| topk=1 | 1 | 0 | 1 | 0 | native† | 18.4069 |

†topk=1 nominally finds the native model but with the wrong canonical wiring — deficit 18.4069
vs 0.0391 for the correct wiring.  The search is compromised even though the model identity
happens to be correct.

**threshold=0.05 (too strict) — wrong answer.**  Five contenders enter stage 2.
Ghost's canonical wiring scores 0.0166 (< 0.05) and survives; native acc80's best
extension scores 0.5457 (> 0.05) and is eliminated.  Only the ghost proceeds to stage 3.
Ghost "wins" with deficit 2.8887 — the actual winner never got a chance to compete.

**cliff (current) — correct answer.**  The cliff detector scans the full stage-2 distribution
and finds that the largest gap is in the right tail (≥ 4.5), not at the ghost/native boundary
(gap = 0.5291 between ghost 0.0166 and native 0.5457).  Both native acc80 contenders survive
as a minority in stage 2 (2 of 14).  At stage 3 native wins 0.0391 vs ghost 2.8887.

**threshold=2.0 (lenient) — correct but expensive.**  Carries far more contenders
(18 at cap3, 8 at cap4) including ghost deadweight.  Correct final ranking (0.0391),
but the search is less focused.

**topk=1 (greedy) — wrong wiring.**  Keeps only the single best stage-1 contender:
native acc80 with the reverse-canonical wiring (DEC↔INC, C0↔C2), deficit 0.0096.
This is optimal at stage 1 but the wrong path for stages 2–3.  The wiring that works
best on a cap3 world need not extend cleanly to cap4 and cap5.  Final deficit 18.4069 —
catastrophic.  Even correct model identity is an accident here; the correct wiring
(deficit 0.0391) was never evaluated because it was eliminated at stage 1.

## The necessary condition

The cliff strategy is necessary because:
1. Fixed low thresholds prune models whose scores are temporarily high at an
   intermediate stage but who will win the final.
2. Greedy single-path search commits to a local optimum that cannot be corrected.

The minimum retention policy is one that preserves the **distributional shape** of the
contender pool, not a fixed score floor.  The cliff finds natural breakpoints — places
where the deficit distribution has a genuine discontinuity — and cuts there.  At stage 2,
the genuine discontinuity is in the ghost's own right tail (bad ghost wirings collapsing
after C4 is assigned), not at the ghost/native boundary.

The contender set is the hedge.  A policy that eliminates all minority-model contenders
at an intermediate stage is gambling that the intermediate leader is also the final leader.
Here — as in cap4_succession — that bet is wrong.

## Connection to the paper

This match makes the retention policy claim precise: the cliff strategy succeeds
not because it is lenient but because it cuts at the right place.  The ghost/native
gap at stage 2 (0.53) looks like a cliff, but it is not the largest cliff.  A fixed
threshold set to 0.1 would reach the same wrong conclusion as threshold=0.05.  Only
a strategy that adapts to the score distribution can reliably preserve the eventual
winner through intermediate stages where it is temporarily behind.
