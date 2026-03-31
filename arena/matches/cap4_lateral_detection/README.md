# cap4_lateral_detection

**Claim:** Filtering the new world token from the evaluation stream is not sufficient to
hide that the world has expanded. The ghost fails even when C3 is removed from the
sequences — because the world extension leaks through INC/DEC dynamics at the cap3/cap4
boundary.

## Setup

Two models scored on cap4 world sequences under two observation regimes:
- `cap4_ghost` — **ghost**: trained on cap3, C3 empty
- `cap4_acc80` — **native**: trained on the full cap4 world

**Pass 1 (filtered observer):** C3 tokens are removed from the sequences before scoring.
Only INC/DEC/C0/C1/C2 events remain. The observer is unaware C3 exists.

**Pass 2 (full observer):** sequences are unfiltered; all cap4 tokens are scored.

## What to look at

**Pass 1 — filtered:** ghost deficit 3.38, native 0.040. The ghost fails even without C3.

The cap4 world dynamics cannot be concealed by removing the C3 token. When count=3
is the current world state, INC saturates at 3 (instead of 2), DEC transitions from 3
to 2 carry different probability mass, and no C2 reads occur from count=3. These
distributional shifts in the INC/DEC/C0–C2 subsequences are detectable — the ghost,
whose training stops at count=2, is betrayed by the boundary before the explicit read
token ever appears.

**Pass 2 — full:** ghost deficit 7.07, native 0.040. Forcing C3 into the wiring makes
the failure categorical, but the signal was already present in pass 1.

## Connection to the paper

Ignoring a token is not the same as being in the old world. The world state machine has
expanded, and that expansion is observable in every event type that touches the new
boundary — not just the new read token itself.

This has implications for the succession trigger: the system does not need to wait for
an explicit C3 observation to detect that its model is inadequate. The ghost's deficit
on the incumbent token vocabulary is already elevated. The new token is the confirmation,
not the first signal.

Pair with `cap4_succession`: there, the succession event is triggered by the full
incremental wiring. Here, the boundary signature is visible even to a filtered observer
that has never seen C3.
