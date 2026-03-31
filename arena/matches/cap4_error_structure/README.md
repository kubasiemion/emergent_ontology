# cap4_error_structure

**Claim:** World extension and screen violation produce structurally different prediction error
patterns. World extension deficit is concentrated at the new token and its boundary; screen
violation deficit is spread across existing tokens and discriminates models on the wrong axis.

## Setup

Two models, canonical wiring (identity perm), two scenarios:

- `cap4_ghost` — **ghost**: cap4 architecture, trained only to cap3
- `cap4_acc80` — **native**: trained on the full cap4 curriculum

**Scenario A (world extension):** Models scored on cap4 sequences using the canonical cap4
wiring. The ghost has never trained on count=3; its C3 model slot is a zero-gradient ghost state.

**Scenario B (screen violation):** Models scored on cap3 sequences where 10% of count token
emissions are falsified (C_k replaced by a random C_j, j ≠ k). World dynamics are intact; only
the read signal is corrupted.

## What to look at

**Scenario A — world extension:**

Ghost deficit = 7.07, decomposed as **C2: 3.35 + C3: 3.68** (98.9% at C2/C3).
Native deficit = 0.04, all at C1.

The C3 component is direct failure: the model cannot predict C3 because it has no count=3
representation. The C2 component is the boundary effect: after the model steps through C3 (ghost
state), its hidden state is corrupted, so the immediately following C2 reads — which occur when
count transitions 3→2 via DEC — are also mis-predicted. The deficit is structured around the
new world boundary.

Discrimination gap = **7.05** (total over all token types).

**Scenario B — screen violation:**

Ghost deficit = 1.11. Native deficit = **1.69**. The native has *more* deficit than the ghost
on violated cap3 sequences.

The violation signal discriminates, but on the wrong axis: it ranks models by home-world
specialization, not by readiness for the expanded world. The ghost, trained exclusively on the
cap3 world to 80% accuracy, handles the cap3 dynamics (including violations) better than the
native, which trained through the full cap4 curriculum and has a slightly less sharp cap3
representation.

Discrimination gap = **0.83**, inverted relative to Scenario A.

## Connection to the paper

The two signals differ not just in magnitude but in direction. World extension produces a large,
structured, correctly-directed gap: native outperforms ghost because native has a trained
representation for the new state. Screen violation produces a smaller gap in the opposite
direction: ghost outperforms native because ghost specializes in the smaller world.

A succession system that acts on screen violation signal would promote the ghost — the wrong
move. Acting on world extension signal promotes the native — the right move. The presence or
absence of a new world token is not incidental; it is the mechanism that makes the signal
discriminate in the correct direction.

Violation deficit is also structurally uninformative: it is spread across C0, C1, C2 in
rough proportion to their violation rates, with no concentration at any boundary. There is no
cliff in the violation deficit landscape to trigger a succession event.

## Architecture conjecture confirmed

The ghost's zero-gradient C3 slot was expected to corrupt hidden state and cascade into
adjacent predictions. The deficit breakdown confirms this: C2 (3.35) is nearly as large as C3
(3.68), carried by steps where the model was already in a corrupted state from a prior C3
transition. The contamination is directional — it flows from the ghost boundary downward into
the last trained count state — and is absent in the native model. The architecture produces
exactly the error gradient the conjecture predicted.
