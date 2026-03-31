# cap4_ghost_games_scorers

**Claim:** The ghost failure result and the ordinal ranking of wirings are robust to the choice
of scoring function.

## Setup

Same models and sequences as `cap4_ghost_games`, scored under three functions:

- **deficit**: `max(1/n_tokens − pred_prob[next], 0)` — hinge loss at uniform baseline
- **tiered**: stepped penalty (0 within eps, penalty at first tier, 4×penalty beyond)
- **cross_entropy**: `−log(pred_prob[next])` — standard NLL, no threshold, no floor

## What to look at

Canonical wiring rankings across scorers:

| Model | deficit | tiered | cross_entropy |
|---|---|---|---|
| symbolic_cap4 | **0.0000** | **0.0000** | 283.7 |
| native canonical | 0.0400 | 1.80 | 382.1 |
| ghost canonical | 7.0694 | 219.2 | 537.9 |

The ordinal structure is preserved. Ghost canonical ranks last in all three; native canonical
ranks first among trained models in all three.

**Cross-entropy reveals resolution that deficit compresses.** The deficit scorer clips all
above-threshold predictions to 0, making the symbolic model and a near-perfect model
indistinguishable (both 0.0). Cross-entropy shows that the symbolic model (283.7) is better
than the native (382.1) because its above-threshold predictions are also more confident.
The gap is real; deficit just cannot see it.

**Symbolic wrong wirings.** Under deficit, the symbolic model's incorrect wirings score 4.33–5.27
— modest, bounded. Under cross_entropy they score 871–998 — catastrophic. The symbolic model is
extremely confident when wrong (near-zero probability on the correct token when the wiring is
incorrect), and cross_entropy punishes this exponentially. Deficit caps the per-step contribution
at 1/n_tokens and misses the severity.

## Connection to the paper

The key claim — ghost fails, native succeeds, symbolic is ceiling — holds regardless of whether
the scorer is a hinge loss, a step function, or an unbounded log penalty. The failure is
structural, not an artifact of the deficit function's particular shape.
