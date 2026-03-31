# Models

Pre-trained `BoxedCounter` models. Each subdirectory contains:

```
<model_name>/
  weights.pt   — trained weights
  train.py     — training script that produced them
  README.md    — notes (where present)
```

## Naming convention

`cap{N}_acc{X}` — trained to count up to N, target accuracy X%.
`cap{N}_ghost` — cap{N+1} architecture, curriculum stopped at capN.
`cap{N}_cap{M}trained_acc{X}` — cap{N} architecture, trained only to capM.
