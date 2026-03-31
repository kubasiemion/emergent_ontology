#!/usr/bin/env python3
"""
pretrain_resolver.py

Pre-train a DirichletResolver against a deterministic world + fixed embedder.
The resolver learns to partition the embedding space into stable prototypes.

Output: resolver_pretrained.pt
"""

from .world_state_machine import WorldStateMachine
from .embedder import EventEmbedder
from .dirichlet_resolver import DirichletResolver

# --- configuration ------------------------------------------------------------

NUM_STEPS      = 500
NUM_CATEGORIES = 1
MAX_COUNT      = 4
EMBED_DIM      = 16
SEED           = 42
P_READ         = 0.3
THRESHOLD      = 0.3
LR             = 0.1
DEVICE         = "cpu"

EMBEDDER_PATH  = "embedder_state.pt"
RESOLVER_PATH  = "resolver_pretrained.pt"


def main():
    world = WorldStateMachine(
        num_categories=NUM_CATEGORIES,
        max_count=MAX_COUNT,
        device=DEVICE,
        p_read=P_READ,
        seed=SEED,
        initial_state=0,
    )

    embedder = EventEmbedder.load(EMBEDDER_PATH, device=DEVICE)
    embedder.enable_noise(False)

    resolver = DirichletResolver(
        embed_dim=EMBED_DIM,
        threshold=THRESHOLD,
        lr=LR,
        device=DEVICE,
    )

    for step in range(NUM_STEPS):
        event_name, category, _, state = world.random_event()
        count_value = int(state[category].item())

        x = embedder(event_name, category, count_value)
        embedding, meta = resolver(x, event_name=event_name, count_value=count_value)

        print(
            f"Step {step:03d}: event={event_name:<8} count={count_value}"
            f" -> proto={meta['proto_id']} dist={meta['proto_dist']:.3f}"
            f" label={meta['proto_label']!r} new={meta['is_new']}"
        )

    resolver.save(RESOLVER_PATH)
    print(f"\nResolver saved to {RESOLVER_PATH}")

    print("\nLearned prototypes:")
    for proto_id, label in resolver.list_prototypes():
        print(f"  [{proto_id}] {label}")

    print(f"\nMin prototype distance: {resolver.min_prototype_distance():.4f}")
    resolver.print_prototype_distances()


if __name__ == "__main__":
    main()
