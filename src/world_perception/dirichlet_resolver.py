# world_perception/dirichlet_resolver.py

import os
import torch
import torch.nn as nn
import torch.nn.functional as F
from collections import deque


class DirichletResolver(nn.Module):
    """
    Nonparametric prototype resolver.

    Maintains a dynamic list of normalized prototype embeddings.
    On each call:
      - if input is closer than threshold to an existing prototype: update it (soft move)
      - otherwise: create a new prototype

    forward() returns:
      - embedding  : the fired (or newly created) prototype tensor [D], CPU, normalized
      - metadata   : dict with diagnostic information (proto_id, proto_dist, proto_label, is_new)

    Downstream always receives a prototype, never a raw embedding.
    """

    def __init__(self, embed_dim=16, threshold=0.7, lr=0.01, device="cpu"):
        super().__init__()
        self.device = device
        self.embed_dim = embed_dim
        self.threshold = threshold
        self.lr = lr
        self.labels = []

        self.prototypes = nn.Parameter(torch.empty(0, embed_dim), requires_grad=False)
        self.recent_squeezes = deque(maxlen=500)
        self.current_max_squeeze = 0.0

    # --- core -----------------------------------------------------------------

    def forward(self, x: torch.Tensor, event_name: str = None, count_value: int = None):
        """
        Resolve input embedding x to a prototype.

        Returns:
            embedding : torch.Tensor [D]  - the fired prototype (normalized, CPU)
            metadata  : dict              - proto_id, proto_dist, proto_label, is_new
        """
        if x.dim() == 1:
            x = x.unsqueeze(0)
        x = F.normalize(x, dim=-1)

        if self.prototypes.shape[0] == 0:
            return self._create_prototype(x, event_name, count_value, d_min=0.0)

        protos = F.normalize(self.prototypes, dim=-1)
        d2 = ((x - protos) ** 2).sum(dim=-1)  # (K,)
        d_min, k = torch.min(d2, dim=0)
        squeeze = d_min.item()

        self.recent_squeezes.append(squeeze)
        self.current_max_squeeze = max(self.recent_squeezes)

        if squeeze > self.threshold:
            return self._create_prototype(x, event_name, count_value, d_min=squeeze)

        return self._update_prototype(k.item(), x, event_name, count_value, d_min=squeeze)

    def _create_prototype(self, x, event_name, count_value, d_min):
        with torch.no_grad():
            new_proto = F.normalize(x.clone(), dim=-1)
            self.prototypes = nn.Parameter(
                torch.cat([self.prototypes, new_proto], dim=0),
                requires_grad=False,
            )
        proto_id = self.prototypes.shape[0] - 1
        self._set_label(proto_id, event_name, count_value)

        embedding = self.prototypes[proto_id].detach().cpu().clone()
        metadata = {
            "proto_id":    proto_id,
            "proto_dist":  float(d_min),
            "proto_label": self.labels[proto_id],
            "is_new":      True,
        }
        return embedding, metadata

    def _update_prototype(self, k, x, event_name, count_value, d_min):
        with torch.no_grad():
            current = self.prototypes[k]
            updated = F.normalize(current + self.lr * (x.squeeze(0) - current), dim=-1)
            self.prototypes[k].copy_(updated)
        self._set_label(k, event_name, count_value)

        embedding = self.prototypes[k].detach().cpu().clone()
        metadata = {
            "proto_id":    k,
            "proto_dist":  float(d_min),
            "proto_label": self.labels[k],
            "is_new":      False,
        }
        return embedding, metadata

    def _set_label(self, k, event_name, count_value):
        label = f"read({count_value})" if event_name == "read" else (event_name or "?")
        while len(self.labels) <= k:
            self.labels.append("?")
        self.labels[k] = label

    # --- I/O ------------------------------------------------------------------

    def save(self, path: str):
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        torch.save({
            "prototypes": self.prototypes.detach().cpu().clone(),
            "labels":     list(self.labels),
            "threshold":  self.threshold,
            "lr":         self.lr,
            "embed_dim":  self.embed_dim,
        }, path)

    @classmethod
    def load(cls, path: str, device: str = "cpu") -> "DirichletResolver":
        state = torch.load(path, map_location=device)
        resolver = cls(
            embed_dim=state["embed_dim"],
            threshold=state["threshold"],
            lr=state["lr"],
            device=device,
        )
        with torch.no_grad():
            resolver.prototypes = nn.Parameter(
                state["prototypes"].to(device).clone(), requires_grad=False
            )
        resolver.labels = list(state["labels"])
        return resolver

    # --- runtime controls -----------------------------------------------------

    def set_threshold(self, t: float):
        self.threshold = float(t)

    def set_lr(self, lr: float):
        self.lr = float(lr)

    # --- diagnostics ----------------------------------------------------------

    def list_prototypes(self):
        return [(i, self.labels[i] if i < len(self.labels) else "?")
                for i in range(self.prototypes.shape[0])]

    def min_prototype_distance(self) -> float:
        if self.prototypes.shape[0] < 2:
            return 0.0
        dists = torch.cdist(self.prototypes, self.prototypes, p=2)
        dists.fill_diagonal_(float("inf"))
        return dists.min().item()

    def prototype_distance_matrix(self):
        """Lower-triangular matrix of pairwise Euclidean distances."""
        K = self.prototypes.shape[0]
        if K == 0:
            return None
        protos = F.normalize(self.prototypes, dim=-1)
        d = torch.cdist(protos, protos, p=2)
        return [[float(d[i, j].item()) for j in range(i + 1)] for i in range(K)]

    def print_prototype_distances(self):
        matrix = self.prototype_distance_matrix()
        if matrix is None:
            print("No prototypes yet.")
            return
        print("\nPrototype distance matrix (lower triangle):")
        for i, row in enumerate(matrix):
            print(f"  proto {i}: " + "  ".join(f"{v:.4f}" for v in row))

    def merge_prototypes(self, i: int, j: int):
        """
        Merge prototype j into i (normalized average), remove j.
        Indices above j shift down by 1.
        """
        K = self.prototypes.shape[0]
        if not (0 <= i < K and 0 <= j < K and i != j):
            raise IndexError("invalid prototype indices for merge")
        with torch.no_grad():
            merged = F.normalize(
                (self.prototypes[i] + self.prototypes[j]) / 2.0, dim=-1
            )
            self.prototypes[i].copy_(merged)
            mask = [idx for idx in range(K) if idx != j]
            self.prototypes = nn.Parameter(
                self.prototypes[mask].clone(), requires_grad=False
            )
        if j < len(self.labels):
            self.labels.pop(j)
        while len(self.labels) < self.prototypes.shape[0]:
            self.labels.append("?")