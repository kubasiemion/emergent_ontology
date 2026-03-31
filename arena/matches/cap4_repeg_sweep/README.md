# cap4_repeg_sweep

> **STATUS: FOOTNOTE** — diagnostic result, not a main narrative piece.

Tests `repeg_alpha` = 0, 0.1, 0.2, 0.5 on the cap4_acc80 model after retraining with
curriculum + GRU bypass.

**Finding**: repeg strictly hurts. With clean training, best deficit is 0.052 at alpha=0;
it degrades monotonically to 3.25 at alpha=0.5. Repeg was calibrated as a corrective tool
for models with scrambled internal representations. When the representation is clean the
model finds the right hidden state on its own — repeg displaces it.

This inverts the pre-curriculum result where repeg=0.5 gave deficit 4.17 vs 6.36 at 0.0.
