"""
train.py — cap4_ghost
==========================================
Cap4 architecture (n_counts=4, n_tokens=6) trained only on cap3 sequences.
Curriculum: cap1 → cap2 → cap3. Stage 4 is never run.
C3 receives zero gradient throughout — it is a ghost state.

Saves weights.pt when cap3 accuracy first reaches 80% for 2 consecutive epochs.

Usage (from repo root):
    python demos/wynns_world/models/pretrained/cap4_ghost/train.py
"""

import random
from pathlib import Path

import torch

from models.boxed_counter import BoxedCounter
from sequences import make_dataset

# --- config -------------------------------------------------------------------

N_COUNTS        = 4    # architecture: 4 count states, 6 tokens
TRAIN_STAGES    = 3    # curriculum stops at cap3 — C3 never trained
EMB_DIM         = 8
HIDDEN_DIM      = 16
N_SEQS          = 2000
SEQ_LEN         = 200
BATCH_SIZE      = 128
P_READ          = 0.5
LR              = 1e-3
MAX_EPOCHS      = 60
TARGET_ACC      = 0.80
CONSECUTIVE_REQ = 2
SEED            = 42

OUT = Path(__file__).parent / "weights.pt"

# --- evaluation ---------------------------------------------------------------

def evaluate(model, inp_t, tgt_t, msk_t, n_eval=256):
    model.eval()
    n  = min(n_eval, inp_t.shape[0])
    bi, bt, bm = inp_t[:n], tgt_t[:n], msk_t[:n]
    with torch.no_grad():
        embs        = model.embedding(bi)
        h0          = torch.zeros(n, model.hidden_dim)
        out         = model.core.forward_batch(embs, h0)
        pl          = model.core.pred_head(out)
        cl          = model.core.count_head(out)
        count_probs = torch.softmax(cl, dim=-1)
        gate_bias   = torch.matmul(count_probs, model.gate_matrix)
        pred_probs  = torch.softmax(pl + gate_bias, dim=-1)

        gm     = model.group_mask
        priors = model.group_priors
        gsums  = (pred_probs.unsqueeze(2) * gm).sum(-1)
        scale  = priors / gsums.clamp_min(1e-12)
        pred_probs = (pred_probs.unsqueeze(2) * scale.unsqueeze(-1) * gm).sum(2)

        preds   = pred_probs.argmax(dim=-1)
        correct = ((preds == bt) & bm).sum().item()
        total   = bm.sum().item()
    return correct / total if total > 0 else 0.0

# --- curriculum stage ---------------------------------------------------------

def run_stage(model, opt, active_counts):
    inputs, targets, masks = make_dataset(
        N_COUNTS, N_SEQS, SEQ_LEN, P_READ,
        seed=SEED + active_counts * 100,
        active_counts=active_counts,
    )
    inp_t = torch.tensor(inputs,  dtype=torch.long)
    tgt_t = torch.tensor(targets, dtype=torch.long)
    msk_t = torch.tensor(masks,   dtype=torch.bool)

    streak = 0
    for ep in range(1, MAX_EPOCHS + 1):
        model.train()
        rng   = random.Random(SEED + active_counts * 1000 + ep)
        order = list(range(N_SEQS))
        rng.shuffle(order)

        total_nll, total_batches = 0.0, 0
        for b_start in range(0, N_SEQS, BATCH_SIZE):
            idx = order[b_start : b_start + BATCH_SIZE]
            opt.zero_grad()
            loss = model.forward_train(inp_t[idx], msk_t[idx], tgt_t[idx])
            loss.backward()
            opt.step()
            total_nll    += loss.item()
            total_batches += 1

        acc = evaluate(model, inp_t, tgt_t, msk_t)
        print(f"  cap{active_counts} ep {ep:03d}  nll {total_nll/max(1,total_batches):.4f}  acc {acc:.4f}", end="")

        streak = streak + 1 if acc >= TARGET_ACC else 0
        if streak >= CONSECUTIVE_REQ:
            print(f"  → done")
            return True
        print()

    print(f"  cap{active_counts}: max epochs reached.")
    return False

# --- training -----------------------------------------------------------------

def main():
    torch.manual_seed(SEED)
    model = BoxedCounter(n_counts=N_COUNTS, emb_dim=EMB_DIM, hidden_dim=HIDDEN_DIM)
    model.set_fine_tune(True)
    opt = torch.optim.Adam(model.parameters(), lr=LR)

    for k in range(1, TRAIN_STAGES + 1):
        print(f"\n[stage cap{k}]")
        hit = run_stage(model, opt, active_counts=k)

    if hit:
        model.save(str(OUT))
        print(f"\nsaved {OUT.name}")
    else:
        print(f"\nMax epochs reached without hitting {TARGET_ACC:.0%} on cap{TRAIN_STAGES}.")


if __name__ == "__main__":
    main()
