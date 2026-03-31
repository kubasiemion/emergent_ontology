# cap4_error_structure_variants

**Claim:** The screen-violation inversion — ghost beats native under count corruption —
is not an artifact of the canonical wiring choice. It holds across the full set of
stage-1 contenders.

## Setup

Every wiring from `cap4_incremental_wiring` stage 1 (18 entries across ghost,
native acc80, and native acc70) is scored on corrupted cap3 sequences
(10% of count tokens randomly replaced).  The stage-1 deficit is shown alongside
the violation deficit so the two orderings can be compared directly.

## What to look at

**The top of the violation ranking is dominated by ghost wirings.**

| Place | Viol Def | Model | Wiring |
|---|---|---|---|
| 1 | 1.1062 | ghost | DEC INC C2 C1 C0 |
| 2 | 1.1137 | ghost | INC DEC C0 C1 C2 |
| 3 | 1.2194 | acc70 | INC DEC C1 C2 C3 |
| 4 | 1.2435 | acc70 | DEC INC C2 C1 C0 |
| 5 | 1.3079 | acc80 | DEC INC C2 C1 C0 |
| 6 | 1.4486 | acc70 | INC DEC C0 C1 C2 |
| 7 | 1.6938 | acc80 | INC DEC C0 C1 C2 |

Ghost's two best stage-1 wirings (canonical and reverse-canonical) place 1st and 2nd
at screen violation — below native acc80's canonical wiring (place 7, deficit 1.6938).
This is the inversion: the model that catastrophically fails at world extension
actually handles screen violation best.

**Stage-1 ordering is not preserved.**  Ghost's stage-1 winner (canonical, 0.0000) is
violation place 2; ghost's stage-1 runner-up (reverse-canonical, 0.0136) is violation
place 1.  The stage-1 ranking and the violation ranking are not correlated for the
well-performing wirings.

**The weird ghost wirings (places 14–18) are bad everywhere** — high stage-1 deficit
(2.6–3.1) and high violation deficit (3.5–4.0).  These are not contenders in any sense
and do not affect the inversion result.

## Connection to the paper

The error structure results in `cap4_error_structure` used only the canonical wiring.
This match confirms the inversion holds across all 18 stage-1 contenders.
Screen violation is not a useful discriminator regardless of which wiring is chosen:
the ghost's best wirings win the violation ranking, which points in the wrong direction.
