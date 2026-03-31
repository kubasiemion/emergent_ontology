# cap5_acc70

GRU-based BoxedCounter trained to track a linear (non-wrapping) count in [0, 4].
Saved at first epoch where read-position accuracy ≥ 70% holds for 2 consecutive epochs.

## Config

| Parameter | Value |
|-----------|-------|
| `n_counts` | 5 (states: 0–4) |
| `emb_dim` | 8 |
| `hidden_dim` | 16 |
| `n_seqs` | 2000 |
| `seq_len` | 100 |
| `p_read` | 0.3 |
| `lr` | 1e-3 |
| `seed` | 0 |
| `target_acc` | 0.70 |
| `consecutive_req` | 2 |

## Loading

```python
from demos.wynns_world.src.models.boxed_counter import BoxedCounter

model = BoxedCounter.load("demos/wynns_world/models/pretrained/cap5_acc70/weights.pt")
```

## Reproducing

```bash
python demos/wynns_world/models/pretrained/cap5_acc70/train.py
```
