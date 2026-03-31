# cap4_incremental_wiring

**Claim:** A wiring that works for a smaller world can be extended to a larger one — if the
model has the capacity. The extension is forced: once the cap3 tokens are assigned, the cap4
token maps to the only remaining model slot.

## Setup

Three cap4 models scored in two stages:
- **Stage 1**: cap3 world (5 tokens). Find best injection of 5 world tokens into 6 model tokens.
- **Stage 2**: lock stage-1 assignment. The single remaining model token is forced onto C3.
  Score on the full cap4 world.

Models:
- `cap4_acc70` (SEED=37)
- `cap4_acc80` (SEED=42)
- `cap4_ghost` — ghost

## What to look at

**Stage 1** reveals internal representation structure:
- Ghost: 0.000, canonical (C0→C0, C1→C1, C2→C2) — trained exactly for this
- acc80: 0.058, reverse-canonical (C0→C2, C1→C1, C2→C0) — valid mirror symmetry
- acc70: 0.005, **shifted** (C0→C1, C1→C2, C2→C3) — the model internalized cap3 states
  as model tokens C1/C2/C3, not C0/C1/C2. Different random seed → different symmetry breaking.

**Stage 2** shows the cost of early commitment:
- Ghost: canonical C3 assignment, but C3 is the ghost slot → deficit 7.07 (expected)
- acc70: shift locked in → C3 forced to C0 → cyclic permutation → deficit 7.42
  (acc70's true cap4 wiring, found by direct brute-force, is 0.040 — perfectly fine)
- acc80: reverse-canonical locked → deficit 10.31

The high stage-2 deficits for acc70 and acc80 are not model failures — they are a consequence
of committing to the stage-1 best wiring before stage-2 evidence is available.

## Connection to the paper

Incremental wiring makes fossilization concrete: once C0→C1 is committed (fossilized from
stage 1), C3→C0 follows by elimination. If the stage-1 commitment was based on a locally
optimal but globally suboptimal wiring, the extension inherits the error.

The fix — try all top-k stage-1 bases before committing — is the architectural analog of
keeping ontological commitments provisional until the full evidence is in. See
`cap4_incremental_topk` for that variant.
