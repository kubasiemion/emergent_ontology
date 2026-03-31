# world_perception/perception_pipeline.py

from .world_state_machine import WorldStateMachine
from .embedder import EventEmbedder
from .dirichlet_resolver import DirichletResolver
from .accommodation_filter import AccommodationFilter


class PerceptionPipeline:
    """
    World -> Embedder -> Resolver.

    Emits (embedding, metadata) pairs on each step.
    Components are treated as black boxes; each handles its own I/O.
    """

    def __init__(self, world, embedder, resolver, filter_active=False):
        self.world    = world
        self.embedder = embedder
        self.resolver = resolver
        self.filter   = AccommodationFilter(active=filter_active)

    @classmethod
    def create(
        cls,
        *,
        num_categories=1,
        max_count=4,
        seed=42,
        p_read=0.3,
        initial_state=0,
        embedder_path="embedder_state.pt",
        resolver_path="resolver_pretrained.pt",
        filter_active=False,
    ):
        world = WorldStateMachine(
            num_categories=num_categories,
            max_count=max_count,
            device="cpu",
            p_read=p_read,
            seed=seed,
            initial_state=initial_state,
        )

        embedder = EventEmbedder.load(embedder_path)
        resolver = DirichletResolver.load(resolver_path)

        return cls(world, embedder, resolver, filter_active=filter_active)

    def set_filter(self, active: bool):
        """Enable or disable the accommodation filter. Resets filter state."""
        self.filter.set_active(active)

    def next_token(self):
        """
        Advance world one step and resolve to a prototype.

        When the accommodation filter is active, consecutive read tokens after
        the first are silently dropped and the world continues stepping until
        a non-read (or the first read after a non-read) is produced.

        Returns:
            embedding : torch.Tensor  - the fired prototype (1-D, CPU)
            metadata  : dict          - event_name, count, proto_id, proto_dist, proto_label
        """
        while True:
            event_name, category, _, state = self.world.random_event()
            count_value = int(state[category].item())

            if not self.filter(event_name):
                continue                        # drop; world has stepped, we loop

            raw_embedding = self.embedder(event_name, category, count_value)
            embedding, metadata = self.resolver(
                raw_embedding, event_name=event_name, count_value=count_value
            )
            metadata.update({"event_name": event_name, "count": count_value})
            return embedding, metadata

    def get_token_sequence(self, n):
        """Generate a sequence of n (embedding, metadata) pairs."""
        embeddings, metadata = [], []
        for _ in range(n):
            emb, meta = self.next_token()
            embeddings.append(emb)
            metadata.append(meta)
        return embeddings, metadata