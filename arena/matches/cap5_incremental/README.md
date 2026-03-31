# cap5_incremental

**Claim:** The ghost principle has a precise training boundary. A cap5 ghost (trained only
to cap4) is competitive through two stages of incremental wiring — cap3 and cap4 — and
fails exactly at stage 3, when the world requires C4. The training boundary, not the
architectural boundary, is where succession occurs.

## Setup

Three cap5 models (n_tokens=7) on a three-stage cap3→cap4→cap5 incremental match:
- `cap5_acc70/acc80` — native: fully trained cap5
- `cap5_cap4trained_acc80` — **ghost**: cap5 architecture, curriculum stopped at
  cap4, C4 receives zero gradient throughout

Cliff pruning is applied after each intermediate stage on the pooled cross-model deficit
distribution. The final stage is uncut — globally ranked.

## What to look at

**Stage 1 (cap3 world):** ghost 6 contenders, acc80 2, acc70 1. The ghost has excess
architectural capacity (7 tokens, 5 needed) and knows cap3 well — it produces more valid
low-deficit wirings than the native models.

**Stage 2 (cap4 world):** ghost expands to 12 contenders, acc80 holds at 2. The ghost
was trained to cap4 — it extends cleanly. Its stage-2 deficit for the canonical wiring is
0.017, the best result in the field. The challenger is barely represented.

**Stage 3 (cap5 world, final):** the crossing. Ghost's best extension is deficit 2.889
— C4 is empty, the slot carries no information. acc80's canonical wiring scores 0.039.

The ghost leads after stage 1. The ghost still leads after stage 2. The ghost collapses
at stage 3. The training boundary is where the world outruns the model, and the three-
stage structure makes that boundary visible at the exact cap where it falls.

## Connection to the paper

Pair with `cap4_succession` (two-stage, cap3→cap4 boundary) to show the same structure
at two scales and two depth levels. In `cap4_succession` the ghost falls at stage 2. Here
it survives stage 2 because its training covered cap4 — it falls at stage 3.

The number of stages the ghost survives is determined entirely by how far its curriculum
reached. The architecture is irrelevant. A cap10 model trained only to cap4 would fail
at the same stage-3 cliff.

The three-stage contender structure also demonstrates the epistemic point directly: after
stage 2, 12 ghost contenders and 2 native contenders proceed. From inside stage 2, the
ghost looks like the dominant model. Only the cap5 world expansion resolves the ambiguity.
The contender set is the hedge against a world change that hasn't happened yet.
