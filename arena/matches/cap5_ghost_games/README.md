# cap5_ghost_games

**Claim:** The ghost principle scales. A cap5 model with C4 as a ghost state fails on a
cap5 world for the same structural reason as the cap4 ghost fails on a cap4 world.

## Setup

Three contestants on a cap5 world (states 0–4):
- `cap5_acc70` / `acc80` — native: fully trained cap5
- `cap5_cap4trained_acc80` — **ghost**: cap5 architecture, curriculum stopped at cap4;
  C4 is a ghost state (zero gradient throughout)

## What to look at

Expected pattern (mirroring cap4_ghost_games):
- Native cap5 models: low deficit, canonical or near-canonical wiring
- Ghost: high deficit, no coherent wiring — C4 is unrepresented

If the ghost result is not qualitatively worse than native, it would indicate that one
state of headroom (cap5 arch on cap5 world with cap4 training) is insufficient to explain
the ghost's failures — the deficit came from somewhere else.

## Connection to the paper

Confirms the ghost principle is not specific to the cap3/cap4 boundary. The training
boundary, not the architectural boundary, determines what can be wired. Model succession
is triggered whenever the world's token vocabulary exceeds the incumbent's training coverage,
regardless of architectural capacity.

Pair with `cap4_ghost_games` to show the same structure at two scales.
