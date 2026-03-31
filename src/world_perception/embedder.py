# world_perception/embedder.py

import os
import torch
import torch.nn as nn
import torch.nn.functional as F


class EventEmbedder(nn.Module):
    """
    Maps world events (increase, decrease, read) + category + count
    to a normalized embedding vector.

    For read events:    embedding is driven by count_value (category ignored).
    For change events:  embedding is driven by event type + category (count ignored).

    Optional Gaussian noise for training/exploration.
    """

    def __init__(
        self,
        num_categories=1,
        max_count=4,
        embed_dim=16,
        noise_std=0.05,
        noise_enabled=True,
        device="cpu",
    ):
        super().__init__()
        self.device = device
        self.noise_std = noise_std
        self.noise_enabled = noise_enabled

        self.event2id = {"increase": 0, "decrease": 1, "read": 2}

        self.event_embedding    = nn.Embedding(len(self.event2id), embed_dim)
        self.category_embedding = nn.Embedding(num_categories, embed_dim)
        self.count_embedding    = nn.Embedding(max_count, embed_dim)  # max_count is exclusive upper bound
        self.fuser              = nn.Linear(embed_dim * 2, embed_dim)

        self.to(self.device)

    def forward(self, event_name: str, category: int, count_value: int) -> torch.Tensor:
        """Returns a normalized 1-D embedding tensor."""
        if event_name == "read":
            cnt_emb = self.count_embedding(
                torch.tensor(count_value, dtype=torch.long, device=self.device)
            )
            base = torch.cat([cnt_emb, cnt_emb], dim=-1)
        else:
            e_emb = self.event_embedding(
                torch.tensor(self.event2id[event_name], dtype=torch.long, device=self.device)
            )
            c_emb = self.category_embedding(
                torch.tensor(category, dtype=torch.long, device=self.device)
            )
            base = torch.cat([e_emb, c_emb], dim=-1)

        x = self.fuser(base)

        if self.noise_enabled:
            x = x + torch.randn_like(x) * self.noise_std

        return F.normalize(x, dim=-1)

    def enable_noise(self, enable: bool = True, std: float = None):
        self.noise_enabled = enable
        if std is not None:
            self.noise_std = std

    # --- I/O ------------------------------------------------------------------

    def _config(self):
        return {
            "num_categories": self.category_embedding.num_embeddings,
            "max_count":      self.count_embedding.num_embeddings,
            "embed_dim":      self.fuser.out_features,
            "noise_std":      self.noise_std,
            "noise_enabled":  self.noise_enabled,
            "device":         self.device,
        }

    def save(self, path: str):
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        torch.save({"config": self._config(), "state_dict": self.state_dict()}, path)

    @classmethod
    def load(cls, path: str, device: str = "cpu") -> "EventEmbedder":
        checkpoint = torch.load(path, map_location=device)
        cfg = {**checkpoint["config"], "device": device}
        embedder = cls(**cfg)
        embedder.load_state_dict(checkpoint["state_dict"])
        return embedder

    # --- diagnostics ----------------------------------------------------------

    def min_pairwise_distance(self) -> float:
        """
        Minimum Euclidean distance between all embeddings produced by forward,
        evaluated deterministically (noise disabled).
        Useful for checking embedding separation after initialization.
        """
        was_enabled = self.noise_enabled
        self.noise_enabled = False
        self.eval()

        with torch.no_grad():
            vecs = []
            for event_name in self.event2id:
                for cat in range(self.category_embedding.num_embeddings):
                    if event_name == "read":
                        for cnt in range(self.count_embedding.num_embeddings):
                            vecs.append(self.forward(event_name, cat, cnt))
                    else:
                        vecs.append(self.forward(event_name, cat, 0))

            vecs = torch.stack(vecs)
            dist = (vecs.unsqueeze(1) - vecs.unsqueeze(0)).norm(dim=-1)
            dist.fill_diagonal_(float("inf"))

        self.noise_enabled = was_enabled
        return dist.min().item()