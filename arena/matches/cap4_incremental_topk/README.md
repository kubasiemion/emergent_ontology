# cap4_incremental_topk

**Claim:** Premature commitment to a stage-1 wiring corrupts the stage-2 extension.
Holding all semantically coherent stage-1 bases as contenders — and selecting globally
after stage 2 — recovers the optimal result.

## Setup

Three cap4 models on a two-stage cap3→cap4 incremental match with cliff-pruned pooled
contender selection:
- `cap4_acc70/acc80` — native cap4 models
- `cap4_ghost` — ghost: cap4 architecture, cap3 training, C3 empty

Contenders are selected by cliff detection on the *pooled* stage-1 deficit distribution:
all wirings from all models are ranked together; the largest gap in the distribution is
the cut point. No threshold parameter required — the semantic gap declares itself.

## What to look at

**Contender counts:** ghost 2, acc80 4, acc70 8 — the total 14 pass the cliff. The cliff
fires at the gap between deficit 0.677 and the next cluster. Everything above is already
incoherent on the cap3 world; nothing above can extend well.

**Stage-2 winner:** acc80, deficit 0.040, from its *rank-4* stage-1 base (0.380), not its
rank-1 (0.058). The best stage-1 base is not the right foundation for the cap4 world.
The correct cap4 wiring requires a stage-1 base that keeps INC↔INC and C0→C0; acc80's
rank-1 base has INC↔DEC and can't be extended coherently. Only by holding all four
contenders does the right base reach stage 2.

**Ghost:** still fails regardless — its C3 slot is empty by construction, not by commitment.

## Connection to the paper

The matcher is operating in a world that hasn't expanded yet. From inside stage 1, all
contenders look equally valid — the current-world deficit is the only signal available.
The contender count is not just a computational parameter; it is a measure of the matcher's
epistemic humility about which wiring will generalise when the world grows.

Cliff pruning is justified because the wirings above the cliff are already semantically
incoherent on the current world — they have no prospect of extending. The wirings below
the cliff all have some claim to correctness; which survives into the expanded world can
only be determined after the expansion.
