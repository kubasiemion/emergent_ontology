"""
probe_wiring.py — deficit probe for a specific wiring
======================================================
Calculates the predictive deficit of an explicit world→model token wiring,
using world and scorer parameters taken from a match config.

Usage (from repo root):
    python demos/wynns_world/arena/probe_wiring.py \\
        wiring=(1,2,4,5,6) \\
        match=cap3_linear_directPlus \\
        model=cap4_acc80

Wiring syntax:
    A tuple of 1-indexed model vocabulary positions, one per world token
    (also 1-indexed by position).  Example: wiring=(1,2,4,5,6) maps
      world token 1 (INC) → model token 1 (INC)
      world token 2 (DEC) → model token 2 (DEC)
      world token 3 (C0)  → model token 4 (C1)
      world token 4 (C1)  → model token 5 (C2)
      world token 5 (C2)  → model token 6 (C3)

    Use 'x' for a world token that carries no signal: when it appears in the
    sequence the model hidden state is frozen and the step is not scored.
    World tokens not listed at all are treated identically to 'x'.

    Model vocab (1-indexed): 1=INC, 2=DEC, 3=C0, 4=C1, ..., 2+n=C(n-1)
    World vocab (1-indexed): same scheme, sized by world n_counts.
"""

import json
import sys
from pathlib import Path

ROOT       = Path(__file__).resolve().parents[3]
MATCHES    = Path(__file__).resolve().parent / "matches"

from matcher.brute_force.matcher import (
    generate_world_sequence,
    score_wiring,
)
from models.boxed_counter import BoxedCounter

TOKEN_NAMES = ["INC", "DEC"] + [f"C{i}" for i in range(32)]  # generous upper bound


def parse_args(argv):
    args = {}
    for tok in argv:
        if "=" in tok:
            k, v = tok.split("=", 1)
            args[k.strip()] = v.strip()
    return args


def parse_wiring(wiring_str: str, n_world_tokens: int) -> list:
    """
    Parse wiring string like '(1,2,4,5,6)' or '(1,x,4)' into a list of
    length n_world_tokens where each entry is either a 0-indexed model token
    index or None (not wired / frozen).
    """
    inner = wiring_str.strip().lstrip("(").rstrip(")")
    parts = [p.strip() for p in inner.split(",")]

    result = [None] * n_world_tokens
    for i, part in enumerate(parts):
        if i >= n_world_tokens:
            raise ValueError(
                f"Wiring has {len(parts)} entries but world only has "
                f"{n_world_tokens} tokens."
            )
        if part.lower() == "x":
            result[i] = None
        else:
            idx = int(part) - 1  # convert to 0-indexed
            result[i] = idx

    return result  # entries beyond len(parts) stay None (not listed = not wired)


def wiring_to_display(wiring: list, n_model_tokens: int) -> str:
    world_names = TOKEN_NAMES[:len(wiring)]
    model_names = TOKEN_NAMES[:n_model_tokens]
    pairs = []
    for w, m in enumerate(wiring):
        if m is not None:
            pairs.append(f"{world_names[w]}→{model_names[m]}")
        else:
            pairs.append(f"{world_names[w]}→x")
    return "  ".join(pairs)



def main():
    args = parse_args(sys.argv[1:])

    if not {"wiring", "match", "model"} <= args.keys():
        print(__doc__)
        sys.exit(1)

    # --- load match config ----------------------------------------------------
    match_dir   = MATCHES / args["match"]
    config_path = match_dir / "config.json"
    if not config_path.exists():
        print(f"Match not found: {match_dir}")
        sys.exit(1)

    config  = json.loads(config_path.read_text())
    world   = config["world"]
    mtcfg   = config["matcher"]
    scorer  = mtcfg.get("scorer", "deficit")
    sparams = mtcfg.get("scorer_params", {})

    # --- find model path ------------------------------------------------------
    model_name = args["model"]
    model_path = None
    for entry in config["models"]:
        if Path(entry).name == model_name:
            model_path = str(ROOT / entry / "weights.pt")
            break
    if model_path is None:
        print(f"Model '{model_name}' not found in match config.")
        print(f"Available: {[Path(e).name for e in config['models']]}")
        sys.exit(1)

    # --- load model & generate world sequence --------------------------------
    model = BoxedCounter.load(model_path)
    model.eval()

    n_world_counts = world["n_counts"]
    n_world_tokens = n_world_counts + 2
    n_seeds        = world.get("n_seeds", 1)

    world_sequences = [
        generate_world_sequence(
            n_counts = n_world_counts,
            seq_len  = world["seq_len"],
            seed     = world["seed"] + i,
            p_read   = world.get("p_read", 0.6),
        )
        for i in range(n_seeds)
    ]

    # --- parse & validate wiring ---------------------------------------------
    wiring = parse_wiring(args["wiring"], n_world_tokens)

    mapped = [w for w in wiring if w is not None]
    if len(mapped) != len(set(mapped)):
        print("Error: wiring maps two world tokens to the same model token.")
        sys.exit(1)
    for m in mapped:
        if m >= model.n_tokens:
            print(f"Error: model token index {m+1} out of range "
                  f"(model has {model.n_tokens} tokens).")
            sys.exit(1)

    # --- score & report -------------------------------------------------------
    deficit = score_wiring(model, world_sequences, wiring, scorer, sparams)

    n_wired = sum(1 for w in wiring if w is not None)
    print(f"Match:   {args['match']}")
    print(f"Model:   {model_name}  "
          f"(n_counts={model.n_counts}, n_tokens={model.n_tokens})")
    print(f"World:   n_counts={n_world_counts}  seq_len={world['seq_len']}  "
          f"seed={world['seed']}  p_read={world.get('p_read', 0.6)}")
    print(f"Scorer:  {scorer}" +
          (f"  params={sparams}" if sparams else ""))
    print(f"Wiring:  {wiring_to_display(wiring, model.n_tokens)}")
    print(f"         ({n_wired}/{n_world_tokens} world tokens wired)")
    print()
    print(f"Deficit: {deficit:.4f}")


if __name__ == "__main__":
    main()
