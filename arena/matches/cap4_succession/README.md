# cap4_succession

**Claim:** Two models wire to the same world. One leads in the incumbent environment.
When the environment expands, the incumbent's wiring cannot be extended — the challenger
takes over. This is model succession as an inspectable architectural event.

## Setup

Two models, same cap4 world, incremental two-stage search:
- `cap4_ghost` — **ghost**: the incumbent, optimised for cap3
- `cap4_acc80` — **challenger**: trained for the full cap4 world

## What to look at

**Stage 1 (cap3 departure)**: ghost leads. It was trained exactly for this world;
its stage-1 deficit is 0.000. The challenger is competitive but not superior.

**Stage 2 (cap4 extension)**: ghost's best extension has C3 mapped to its untrained
ghost slot — deficit collapses. The challenger's extension places C3 correctly — low deficit.

The two curves cross between stage 1 and stage 2. That crossing is the succession event.

The match produces two ranked tables. Read them together: the model that wins stage 1
loses stage 2. The architecture can observe this crossing and act on it — retire the ghost,
promote the challenger, carry forward the stage-1 wiring as the new base.

## Connection to the paper

"The system distinguishes between environments that require extending existing wirings and
those that demand replacing them."

Extending requires a model with unoccupied capacity for the new token. The ghost has the
architecture but not the training. The challenger has both. The distinction is observable
from deficits alone — no privileged knowledge of the models' internals is required.

The cliff pruning makes the epistemic structure explicit: after stage 1, there is a large
gap in the pooled deficit distribution. The contenders below the cliff — 2 ghost + 4
challenger — are the only wirings with any claim to cap3 coherence. Committing to the
stage-1 winner (ghost, deficit 0.000) would foreclose the challenger's contenders
entirely. The succession event is only observable because all six contenders proceed to
stage 2.
