# cap3_linear_directPlus

**Claim:** A model trained on a harder task generalizes down to an easier one, competing
respectably against native models.

## Setup

Cap3 world, three contestants:
- `cap3_acc70` / `acc80` — native cap3
- `cap4_acc80` — over-spec: trained on cap4, tested on cap3

## What to look at

The cap4 model places 3rd (deficit 0.057) behind the native cap3 models (0.010, 0.029).
The gap is small. The cap4 model's representation of cap3 states is not as tight as the
native model's, because its internal geometry had to accommodate a 4th state — but the
cap3 dynamics are fully within its range.

The interesting wiring: cap4's best cap3 assignment is reverse-canonical (DEC→INC, C0→C2,
C1→C1, C2→C0), which the brute-force search finds at deficit 0.057. The canonical assignment
appears at 0.240 — the model's internal geometry is mirrored relative to cap3 canonical but
not scrambled.

## Connection to the paper

Wiring is not identity — a cap4 model wired to a cap3 world is a valid participant. The
matching process does not require the model to have been designed for this world. Productive
wiring is sufficient. This is the "no pre-established correspondence" property of the
architecture: the model brings a prediction surface, the world brings a token stream, and
the matcher finds whether a profitable connection exists.
