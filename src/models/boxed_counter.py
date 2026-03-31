# models/boxed_counter.py
#
# CPU-only by design. No device routing.

import torch
import torch.nn as nn
import torch.nn.functional as F

# Fixed token ids — structural, not configurable.
TOK_INC, TOK_DEC = 0, 1
TOK_C0 = 2       # first count token; TOK_Cn = TOK_C0 + n

EPS = 1e-12


class CounterCore(nn.Module):
    """
    GRU core with two heads (prediction, count state).

    Uses nn.GRU (not GRUCell) so the full sequence can be processed in one
    C++ call during batched training. Single-step inference wraps it as a
    [1,1,D] → [1,1,H] call; the external API is unchanged.
    """
    def __init__(self, emb_dim, hidden_dim, n_tokens):
        super().__init__()
        self.rnn        = nn.GRU(emb_dim, hidden_dim, batch_first=True)
        self.pred_head  = nn.Linear(hidden_dim, n_tokens)
        self.count_head = nn.Linear(hidden_dim, n_tokens - 2)
        self.hidden_size = hidden_dim

    def forward(self, x, h_prev):
        """Single-step: x [emb], h_prev [hidden] → h [hidden], pred, count."""
        out, h_new = self.rnn(x.unsqueeze(0).unsqueeze(0),
                              h_prev.unsqueeze(0).unsqueeze(0))
        h = h_new.squeeze()
        return h, self.pred_head(h), self.count_head(h)

    def forward_batch(self, x, h0):
        """Batched sequence: x [B,L,emb], h0 [B,hidden] → out [B,L,hidden]."""
        out, _ = self.rnn(x, h0.unsqueeze(0))
        return out


class BoxedCounter(nn.Module):
    """
    CPU-only BoxedCounter.

    Learns to track a discrete count in [0, n_counts-1] from a stream of
    INC/DEC action tokens. Predicts the current count at masked positions.

    Token vocabulary:
        INC (0), DEC (1), C0 (2) … C_{n_counts-1} (2 + n_counts - 1)
        Total: n_tokens = 2 + n_counts

    Parameters
    ----------
    n_counts : int
        Number of discrete count states.
    emb_dim : int
        Token embedding dimension.
    hidden_dim : int
        GRU hidden dimension.
    ema_alpha : float
        EMA decay for probability and count-logit statistics.
    control_gate_with_finetune : bool
        If True, gate_matrix is frozen/unfrozen together with core params
        by set_fine_tune().
    repeg_alpha : float
        Soft re-peg strength on count tokens. 0.0 = disabled.
    """

    def __init__(
        self,
        n_counts=4,
        emb_dim=8,
        hidden_dim=16,
        ema_alpha=1e-4,
        control_gate_with_finetune=True,
        repeg_alpha=0.0,
    ):
        super().__init__()
        n_tokens = 2 + n_counts

        self.n_counts   = n_counts
        self.n_tokens   = n_tokens
        self.emb_dim    = emb_dim
        self.hidden_dim = hidden_dim

        self.embedding              = nn.Embedding(n_tokens, emb_dim)
        self.core                   = CounterCore(emb_dim, hidden_dim, n_tokens)
        self.gate_matrix            = nn.Parameter(torch.zeros(n_counts, n_tokens))
        self.count_state_embeddings = nn.Parameter(torch.zeros(n_counts, hidden_dim))
        nn.init.xavier_uniform_(self.count_state_embeddings)

        self.register_buffer("group_mask",        self._make_group_mask())
        self.register_buffer("group_priors",      self._make_group_priors())
        self.register_buffer("probs_ema",         torch.full((n_tokens,), 1.0 / n_tokens))
        self.register_buffer("count_logits_ema",  torch.zeros(n_counts))

        self.ema_alpha                = float(ema_alpha)
        self.repeg_alpha              = float(repeg_alpha)
        self.fine_tune                = True
        self.flat_actions             = True
        self.bypass_read_tokens       = True
        self.control_gate_with_finetune = bool(control_gate_with_finetune)
        self._external_adapter        = None
        self._h                       = torch.zeros(hidden_dim)
        self._probs                   = torch.full((n_tokens,), 1.0 / n_tokens)

    # --- group helpers --------------------------------------------------------

    def _make_group_mask(self):
        # Group 0: actions {INC, DEC};  Group 1: counts {C0 … C_{n-1}}
        gm = torch.zeros(2, self.n_tokens)
        gm[0, TOK_INC] = 1.0
        gm[0, TOK_DEC] = 1.0
        gm[1, TOK_C0 : TOK_C0 + self.n_counts] = 1.0
        return gm

    def _make_group_priors(self):
        return torch.tensor([2.0 / self.n_tokens, float(self.n_counts) / self.n_tokens])

    # --- training control -----------------------------------------------------

    def set_fine_tune(self, flag: bool):
        self.fine_tune = bool(flag)
        for p in self.core.parameters():
            p.requires_grad = self.fine_tune
        if self.control_gate_with_finetune:
            self.gate_matrix.requires_grad = self.fine_tune

    # --- forward --------------------------------------------------------------

    def forward_step(self, x_t_emb, h_prev):
        """Single-step forward. x_t_emb: 1-D [emb], h_prev: 1-D [hidden]."""
        if x_t_emb.dim() != 1 or h_prev.dim() != 1:
            raise ValueError("x_t_emb and h_prev must be 1-D tensors (no batching)")

        h_t, pred_logits_raw, count_logits = self.core(x_t_emb, h_prev)
        count_probs = F.softmax(count_logits, dim=-1)
        gate_bias   = torch.matmul(count_probs, self.gate_matrix)
        pred_probs  = self._recalibrate_groups(F.softmax(pred_logits_raw + gate_bias, dim=-1))
        if self.flat_actions:
            pred_probs = pred_probs.clone()
            pred_probs[TOK_INC] = 1.0 / self.n_tokens
            pred_probs[TOK_DEC] = 1.0 / self.n_tokens

        with torch.no_grad():
            self.probs_ema.mul_(1 - self.ema_alpha).add_(self.ema_alpha * pred_probs)
            self.count_logits_ema.mul_(1 - self.ema_alpha).add_(self.ema_alpha * count_logits)

        return h_t, pred_probs, count_probs

    def forward_step_tokens(self, token_idx, h_prev):
        """Accept scalar token index. Returns h_t, pred_probs, count_probs.

        Count tokens (>= TOK_C0) bypass the GRU: the hidden state is not advanced
        through an untrained embedding. Instead h_prev is kept (and optionally
        repegged), then pred_probs are recomputed from the resulting state.
        This closes the train/inference gap — the GRU sees only INC/DEC in both
        training and inference.
        """
        if isinstance(token_idx, torch.Tensor):
            if token_idx.dim() != 0:
                raise ValueError("token_idx must be scalar (0-d) — no batching")
            token_idx_t = token_idx.to(torch.long)
        else:
            token_idx_t = torch.tensor(int(token_idx), dtype=torch.long)

        if self.bypass_read_tokens and int(token_idx_t.item()) >= TOK_C0:
            # Read token: don't corrupt hidden state with an untrained embedding.
            count_logits = self.core.count_head(h_prev)
            count_probs  = F.softmax(count_logits, dim=-1)
            h_t = h_prev
            if self.repeg_alpha != 0.0:
                peg = torch.matmul(count_probs, self.count_state_embeddings)
                h_t = (1.0 - self.repeg_alpha) * h_prev + self.repeg_alpha * peg
            pred_logits_raw = self.core.pred_head(h_t)
            gate_bias       = torch.matmul(count_probs, self.gate_matrix)
            pred_probs      = self._recalibrate_groups(
                F.softmax(pred_logits_raw + gate_bias, dim=-1)
            )
            if self.flat_actions:
                pred_probs = pred_probs.clone()
                pred_probs[TOK_INC] = 1.0 / self.n_tokens
                pred_probs[TOK_DEC] = 1.0 / self.n_tokens
            return h_t, pred_probs, count_probs

        emb = self._external_adapter(token_idx_t) if self._external_adapter is not None \
              else self.embedding(token_idx_t)
        return self.forward_step(emb, h_prev)

    def _recalibrate_groups(self, probs):
        """Re-normalize so each token group's total probability matches its prior."""
        gm         = self.group_mask    # [2, n_tokens]
        priors     = self.group_priors  # [2]
        group_sums = (gm * probs.unsqueeze(0)).sum(dim=1).clamp_min(EPS)
        scale      = priors / group_sums
        return (gm * (probs.unsqueeze(0) * scale.unsqueeze(1))).sum(dim=0)

    # --- batched training forward ---------------------------------------------

    def forward_train(self, seqs_in, masks, seqs_tgt):
        """
        Batched forward for training only.

        seqs_in  : LongTensor [B, L]  — INC/DEC token ids
        masks    : BoolTensor  [B, L]  — True at positions that contribute to loss
        seqs_tgt : LongTensor [B, L]  — target count token ids

        Returns scalar mean NLL loss over masked positions.
        """
        B, L  = seqs_in.shape
        embs  = self.embedding(seqs_in)
        h0    = torch.zeros(B, self.hidden_dim)
        out   = self.core.forward_batch(embs, h0)

        pl          = self.core.pred_head(out)
        cl          = self.core.count_head(out)
        count_probs = F.softmax(cl, dim=-1)
        gate_bias   = torch.matmul(count_probs, self.gate_matrix)
        pred_probs  = F.softmax(pl + gate_bias, dim=-1)

        p_all   = pred_probs.gather(2, seqs_tgt.unsqueeze(2)).squeeze(2).clamp_min(EPS)
        nll     = -torch.log(p_all)
        n_reads = masks.sum().clamp_min(1)
        return (nll * masks.float()).sum() / n_reads

    # --- adapter --------------------------------------------------------------

    def attach_adapter(self, adapter: nn.Module):
        self._external_adapter = adapter

    def detach_adapter(self):
        self._external_adapter = None

    # --- serialisation --------------------------------------------------------

    def _config(self):
        return {
            "n_counts":                   self.n_counts,
            "emb_dim":                    self.emb_dim,
            "hidden_dim":                 self.hidden_dim,
            "ema_alpha":                  self.ema_alpha,
            "control_gate_with_finetune": self.control_gate_with_finetune,
            "repeg_alpha":                self.repeg_alpha,
        }

    def save(self, path: str):
        torch.save({"config": self._config(), "state_dict": self.state_dict()}, path)

    @classmethod
    def load(cls, path: str) -> "BoxedCounter":
        """Load a model saved with save(). Reconstructs architecture from config."""
        payload = torch.load(path, map_location="cpu")
        model   = cls(**payload["config"])
        model.load_state_dict(payload["state_dict"])
        return model

    def set_repeg(self, enabled: bool) -> None:
        """Protocol stub — repeg is implicit in the GRU dynamics."""
        pass

    def reset(self) -> None:
        """Reset hidden state to zeros. Call before a new scoring sequence."""
        self._h     = torch.zeros(self.hidden_dim)
        self._probs = torch.full((self.n_tokens,), 1.0 / self.n_tokens)

    def step(self, token: int) -> None:
        """Advance hidden state by one token."""
        self._h, self._probs, _ = self.forward_step_tokens(token, self._h)

    def predict(self) -> "torch.Tensor":
        """Return the current next-token distribution."""
        return self._probs

    # --- diagnostics ----------------------------------------------------------

    def get_embedding_weights(self):
        return self.embedding.weight.detach().cpu().clone()

    def set_embedding_weights(self, weights: torch.Tensor):
        if weights.shape != self.embedding.weight.shape:
            raise ValueError("weights shape mismatch")
        with torch.no_grad():
            self.embedding.weight.copy_(weights)

    def freeze_embedding(self, freeze: bool = True):
        for p in self.embedding.parameters():
            p.requires_grad = not freeze

    def get_probs_ema(self):
        return self.probs_ema.detach().cpu().clone()
