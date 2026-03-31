# matcher/brute_force/matcher.py
#
# Brute-force token-space matcher for BoxedCounter.
#
# Enumerates all permutations of the model's token vocabulary and scores each
# against a world-generated sequence. Feasible up to ~7 tokens (7! = 5040).
#
# The "match" question:
#   Is there a relabeling of the model's token space such that — when the world
#   sequence is fed through that relabeling — the model's next-token predictions
#   agree with the actual next world token?
#
# World token mapping (same as training):
#   increase  → TOK_INC  (0)
#   decrease  → TOK_DEC  (1)
#   read(n)   → TOK_C0+n (2+n)

import itertools
import random

import torch

from models.boxed_counter import BoxedCounter, TOK_INC, TOK_DEC, TOK_C0
from models.load import load_model, build_model
from world_perception.world_state_machine import WorldStateMachine
from world_perception.perception_pipeline import PerceptionPipeline


# ---------------------------------------------------------------------------
# World sequence generation
# ---------------------------------------------------------------------------

def event_to_token(event_name: str, count_value: int) -> int:
    if event_name == "read":
        return TOK_C0 + count_value
    return TOK_INC if event_name == "increase" else TOK_DEC


def generate_world_sequence(n_counts: int, seq_len: int, seed: int = 0, p_read: float = 0.6) -> list[int]:
    """Run WorldStateMachine directly and return a list of token indices."""
    world = WorldStateMachine(
        num_categories=1,
        max_count=n_counts,
        p_read=p_read,
        seed=seed,
    )
    tokens = []
    for _ in range(seq_len):
        event_name, category, _, state = world.random_event()
        count_value = int(state[category].item())
        tokens.append(event_to_token(event_name, count_value))
    return tokens


def generate_pipeline_sequence(
    n_counts: int,
    seq_len: int,
    embedder_path: str,
    resolver_path: str,
    seed: int = 0,
    p_read: float = 0.6,
) -> list[int]:
    """
    Run PerceptionPipeline and return token indices derived from event metadata.
    The pipeline adds the embedder + prototype resolver on top of the world —
    tokens are still identified from metadata (event_name, count), so the
    token mapping is the same as generate_world_sequence.
    """
    pipeline = PerceptionPipeline.create(
        num_categories=1,
        max_count=n_counts,
        seed=seed,
        p_read=p_read,
        embedder_path=embedder_path,
        resolver_path=resolver_path,
    )
    _, metadata = pipeline.get_token_sequence(seq_len)
    return [event_to_token(m["event_name"], m["count"]) for m in metadata]


# ---------------------------------------------------------------------------
# Scoring a single permutation
# ---------------------------------------------------------------------------

def score_permutation(
    model: BoxedCounter,
    world_tokens: list[int],
    perm: tuple[int, ...],
) -> float:
    """
    Map world_tokens through perm, run the model, compute predictive deficit.

    perm[world_token] = model_token.

    Deficit: sum over steps of max(threshold - pred_probs[m_next], 0).
    Lower is better. A perfect model that always meets the threshold scores 0.
    Threshold = 1/N (uniform baseline), entirely oblivious to group structure.
    """
    threshold = 1.0 / model.n_tokens
    deficit   = 0.0

    with torch.no_grad():
        model.reset()
        for i in range(len(world_tokens) - 1):
            m_curr = perm[world_tokens[i]]
            m_next = perm[world_tokens[i + 1]]

            model.step(m_curr)
            deficit += max(threshold - model.predict()[m_next].item(), 0.0)

    return deficit


def score_permutation_tiered(
    model: BoxedCounter,
    world_tokens: list[int],
    perm: tuple[int, ...],
    eps: float = 0.03,
    penalty: float = 1.0,
) -> float:
    """
    Stepped alternative to score_permutation. Lower is better.

    At each step, let deficit = threshold - pred_probs[m_next]:
      deficit <= eps          →  0          (within tolerance)
      eps < deficit <= 2*eps  →  penalty    (first tier)
      deficit > 2*eps         →  2*penalty  (second tier)

    eps    : tolerance — deviations up to eps from threshold are ignored.
    penalty: cost per tier step.
    """
    threshold = 1.0 / model.n_tokens
    score     = 0.0

    with torch.no_grad():
        model.reset()
        for i in range(len(world_tokens) - 1):
            m_curr = perm[world_tokens[i]]
            m_next = perm[world_tokens[i + 1]]

            model.step(m_curr)
            deficit = threshold - model.predict()[m_next].item()
            if deficit > 2 * eps:
                score += 4 * penalty
            elif deficit > eps:
                score += penalty

    return score


def score_permutation_cross_entropy(
    model: BoxedCounter,
    world_tokens: list[int],
    perm: tuple[int, ...],
) -> float:
    """
    Cross-entropy (NLL) scorer.  Lower is better.

    At each step: score += -log(pred_prob[m_next]).
    No threshold, no floor.  Penalises near-zero predictions exponentially.
    Clipped at 1e-10 to avoid log(0).
    """
    import math
    score = 0.0

    with torch.no_grad():
        model.reset()
        for i in range(len(world_tokens) - 1):
            m_curr = perm[world_tokens[i]]
            m_next = perm[world_tokens[i + 1]]
            model.step(m_curr)
            p = model.predict()[m_next].item()
            score += -math.log(max(p, 1e-10))

    return score


# ---------------------------------------------------------------------------
# Partial-wiring scorer (used by probe_wiring)
# ---------------------------------------------------------------------------

def score_wiring(
    model: BoxedCounter,
    world_sequences: list[list[int]],
    wiring: list,
    scorer: str = "deficit",
    scorer_params: dict = None,
) -> float:
    """
    Score an explicit partial wiring; deficit is averaged over world_sequences.

    wiring[world_token_idx] = model_token_idx, or None if not wired.

    Not-wired world tokens are completely skipped: the model hidden state is
    frozen for that step and no deficit is accumulated.  Only steps where the
    *next* world token is wired contribute to the deficit.
    """
    score_kwargs = scorer_params or {}
    threshold    = 1.0 / model.n_tokens
    total        = 0.0

    for world_tokens in world_sequences:
        deficit = 0.0
        with torch.no_grad():
            model.reset()
            for i in range(len(world_tokens) - 1):
                w_curr = world_tokens[i]
                w_next = world_tokens[i + 1]

                m_curr = wiring[w_curr] if w_curr < len(wiring) else None
                m_next = wiring[w_next] if w_next < len(wiring) else None

                if m_curr is None:
                    continue

                model.step(m_curr)

                if m_next is None:
                    continue

                p = model.predict()[m_next].item()
                if scorer == "tiered":
                    eps     = score_kwargs.get("eps",     0.02)
                    penalty = score_kwargs.get("penalty", 1.0)
                    d = threshold - p
                    if d > 2 * eps:
                        deficit += 2 * penalty
                    elif d > eps:
                        deficit += penalty
                else:
                    deficit += max(threshold - p, 0.0)
        total += deficit

    return total / len(world_sequences)


# ---------------------------------------------------------------------------
# Brute-force search
# ---------------------------------------------------------------------------

def perm_to_map(perm: tuple, n_world_tokens: int, n_model_tokens: int) -> dict:
    world_names = ["INC", "DEC"] + [f"C{i}" for i in range(n_world_tokens - 2)]
    model_names = ["INC", "DEC"] + [f"C{i}" for i in range(n_model_tokens - 2)]
    return {world_names[w]: model_names[perm[w]] for w in range(n_world_tokens)}


_SCORERS = {
    "deficit":       score_permutation,
    "tiered":        score_permutation_tiered,
    "cross_entropy": score_permutation_cross_entropy,
}


def brute_force_match(
    model: BoxedCounter,
    world_sequences: list[list[int]],
    top_k: int = 5,
    n_world_tokens: int = None,
    scorer: str = "deficit",
    scorer_params: dict = None,
    verbose: bool = True,
) -> dict:
    """
    Enumerate all wirings of the world token space into the model token space
    and return the top_k matches by deficit (ascending).

    world_sequences: list of token sequences; deficit is averaged across all.

    When world and model vocabularies differ in size, the search covers all
    injections of the smaller (world) vocabulary into the larger (model) one —
    i.e. itertools.permutations(range(n_model_tokens), n_world_tokens).
    This tries every ordered assignment of distinct model tokens to world tokens,
    so no valid partial wiring is missed.  When sizes are equal this reduces to
    the standard full-permutation search.

    n_world_tokens : vocabulary size of the world sequence. Inferred from
                     max token value across all sequences when not supplied.
    scorer         : "deficit" | "tiered"
    scorer_params  : kwargs forwarded to the scorer (e.g. eps, penalty for "tiered")

    Returns dict with:
        results   : list of {deficit, perm, token_map} sorted ascending by deficit
        n_perms   : int — total wirings evaluated
    """
    if scorer not in _SCORERS:
        raise ValueError(f"Unknown scorer {scorer!r}. Choose from {list(_SCORERS)}")
    score_fn     = _SCORERS[scorer]
    score_kwargs = scorer_params or {}

    n_model_tokens = model.n_tokens
    if n_world_tokens is None:
        n_world_tokens = max(t for seq in world_sequences for t in seq) + 1
    scored = []

    for n_perms, perm in enumerate(
        itertools.permutations(range(n_model_tokens), n_world_tokens), 1
    ):
        s = sum(score_fn(model, seq, perm, **score_kwargs) for seq in world_sequences)
        s /= len(world_sequences)
        scored.append((s, perm))

    scored.sort(key=lambda x: x[0])

    results = [
        {
            "deficit":   s,
            "perm":      list(p),
            "token_map": perm_to_map(p, n_world_tokens, n_model_tokens),
        }
        for s, p in scored[:top_k]
    ]

    if verbose:
        print(f"Top {top_k} permutations (of {n_perms} evaluated):\n")
        for rank, r in enumerate(results, 1):
            mapping = "  ".join(f"{k}→{v}" for k, v in r["token_map"].items())
            print(f"  #{rank}  deficit={r['deficit']:.4f}  [{mapping}]")

    return {"results": results, "n_perms": n_perms}


# ---------------------------------------------------------------------------
# N-stage incremental match (pooled, pluggable pruning)
# ---------------------------------------------------------------------------

def incremental_match_multistage(
    models: list,
    world_sequences_per_stage: list,
    n_world_tokens_per_stage: list,
    top_k: int = 5,
    pruning_strategy: str = "cliff",
    pruning_params: dict = None,
    scorer: str = "deficit",
    scorer_params: dict = None,
) -> dict:
    """
    N-stage incremental wiring with pooled cross-model pruning after each
    intermediate stage.

    models                   : [(name, BoxedCounter), ...]
    world_sequences_per_stage: [seqs_s1, seqs_s2, ..., seqs_sN]
    n_world_tokens_per_stage : [n_s1, n_s2, ..., n_sN]  (must be strictly increasing)
    pruning_strategy/params  : applied after every stage except the last.

    Stage 1: full brute-force over all models; pool; prune.
    Stage k (2..N-1): extend surviving (model, perm) pairs with all orderings of
        the k new world tokens; pool; prune.
    Stage N (final): extend; pool; no pruning — return top_k globally.

    Returns:
        {
          "n_stages": N,
          "stages":   [stage1_result, stage2_result, ..., stageN_result]
        }

    Each stage_result:
        results              — top_k entries {deficit, model, perm, token_map,
                               prev_perm, prev_token_map, prev_deficit}
                               (stage 1 has no prev_* fields)
        n_perms / n_perms_per_model
        n_contenders         — survivors after pruning (absent on final stage)
        contenders_per_model — {name: count} (absent on final stage)
        pruning_strategy, pruning_params (absent on final stage)
    """
    if scorer not in _SCORERS:
        raise ValueError(f"Unknown scorer {scorer!r}. Choose from {list(_SCORERS)}")
    score_fn     = _SCORERS[scorer]
    score_kwargs = scorer_params or {}
    pruning_params = pruning_params or {}

    n_stages = len(n_world_tokens_per_stage)
    assert n_stages == len(world_sequences_per_stage), "stages length mismatch"
    assert n_stages >= 2, "need at least 2 stages"

    from collections import Counter

    # ------------------------------------------------------------------ Stage 1
    n_world_s1 = n_world_tokens_per_stage[0]
    seqs_s1    = world_sequences_per_stage[0]

    all_s1 = []           # (deficit, name, perm, model_obj)
    n_perms_per_model = {}
    for name, model in models:
        n_model_tokens = model.n_tokens
        count = 0
        for perm in itertools.permutations(range(n_model_tokens), n_world_s1):
            count += 1
            s = sum(score_fn(model, seq, perm, **score_kwargs) for seq in seqs_s1)
            s /= len(seqs_s1)
            all_s1.append((s, name, perm, model))
        n_perms_per_model[name] = count
    all_s1.sort(key=lambda x: x[0])

    contenders = _apply_pruning(all_s1, pruning_strategy, pruning_params)
    cpm        = dict(Counter(name for _, name, _, _ in contenders))

    stage_results = [{
        "results": [
            {
                "deficit":   s,
                "model":     name,
                "perm":      list(perm),
                "token_map": perm_to_map(perm, n_world_s1, model.n_tokens),
            }
            for s, name, perm, model in all_s1[:top_k]
        ],
        "n_perms_per_model":  n_perms_per_model,
        "n_contenders":       len(contenders),
        "contenders_per_model": cpm,
        "pruning_strategy":   pruning_strategy,
        "pruning_params":     pruning_params,
    }]

    # (deficit, name, perm, model) — perm grows each stage
    current_contenders = contenders

    # --------------------------------------------------------------- Stages 2..N
    for stage_idx in range(1, n_stages):
        n_world_prev = n_world_tokens_per_stage[stage_idx - 1]
        n_world_curr = n_world_tokens_per_stage[stage_idx]
        n_new        = n_world_curr - n_world_prev
        seqs_curr    = world_sequences_per_stage[stage_idx]
        is_final     = (stage_idx == n_stages - 1)

        all_curr = []   # (deficit, name, full_perm, prev_perm, prev_deficit, model)
        n_perms_curr = 0

        for prev_deficit, name, prev_perm, model in current_contenders:
            n_model_tokens = model.n_tokens
            remaining = [t for t in range(n_model_tokens) if t not in set(prev_perm)]
            for ext in itertools.permutations(remaining, n_new):
                n_perms_curr += 1
                full_perm = prev_perm + ext
                s = sum(score_fn(model, seq, full_perm, **score_kwargs) for seq in seqs_curr)
                s /= len(seqs_curr)
                all_curr.append((s, name, full_perm, prev_perm, prev_deficit, model))
        all_curr.sort(key=lambda x: x[0])

        results_top = [
            {
                "deficit":       s,
                "model":         name,
                "perm":          list(perm),
                "token_map":     perm_to_map(perm, n_world_curr, model.n_tokens),
                "prev_perm":     list(pp),
                "prev_token_map": perm_to_map(pp, n_world_prev, model.n_tokens),
                "prev_deficit":  pd,
            }
            for s, name, perm, pp, pd, model in all_curr[:top_k]
        ]

        if is_final:
            stage_results.append({
                "results":  results_top,
                "n_perms":  n_perms_curr,
            })
            current_contenders = []
        else:
            # prune for next stage; carry full_perm forward
            prunable  = [(s, name, perm, model) for s, name, perm, _, _, model in all_curr]
            survived  = _apply_pruning(prunable, pruning_strategy, pruning_params)
            cpm_curr  = dict(Counter(name for _, name, _, _ in survived))
            stage_results.append({
                "results":             results_top,
                "n_perms":             n_perms_curr,
                "n_contenders":        len(survived),
                "contenders_per_model": cpm_curr,
                "pruning_strategy":    pruning_strategy,
                "pruning_params":      pruning_params,
            })
            current_contenders = survived

    return {"n_stages": n_stages, "stages": stage_results}


# ---------------------------------------------------------------------------
# Incremental (two-stage) match
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Partial-injection brute-force (lateral detection demo)
# ---------------------------------------------------------------------------

def brute_force_partial_match(
    model: BoxedCounter,
    world_sequences: list,
    n_partial_world_tokens: int,
    n_full_world_tokens: int,
    top_k: int = 5,
    scorer: str = "deficit",
    scorer_params: dict = None,
) -> dict:
    """
    Enumerate all injections of the first n_partial_world_tokens world tokens
    into the model space; score on world_sequences that may contain additional
    (unrecognised) world tokens.  Unrecognised tokens are silently skipped —
    the model's hidden state is not advanced and no deficit is accumulated.

    This simulates a matcher that ignores tokens it has not yet seen, e.g.
    scoring a cap4 world with only cap3 tokens wired.

    Returns dict with results (top_k) and n_perms.
    """
    n_model_tokens = model.n_tokens
    n_new = n_full_world_tokens - n_partial_world_tokens  # tokens to skip
    scored = []
    n_perms = 0

    for perm in itertools.permutations(range(n_model_tokens), n_partial_world_tokens):
        n_perms += 1
        # Full wiring: partial assignments + None for unrecognised slots
        wiring = list(perm) + [None] * n_new
        s = score_wiring(model, world_sequences, wiring,
                         scorer=scorer, scorer_params=scorer_params or {})
        scored.append((s, perm))

    scored.sort(key=lambda x: x[0])

    results = [
        {
            "deficit":   s,
            "perm":      list(p),
            "token_map": perm_to_map(p, n_partial_world_tokens, n_model_tokens),
        }
        for s, p in scored[:top_k]
    ]
    return {"results": results, "n_perms": n_perms}


# ---------------------------------------------------------------------------
# Pruning helpers
# ---------------------------------------------------------------------------

def _detect_cliff(
    sorted_deficits: list,
    cliff_min_gap: float = 0.1,
    min_contenders: int = 1,
    max_contenders: int = None,
) -> int:
    """
    Return how many entries to keep from a sorted (ascending) deficit list.

    Finds the index of the largest absolute gap; everything below it is kept.
    If the largest gap is smaller than cliff_min_gap, no cliff is declared and
    all entries are kept (subject to max_contenders).
    """
    n = len(sorted_deficits)
    if n <= min_contenders:
        return n

    best_gap  = -1.0
    cliff_idx = n - 1  # default: keep all
    for i in range(n - 1):
        gap = sorted_deficits[i + 1] - sorted_deficits[i]
        if gap > best_gap:
            best_gap  = gap
            cliff_idx = i

    cutoff = n if best_gap < cliff_min_gap else cliff_idx + 1
    cutoff = max(cutoff, min_contenders)
    if max_contenders is not None:
        cutoff = min(cutoff, max_contenders)
    return cutoff


def _apply_pruning(
    scored: list,
    strategy: str,
    params: dict,
) -> list:
    """
    Return the surviving subset of scored after applying the pruning strategy.

    scored entries are (deficit, ...) tuples, sorted ascending by deficit.

    strategy:
        "cliff"     — largest-gap detection; params: cliff_min_gap, min_contenders, max_contenders
        "threshold" — keep all with deficit <= pruning_threshold; params: pruning_threshold
        "topk"      — keep first top_k; params: top_k
    """
    params = params or {}
    if strategy == "threshold":
        thresh = params.get("pruning_threshold", 1.0)
        return [x for x in scored if x[0] <= thresh]
    elif strategy == "topk":
        return scored[: params.get("top_k", 10)]
    elif strategy == "cliff":
        deficits = [x[0] for x in scored]
        n_keep   = _detect_cliff(
            deficits,
            cliff_min_gap    = params.get("cliff_min_gap",    0.1),
            min_contenders   = params.get("min_contenders",   1),
            max_contenders   = params.get("max_contenders",   None),
        )
        return scored[:n_keep]
    else:
        raise ValueError(f"Unknown pruning_strategy {strategy!r}. "
                         f"Choose from 'cliff', 'threshold', 'topk'.")


# ---------------------------------------------------------------------------
# Pooled incremental match (cross-model, with pluggable pruning)
# ---------------------------------------------------------------------------

def incremental_match_pooled(
    models: list,
    world_sequences_s1: list,
    world_sequences_s2: list,
    n_world_tokens_s1: int,
    n_world_tokens_s2: int,
    top_k: int = 5,
    pruning_strategy: str = "cliff",
    pruning_params: dict = None,
    scorer: str = "deficit",
    scorer_params: dict = None,
) -> dict:
    """
    Two-stage incremental wiring with pooled cross-model pruning.

    models          : list of (name, BoxedCounter) pairs.
    pruning_strategy: "cliff" | "threshold" | "topk"
    pruning_params  : strategy-specific params dict.

    Stage 1: enumerate all injections for every model; pool all (deficit, name,
             perm, model) entries; prune the pool by strategy.
    Stage 2: extend every surviving entry with all orderings of that model's
             remaining tokens; globally rank results.

    Returns:
        stage1:
            results          — top_k pooled entries, sorted by deficit
            n_perms_per_model— {name: n_perms}
            n_contenders     — how many survived pruning
            contenders_per_model — {name: count}
            pruning_strategy, pruning_params
        stage2:
            results          — top_k pooled, each with s1_deficit / s1_token_map
            n_perms          — total stage-2 wirings evaluated
    """
    if scorer not in _SCORERS:
        raise ValueError(f"Unknown scorer {scorer!r}. Choose from {list(_SCORERS)}")
    score_fn     = _SCORERS[scorer]
    score_kwargs = scorer_params or {}
    pruning_params = pruning_params or {}
    n_new = n_world_tokens_s2 - n_world_tokens_s1

    # --- Stage 1: enumerate all wirings for every model, pool ---
    all_s1 = []   # (deficit, name, perm, model_obj)
    n_perms_per_model = {}
    for name, model in models:
        n_model_tokens = model.n_tokens
        count = 0
        for perm in itertools.permutations(range(n_model_tokens), n_world_tokens_s1):
            count += 1
            s = sum(score_fn(model, seq, perm, **score_kwargs) for seq in world_sequences_s1)
            s /= len(world_sequences_s1)
            all_s1.append((s, name, perm, model))
        n_perms_per_model[name] = count
    all_s1.sort(key=lambda x: x[0])

    # --- Prune ---
    contenders = _apply_pruning(all_s1, pruning_strategy, pruning_params)
    from collections import Counter
    contenders_per_model = dict(Counter(name for _, name, _, _ in contenders))

    stage1_results = [
        {
            "deficit":   s,
            "model":     name,
            "perm":      list(perm),
            "token_map": perm_to_map(perm, n_world_tokens_s1, model.n_tokens),
        }
        for s, name, perm, model in all_s1[:top_k]
    ]

    # --- Stage 2: extend every contender ---
    all_s2 = []
    n_perms_s2 = 0
    for s1_deficit, name, s1_perm, model in contenders:
        n_model_tokens = model.n_tokens
        remaining = [t for t in range(n_model_tokens) if t not in set(s1_perm)]
        for ext in itertools.permutations(remaining, n_new):
            n_perms_s2 += 1
            full_perm = s1_perm + ext
            s = sum(score_fn(model, seq, full_perm, **score_kwargs) for seq in world_sequences_s2)
            s /= len(world_sequences_s2)
            all_s2.append((s, name, full_perm, s1_perm, s1_deficit, model))
    all_s2.sort(key=lambda x: x[0])

    stage2_results = [
        {
            "deficit":      s,
            "model":        name,
            "perm":         list(perm),
            "token_map":    perm_to_map(perm, n_world_tokens_s2, model.n_tokens),
            "s1_perm":      list(s1p),
            "s1_token_map": perm_to_map(s1p, n_world_tokens_s1, model.n_tokens),
            "s1_deficit":   s1d,
        }
        for s, name, perm, s1p, s1d, model in all_s2[:top_k]
    ]

    return {
        "stage1": {
            "results":             stage1_results,
            "n_perms_per_model":   n_perms_per_model,
            "n_contenders":        len(contenders),
            "contenders_per_model": contenders_per_model,
            "pruning_strategy":    pruning_strategy,
            "pruning_params":      pruning_params,
        },
        "stage2": {
            "results":  stage2_results,
            "n_perms":  n_perms_s2,
        },
    }


def incremental_match(
    model,
    world_sequences_s1: list,
    world_sequences_s2: list,
    n_world_tokens_s1: int,
    n_world_tokens_s2: int,
    top_k: int = 5,
    scorer: str = "deficit",
    scorer_params: dict = None,
) -> dict:
    """
    Two-stage incremental wiring.

    Stage 1: brute-force all injections of n_world_tokens_s1 world tokens
             into the model's token space; scored on world_sequences_s1.
    Stage 2: lock the best stage-1 assignment; try all orderings of the
             remaining model tokens for the new world token slots
             (n_world_tokens_s2 - n_world_tokens_s1 new tokens).
             Scored on world_sequences_s2.

    Returns {"stage1": {results, n_perms}, "stage2": {results, n_perms}}.
    """
    if scorer not in _SCORERS:
        raise ValueError(f"Unknown scorer {scorer!r}. Choose from {list(_SCORERS)}")
    score_fn     = _SCORERS[scorer]
    score_kwargs = scorer_params or {}

    n_model_tokens = model.n_tokens
    n_new = n_world_tokens_s2 - n_world_tokens_s1

    # --- Stage 1 ---
    scored_s1 = []
    n_perms_s1 = 0
    for perm in itertools.permutations(range(n_model_tokens), n_world_tokens_s1):
        n_perms_s1 += 1
        s = sum(score_fn(model, seq, perm, **score_kwargs) for seq in world_sequences_s1)
        s /= len(world_sequences_s1)
        scored_s1.append((s, perm))
    scored_s1.sort(key=lambda x: x[0])

    stage1_results = [
        {
            "deficit":   s,
            "perm":      list(p),
            "token_map": perm_to_map(p, n_world_tokens_s1, n_model_tokens),
        }
        for s, p in scored_s1[:top_k]
    ]

    # --- Stage 2: extend best stage-1 perm with remaining model tokens ---
    best_s1_perm = scored_s1[0][1]
    remaining    = [t for t in range(n_model_tokens) if t not in set(best_s1_perm)]

    scored_s2 = []
    n_perms_s2 = 0
    for ext in itertools.permutations(remaining, n_new):
        n_perms_s2 += 1
        full_perm = best_s1_perm + ext
        s = sum(score_fn(model, seq, full_perm, **score_kwargs) for seq in world_sequences_s2)
        s /= len(world_sequences_s2)
        scored_s2.append((s, full_perm))
    scored_s2.sort(key=lambda x: x[0])

    stage2_results = [
        {
            "deficit":   s,
            "perm":      list(p),
            "token_map": perm_to_map(p, n_world_tokens_s2, n_model_tokens),
        }
        for s, p in scored_s2[:top_k]
    ]

    return {
        "stage1": {"results": stage1_results, "n_perms": n_perms_s1},
        "stage2": {"results": stage2_results, "n_perms": n_perms_s2},
    }


def incremental_topk_match(
    model,
    world_sequences_s1: list,
    world_sequences_s2: list,
    n_world_tokens_s1: int,
    n_world_tokens_s2: int,
    top_k: int = 5,
    s1_threshold: float = 1.0,
    scorer: str = "deficit",
    scorer_params: dict = None,
) -> dict:
    """
    Two-stage incremental wiring with threshold-based contender set.

    Stage 1: full brute-force over all injections of n_world_tokens_s1 world tokens
             into the model token space. All wirings with deficit <= s1_threshold are
             retained as contenders. The contender count is itself a result.

    Stage 2: extend every stage-1 contender with all orderings of the remaining model
             tokens for the new world token slots. The globally best extensions are
             returned. Each result records its stage-1 base and deficit.

    top_k    : number of rows to show in each output table.
    s1_threshold : deficit ceiling for stage-1 contenders. All wirings below this
                   value proceed to stage 2.
    """
    if scorer not in _SCORERS:
        raise ValueError(f"Unknown scorer {scorer!r}. Choose from {list(_SCORERS)}")
    score_fn     = _SCORERS[scorer]
    score_kwargs = scorer_params or {}

    n_model_tokens = model.n_tokens
    n_new = n_world_tokens_s2 - n_world_tokens_s1

    # --- Stage 1: full search ---
    scored_s1 = []
    n_perms_s1 = 0
    for perm in itertools.permutations(range(n_model_tokens), n_world_tokens_s1):
        n_perms_s1 += 1
        s = sum(score_fn(model, seq, perm, **score_kwargs) for seq in world_sequences_s1)
        s /= len(world_sequences_s1)
        scored_s1.append((s, perm))
    scored_s1.sort(key=lambda x: x[0])

    contenders = [(s, p) for s, p in scored_s1 if s <= s1_threshold]

    stage1_results = [
        {
            "deficit":   s,
            "perm":      list(p),
            "token_map": perm_to_map(p, n_world_tokens_s1, n_model_tokens),
        }
        for s, p in scored_s1[:top_k]
    ]

    # --- Stage 2: extend every contender ---
    all_s2 = []
    n_perms_s2 = 0
    for s1_deficit, s1_perm in contenders:
        remaining = [t for t in range(n_model_tokens) if t not in set(s1_perm)]
        for ext in itertools.permutations(remaining, n_new):
            n_perms_s2 += 1
            full_perm = s1_perm + ext
            s = sum(score_fn(model, seq, full_perm, **score_kwargs) for seq in world_sequences_s2)
            s /= len(world_sequences_s2)
            all_s2.append((s, full_perm, s1_perm, s1_deficit))
    all_s2.sort(key=lambda x: x[0])

    stage2_results = [
        {
            "deficit":      s,
            "perm":         list(p),
            "token_map":    perm_to_map(p, n_world_tokens_s2, n_model_tokens),
            "s1_perm":      list(s1p),
            "s1_token_map": perm_to_map(s1p, n_world_tokens_s1, n_model_tokens),
            "s1_deficit":   s1d,
        }
        for s, p, s1p, s1d in all_s2[:top_k]
    ]

    return {
        "stage1": {
            "results":    stage1_results,
            "n_perms":    n_perms_s1,
            "n_contenders": len(contenders),
            "s1_threshold": s1_threshold,
        },
        "stage2": {"results": stage2_results, "n_perms": n_perms_s2},
    }


# ---------------------------------------------------------------------------
# Error structure: per-token deficit breakdown and corrupt sequence generator
# ---------------------------------------------------------------------------

def generate_corrupt_world_sequence(
    n_counts: int,
    seq_len: int,
    seed: int = 0,
    p_read: float = 0.6,
    p_corrupt: float = 0.1,
) -> list[int]:
    """
    Generate a clean world sequence, then falsify some count token emissions.

    For each read token C_k in the clean sequence, with probability p_corrupt,
    replace it with a uniformly random C_j (j != k).  Action tokens (INC/DEC)
    and the world's internal counter state are never touched — only the emitted
    read signal is corrupted.  This simulates a screen violation: the world
    state machine is correct but the signal it puts on the screen is wrong.
    """
    import random as _random
    clean = generate_world_sequence(n_counts, seq_len, seed, p_read)
    rng   = _random.Random(seed ^ 0xDEAD_BEEF)
    result = []
    for tok in clean:
        if tok >= TOK_C0 and rng.random() < p_corrupt:
            actual  = tok - TOK_C0
            choices = [c for c in range(n_counts) if c != actual]
            if choices:
                tok = TOK_C0 + rng.choice(choices)
        result.append(tok)
    return result


def score_sequences_breakdown(
    model,
    world_sequences: list[list[int]],
    perm: tuple,
    n_world_tokens: int,
) -> dict:
    """
    Score a fixed wiring (perm) on multiple sequences and return the
    per-next-token deficit breakdown, averaged over sequences.

    perm[world_token] = model_token.  Tokens >= n_world_tokens are skipped.

    Returns:
        {
          "total":       float,                   # total deficit, seq-averaged
          "by_next":     {world_tok_idx: float},  # deficit when that tok is target
          "counts_next": {world_tok_idx: int},    # prediction steps per target tok
        }
    """
    threshold     = 1.0 / model.n_tokens
    by_next_sum   = {t: 0.0 for t in range(n_world_tokens)}
    counts_next   = {t: 0   for t in range(n_world_tokens)}
    total_sum     = 0.0

    for world_tokens in world_sequences:
        with torch.no_grad():
            model.reset()
            for i in range(len(world_tokens) - 1):
                w_curr = world_tokens[i]
                w_next = world_tokens[i + 1]
                if w_curr >= n_world_tokens or w_next >= n_world_tokens:
                    continue
                m_curr = perm[w_curr]
                m_next = perm[w_next]
                model.step(m_curr)
                d = max(threshold - model.predict()[m_next].item(), 0.0)
                by_next_sum[w_next] += d
                counts_next[w_next] += 1
                total_sum += d

    n_seqs = len(world_sequences)
    return {
        "total":       total_sum  / n_seqs,
        "by_next":     {t: v / n_seqs for t, v in by_next_sum.items()},
        "counts_next": counts_next,
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def match(
    weights_path: str = None,
    seq_len: int = 500,
    seed: int = 0,
    n_seeds: int = 1,
    top_k: int = 5,
    p_read: float = 0.6,
    n_counts: int = None,
    embedder_path: str = None,
    resolver_path: str = None,
    scorer: str = "deficit",
    scorer_params: dict = None,
    model_params: dict = None,
    model=None,
    verbose: bool = True,
) -> dict:
    """
    Run brute-force matching for a model against world sequences.

    Supply either weights_path (load from file) or model (pre-built instance).
    model_params : dict of attributes to set on the model after loading.
    n_seeds      : number of sequences to average over; seeds are seed, seed+1, ...
    n_counts     : world cap. Defaults to model.n_counts.

    If embedder_path and resolver_path are both provided, uses PerceptionPipeline
    to generate the world feed. Otherwise uses WorldStateMachine directly.
    """
    if model is None:
        model = load_model(weights_path)
    for k, v in (model_params or {}).items():
        setattr(model, k, v)
    if hasattr(model, "eval"):
        model.eval()

    if n_counts is None:
        n_counts = model.n_counts
    use_pipeline = embedder_path is not None and resolver_path is not None

    if use_pipeline:
        world_sequences = [
            generate_pipeline_sequence(
                n_counts, seq_len, embedder_path, resolver_path, seed + i, p_read=p_read
            )
            for i in range(n_seeds)
        ]
        feed_label = "PerceptionPipeline"
    else:
        world_sequences = [
            generate_world_sequence(n_counts, seq_len, seed + i, p_read=p_read)
            for i in range(n_seeds)
        ]
        feed_label = "WorldStateMachine"

    if verbose:
        print(f"Model:  n_counts={n_counts}, n_tokens={model.n_tokens}")
        print(f"Feed:   {feed_label}, seq_len={seq_len}, "
              f"seeds={seed}..{seed + n_seeds - 1}, p_read={p_read}")
        print(f"Search: {model.n_tokens}! = "
              f"{len(list(itertools.permutations(range(model.n_tokens))))} permutations")
        print()

    return brute_force_match(
        model, world_sequences,
        top_k=top_k, n_world_tokens=n_counts + 2,
        scorer=scorer, scorer_params=scorer_params, verbose=verbose,
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Brute-force token-space matcher for BoxedCounter")
    parser.add_argument("weights",                            help="Path to weights.pt")
    parser.add_argument("--seq_len",       type=int,   default=500)
    parser.add_argument("--seed",          type=int,   default=0)
    parser.add_argument("--top_k",         type=int,   default=5)
    parser.add_argument("--embedder_path", type=str,   default=None, help="Use PerceptionPipeline feed")
    parser.add_argument("--resolver_path", type=str,   default=None, help="Use PerceptionPipeline feed")
    args = parser.parse_args()

    match(
        weights_path   = args.weights,
        seq_len        = args.seq_len,
        seed           = args.seed,
        top_k          = args.top_k,
        embedder_path  = args.embedder_path,
        resolver_path  = args.resolver_path,
    )
