# cap3_acc80

GRU-based BoxedCounter trained to track a linear (non-wrapping) count in [0, 2].
Saved at first epoch where read-position accuracy ≥ 80% holds for 2 consecutive epochs.

## Config

| Parameter | Value |
|-----------|-------|
| `n_counts` | 3 (states: 0–2) |
| `emb_dim` | 8 |
| `hidden_dim` | 16 |
| `n_seqs` | 2000 |
| `seq_len` | 100 |
| `p_read` | 0.3 |
| `lr` | 1e-3 |
| `seed` | 0 |
| `target_acc` | 0.80 |
| `consecutive_req` | 2 |

## Loading

```python
from demos.wynns_world.src.models.boxed_counter import BoxedCounter

model = BoxedCounter.load("demos/wynns_world/models/pretrained/cap3_acc80/weights.pt")
```

## Reproducing

```bash
python demos/wynns_world/models/pretrained/cap3_acc80/train.py
```
