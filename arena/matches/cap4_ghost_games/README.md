# cap4_ghost_games

**Claim:** A model's wiring cannot be extended beyond its training boundary. When the world
expands past that boundary, the incumbent model must be replaced — not patched.

## Setup

Three contestants on a cap4 world (states 0–3):
- `cap4_acc80` — fully trained to cap4
- `cap4_ghost` — **ghost**: cap4 architecture, trained only to cap3
- `symbolic_cap4` — oracle reference

## What to look at

The fully-trained cap4 model scores **deficit = 0.040** with canonical wiring. The ghost scores
**6.36** — best wiring is incoherent, canonical wiring (if forced) scores even worse at 7.07.

The ghost has no representation of C3. Its pred_head and count_head weights for index 3 received
zero gradient throughout training. When the world emits C3 events the ghost's predictions are
noise, and no relabeling of the token space recovers a useful signal.

Contrast with cap3_ghost_games: the same ghost model, on its home world, scores 0.000.
The capacity was always there. What was missing was training.

## Connection to the paper

This is the succession trigger: when prediction error on the new world token exceeds any wiring's
ability to compensate, the architecture must retire the incumbent and promote a model that covers
the expanded world. The ghost's failure is unambiguous — it is not a wiring problem, it is a
capacity problem. The system can inspect this distinction architecturally.
