import torch

from models.boxed_counter import BoxedCounter
from models.symbolic_counter import SymbolicCounter

_INLINE_BUILDERS = {
    "symbolic": lambda cfg: SymbolicCounter(n_counts=cfg["n_counts"]),
}


def build_model(entry: dict):
    """Construct a model directly from an inline config entry (no file needed)."""
    kind = entry.get("type")
    if kind not in _INLINE_BUILDERS:
        raise ValueError(f"Unknown inline model type: {kind!r}")
    return _INLINE_BUILDERS[kind](entry)


def load_model(path: str):
    """Load any BoxedModel-compliant model from a .pt file."""
    return BoxedCounter.load(path)
