# Wynn's World

Companion repository for two inter-related papers:

- **[Architecture paper]** *A Cognitive Architecture That Produces Teleosemantic Content as Fossilized Wiring Between Independent Perception and Prediction Systems* — [link to be added]
- **[Companion paper]** *Wynn's World: The Cognitive Architecture at Work in a Minimal Counting Scenario* — [link to be added]

All experiments in the companion paper are reproducible from this repository. Results run in under a minute on CPU.

## Quickstart

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/kubasiemion/emergent_ontology/blob/master/wynns_world.ipynb)

The notebook `wynns_world.ipynb` reproduces every exhibit in the companion paper, in section order. No setup required beyond running the first cell.

## Local setup

Requires Python ≥ 3.10, PyTorch ≥ 2.0, NumPy ≥ 1.24. No GPU required.

```
pip install -e .
```

Then run any match directly:

```
python arena/run_match.py arena/matches/cap4_ghost_games
```

Or run the notebook in Jupyter.

## Structure

```
emergent_ontology/
  arena/
    run_match.py          — match runner
    probe_wiring.py       — score individual wirings without re-running a full match
    matches/              — one directory per experiment
      cap4_ghost_games/
        config.json       — match parameters
        results.json      — raw results
        results.md        — human-readable summary
      ...
  models/
    pretrained/           — one directory per model
      cap4_acc80/
        weights.pt        — trained weights
        train.py          — training script
      ...
  papers/
    architecture_preprint_v6b.pdf
    companion_paper_v4.pdf
    architecture_diagram_v2.pdf
    *.tex                 — LaTeX sources
  src/
    models/               — BoxedCounter, SymbolicCounter
    matcher/              — brute-force wiring search
    world_perception/     — perception pipeline
    sequences.py          — sequence generation
  wynns_world.ipynb       — reproduces all paper exhibits
```

## Models

All neural models are `BoxedCounter`: a GRU-based recurrent network (emb dim 8, hidden dim 16) pre-trained on token sequences from its training world. Token vocabulary: `INC`, `DEC`, `C0`…`C_{n-1}` — total `n_counts + 2` tokens.

| Model | n_counts | Training | Accuracy |
|---|---|---|---|
| cap3_acc70 | 3 | Full cap3 curriculum | ~70% |
| cap3_acc80 | 3 | Full cap3 curriculum | ~80% |
| cap3_acc90 | 3 | Full cap3 curriculum | ~90% |
| cap4_acc70 | 4 | Full cap4 curriculum | ~70% |
| cap4_acc80 | 4 | Full cap4 curriculum | ~80% |
| cap4_ghost | 4 | Cap3 curriculum only | ~80% on cap3 |
| cap5_acc70 | 5 | Full cap5 curriculum | ~70% |
| cap5_acc80 | 5 | Full cap5 curriculum | ~80% |
| cap5_cap4trained_acc80 | 5 | Cap4 curriculum only | ~80% on cap4 |
| mod5_counter_acc80 | 5 | Modular counter variant | ~80% |
| symbolic_cap4 | 4 | By construction | 100% |

## Citation

```
[citation placeholder — to be added upon publication]
```
