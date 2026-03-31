# src/sequences.py
#
# Training sequence generation for BoxedCounter.
# Supports linear (non-wrapping) and modular (wrapping) counters.
#
# Linear : only INC valid at 0, only DEC valid at n_counts-1.
# Modular: INC and DEC always valid; counter wraps at boundaries.

import random
from models.boxed_counter import TOK_INC, TOK_DEC, TOK_C0


def make_sequence(n_counts, seq_len, p_read, rng, modular=False, active_counts=None):
    """
    Generate one training sequence.

    Input  : INC/DEC actions only (count tokens never appear as input).
    Target : count token after each action (always computed, masked for loss).
    Mask   : random Bernoulli(p_read) — which positions contribute to loss.

    active_counts : restrict state to [0, active_counts-1] for curriculum training.
                    Defaults to n_counts (full range). Architecture stays at n_counts.
    """
    if active_counts is None:
        active_counts = n_counts
    s = 0
    inp, tgt, mask = [], [], []
    for _ in range(seq_len):
        if modular:
            choices = [TOK_INC, TOK_DEC]
        else:
            choices = []
            if s > 0:
                choices.append(TOK_DEC)
            if s < active_counts - 1:
                choices.append(TOK_INC)
            if not choices:          # active_counts == 1: state is always 0
                choices = [TOK_INC, TOK_DEC]
        a = rng.choice(choices)
        if modular:
            s = (s + 1) % active_counts if a == TOK_INC else (s - 1) % active_counts
        else:
            s = min(s + 1, active_counts - 1) if a == TOK_INC else max(s - 1, 0)
        inp.append(a)
        tgt.append(TOK_C0 + s)
        mask.append(rng.random() < p_read)
    return inp, tgt, mask


def make_dataset(n_counts, n_seqs, seq_len, p_read, seed, modular=False, active_counts=None):
    rng = random.Random(seed)
    inputs, targets, masks = [], [], []
    for _ in range(n_seqs):
        i, t, m = make_sequence(n_counts, seq_len, p_read, rng,
                                modular=modular, active_counts=active_counts)
        inputs.append(i)
        targets.append(t)
        masks.append(m)
    return inputs, targets, masks
