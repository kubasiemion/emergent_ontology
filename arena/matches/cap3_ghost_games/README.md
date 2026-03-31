# cap3_ghost_games

**Claim:** A model with excess capacity, trained only up to its task boundary, outperforms
native models on that task.

## Setup

Four contestants on a cap3 world (states 0–2):
- `cap3_acc70` / `acc80` — native: architecture matches the world
- `cap4_acc80` — over-spec: cap4 architecture, fully trained to cap4
- `cap4_ghost` — **ghost**: cap4 architecture, curriculum stopped at cap3

The ghost has capacity for a 4th count state (C3) but was never trained on it — C3 is a ghost slot
with zero gradient throughout training.

## What to look at

The ghost wins with **deficit = 0.000**, beating every native model.

The explanation is geometric: native cap3 models must pack their count-state line into a space
where C2 is pressed against the representable boundary. The ghost places C2 in the interior,
with unused slack beyond it. The dynamics are less compressed, the predictions are cleaner.

The over-spec full cap4 model lands 5th (deficit 0.057) — it knows about C3 and its
representation reflects that, softening the C2 boundary.

## Connection to the paper

The ghost is a model whose wiring capacity exceeds the current world's requirements. Its
proto-ontology has room that the world hasn't yet claimed. This is the minimal precondition
for wiring extension to be possible at all: the model must have unoccupied capacity before
the world can expand into it.
