"""
run_match.py — central arena runner
=====================================
Loads a match config, runs the brute-force matcher against each model,
and writes results.json into the match folder.

Usage (from repo root):
    python demos/wynns_world/arena/run_match.py <match_folder>

Example:
    python demos/wynns_world/arena/run_match.py \\
        demos/wynns_world/arena/matches/cap3_linear_direct
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

import itertools as _itertools

from matcher.brute_force.matcher import (
    match, incremental_match, incremental_topk_match,
    incremental_match_pooled, incremental_match_multistage,
    brute_force_match, brute_force_partial_match,
    generate_world_sequence,
    generate_corrupt_world_sequence, score_sequences_breakdown,
    score_permutation, _apply_pruning, perm_to_map,
)
from models.load import build_model, load_model


def _pool_rows(config: dict, model_results: dict) -> tuple[list, list]:
    """Return (token_names, sorted rows) pooled across all models."""
    n_counts = config["world"]["n_counts"]
    token_names = ["INC", "DEC"] + [f"C{i}" for i in range(n_counts)]
    rows = []
    for name, res in model_results.items():
        for entry in res["results"]:
            rows.append((entry["deficit"], name, entry["token_map"]))
    rows.sort(key=lambda x: x[0])
    return token_names, rows


def _render_table(token_names: list, rows: list, title: str = "") -> list[str]:
    col_w   = max(len(n) for n in token_names)
    model_w = max((len(r[1]) for r in rows), default=5)
    model_w = max(model_w, len("Model"))

    header = (
        f"| {'Place':>5} | {'Deficit':>8} | {'Model':<{model_w}} | "
        + " | ".join(f"{n:^{col_w}}" for n in token_names)
        + " |"
    )
    sep = (
        f"| {'-'*5} | {'-'*8} | {'-'*model_w} | "
        + " | ".join("-" * col_w for _ in token_names)
        + " |"
    )
    lines = ([f"# {title}", ""] if title else []) + [header, sep]
    for place, (deficit, name, token_map) in enumerate(rows, 1):
        wiring = " | ".join(f"{token_map.get(n, '?'):^{col_w}}" for n in token_names)
        lines.append(f"| {place:>5} | {deficit:>8.4f} | {name:<{model_w}} | {wiring} |")
    return lines


def _render_table_s2(token_names: list, rows: list, title: str = "") -> list[str]:
    """Like _render_table but with an extra S1 Base deficit column."""
    col_w   = max(len(n) for n in token_names)
    model_w = max((len(r[1]) for r in rows), default=5)
    model_w = max(model_w, len("Model"))

    header = (
        f"| {'Place':>5} | {'Deficit':>8} | {'S1 Base':>8} | {'Model':<{model_w}} | "
        + " | ".join(f"{n:^{col_w}}" for n in token_names)
        + " |"
    )
    sep = (
        f"| {'-'*5} | {'-'*8} | {'-'*8} | {'-'*model_w} | "
        + " | ".join("-" * col_w for _ in token_names)
        + " |"
    )
    lines = ([f"# {title}", ""] if title else []) + [header, sep]
    for place, (deficit, name, token_map, s1_deficit) in enumerate(rows, 1):
        wiring = " | ".join(f"{token_map.get(n, '?'):^{col_w}}" for n in token_names)
        lines.append(
            f"| {place:>5} | {deficit:>8.4f} | {s1_deficit:>8.4f} | {name:<{model_w}} | {wiring} |"
        )
    return lines


def build_results_md(config: dict, model_results: dict) -> str:
    token_names, rows = _pool_rows(config, model_results)
    lines = _render_table(token_names, rows, title=config.get("description", "Match results"))
    return "\n".join(lines) + "\n"


def print_results(config: dict, model_results: dict):
    token_names, rows = _pool_rows(config, model_results)
    for line in _render_table(token_names, rows):
        print(line)


def _load_model_entry(entry):
    """Load a model entry from config. Returns (name, model)."""
    if isinstance(entry, str):
        name  = Path(entry).name
        model = load_model(str(ROOT / entry / "weights.pt"))
    elif "type" in entry:
        name  = entry.get("name", f"{entry['type']}_{entry.get('n_counts', '')}")
        model = build_model(entry)
    else:
        name   = entry.get("name", Path(entry["dir"]).name)
        model  = load_model(str(ROOT / entry["dir"] / "weights.pt"))
        params = {k: v for k, v in entry.items() if k not in ("dir", "name")}
        for k, v in params.items():
            setattr(model, k, v)
    if hasattr(model, "eval"):
        model.eval()
    return name, model


def _run_incremental(match_dir: Path, config: dict):
    world  = config["world"]
    mtcfg  = config["matcher"]
    n_counts_s2  = world["n_counts"]
    n_counts_s1  = mtcfg["departure_n_counts"]
    seq_len      = world["seq_len"]
    seed         = world["seed"]
    n_seeds      = world.get("n_seeds", 1)
    p_read       = world.get("p_read", 0.6)
    top_k        = mtcfg["top_k"]
    scorer       = mtcfg.get("scorer", "deficit")
    scorer_params = mtcfg.get("scorer_params", {})

    n_world_s1 = n_counts_s1 + 2
    n_world_s2 = n_counts_s2 + 2

    seqs_s1 = [generate_world_sequence(n_counts_s1, seq_len, seed + i, p_read) for i in range(n_seeds)]
    seqs_s2 = [generate_world_sequence(n_counts_s2, seq_len, seed + i, p_read) for i in range(n_seeds)]

    model_results = {}
    for entry in config["models"]:
        name, model = _load_model_entry(entry)
        print(f"  scoring {name} ...", end=" ", flush=True)
        result = incremental_match(
            model, seqs_s1, seqs_s2, n_world_s1, n_world_s2,
            top_k=top_k, scorer=scorer, scorer_params=scorer_params,
        )
        model_results[name] = result
        print("done")

    # --- Stage 1 report ---
    token_names_s1 = ["INC", "DEC"] + [f"C{i}" for i in range(n_counts_s1)]
    rows_s1 = []
    for name, res in model_results.items():
        for entry in res["stage1"]["results"]:
            rows_s1.append((entry["deficit"], name, entry["token_map"]))
    rows_s1.sort(key=lambda x: x[0])

    print(f"\n--- Stage 1  (departure: cap{n_counts_s1} world) ---\n")
    for line in _render_table(token_names_s1, rows_s1):
        print(line)

    # --- Stage 2 report ---
    token_names_s2 = ["INC", "DEC"] + [f"C{i}" for i in range(n_counts_s2)]
    rows_s2 = []
    for name, res in model_results.items():
        for entry in res["stage2"]["results"]:
            rows_s2.append((entry["deficit"], name, entry["token_map"]))
    rows_s2.sort(key=lambda x: x[0])

    print(f"\n--- Stage 2  (extended: cap{n_counts_s2} world, C{n_counts_s1}..C{n_counts_s2-1} locked from stage 1) ---\n")
    for line in _render_table(token_names_s2, rows_s2):
        print(line)

    output = {
        "timestamp": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "match":     match_dir.name,
        "config":    config,
        "results":   model_results,
    }
    (match_dir / "results.json").write_text(json.dumps(output, indent=2))

    # Build markdown with both stages
    md_lines  = [f"# Stage 1 — cap{n_counts_s1} departure", ""]
    md_lines += _render_table(token_names_s1, rows_s1)
    md_lines += ["", f"# Stage 2 — cap{n_counts_s2} extension", ""]
    md_lines += _render_table(token_names_s2, rows_s2)
    (match_dir / "results.md").write_text("\n".join(md_lines) + "\n")


def _run_incremental_topk(match_dir: Path, config: dict):
    world         = config["world"]
    mtcfg         = config["matcher"]
    n_counts_s2   = world["n_counts"]
    n_counts_s1   = mtcfg["departure_n_counts"]
    seq_len       = world["seq_len"]
    seed          = world["seed"]
    n_seeds       = world.get("n_seeds", 1)
    p_read        = world.get("p_read", 0.6)
    top_k         = mtcfg["top_k"]
    scorer        = mtcfg.get("scorer", "deficit")
    scorer_params = mtcfg.get("scorer_params", {})

    # Pruning config — legacy s1_threshold maps to threshold strategy
    if "pruning_strategy" in mtcfg:
        pruning_strategy = mtcfg["pruning_strategy"]
        pruning_params   = mtcfg.get("pruning_params", {})
    elif "s1_threshold" in mtcfg:
        pruning_strategy = "threshold"
        pruning_params   = {"pruning_threshold": mtcfg["s1_threshold"]}
    else:
        pruning_strategy = "cliff"
        pruning_params   = {}

    n_world_s1 = n_counts_s1 + 2
    n_world_s2 = n_counts_s2 + 2

    seqs_s1 = [generate_world_sequence(n_counts_s1, seq_len, seed + i, p_read) for i in range(n_seeds)]
    seqs_s2 = [generate_world_sequence(n_counts_s2, seq_len, seed + i, p_read) for i in range(n_seeds)]

    named_models = []
    for entry in config["models"]:
        name, model = _load_model_entry(entry)
        named_models.append((name, model))
        print(f"  loaded {name}")

    print(f"\n  running pooled match ({pruning_strategy} pruning) ...", flush=True)
    result = incremental_match_pooled(
        named_models, seqs_s1, seqs_s2, n_world_s1, n_world_s2,
        top_k=top_k,
        pruning_strategy=pruning_strategy,
        pruning_params=pruning_params,
        scorer=scorer,
        scorer_params=scorer_params,
    )
    n_cont = result["stage1"]["n_contenders"]
    cpm    = result["stage1"]["contenders_per_model"]
    print(f"  done  ({n_cont} total contenders)")

    # --- Stage 1 report ---
    token_names_s1 = ["INC", "DEC"] + [f"C{i}" for i in range(n_counts_s1)]
    rows_s1 = [(e["deficit"], e["model"], e["token_map"]) for e in result["stage1"]["results"]]

    strat_label = pruning_strategy
    if pruning_strategy == "threshold":
        strat_label += f"={pruning_params.get('pruning_threshold', 1.0)}"
    print(f"\n--- Stage 1  (departure: cap{n_counts_s1}, {strat_label} pruning) ---\n")
    for name, cnt in cpm.items():
        print(f"  {name}: {cnt} contenders")
    print()
    for line in _render_table(token_names_s1, rows_s1):
        print(line)

    # --- Stage 2 report ---
    token_names_s2 = ["INC", "DEC"] + [f"C{i}" for i in range(n_counts_s2)]
    rows_s2 = [
        (e["deficit"], e["model"], e["token_map"], e["s1_deficit"])
        for e in result["stage2"]["results"]
    ]

    print(f"\n--- Stage 2  (extended: cap{n_counts_s2}, best over all contenders) ---\n")
    for line in _render_table_s2(token_names_s2, rows_s2):
        print(line)

    output = {
        "timestamp": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "match":     match_dir.name,
        "config":    config,
        "results":   result,
    }
    (match_dir / "results.json").write_text(json.dumps(output, indent=2))

    # Build markdown
    md_lines  = [f"# Stage 1 — cap{n_counts_s1} departure  ({strat_label} pruning)", ""]
    md_lines.append(f"Contenders surviving to stage 2: **{n_cont}**")
    for name, cnt in cpm.items():
        md_lines.append(f"- **{name}**: {cnt}")
    md_lines.append("")
    md_lines += _render_table(token_names_s1, rows_s1)
    md_lines += ["", f"# Stage 2 — cap{n_counts_s2} extension  (S1 Base = stage-1 deficit)", ""]
    md_lines += _render_table_s2(token_names_s2, rows_s2)
    (match_dir / "results.md").write_text("\n".join(md_lines) + "\n")

    results_path = match_dir / "results.json"
    md_path      = match_dir / "results.md"
    print(f"\nResults written → {results_path}")
    print(f"Results written → {md_path}")


def _run_lateral_detection(match_dir: Path, config: dict):
    """
    Two-pass scoring on the same world sequences:
      Pass 1 — partial injection: only wire cap<partial_n_counts> tokens;
               new tokens are silently skipped (no deficit, no state advance).
      Pass 2 — full injection: all world tokens must be wired to something.

    A ghost model that has never seen the new token looks fine in pass 1
    and fails in pass 2.  The contrast shows that deficit alone cannot
    trigger rewiring if the matcher is allowed to ignore unknown tokens.
    """
    world         = config["world"]
    mtcfg         = config["matcher"]
    n_counts      = world["n_counts"]
    partial_n     = mtcfg["partial_n_counts"]
    seq_len       = world["seq_len"]
    seed          = world["seed"]
    n_seeds       = world.get("n_seeds", 1)
    p_read        = world.get("p_read", 0.6)
    top_k         = mtcfg["top_k"]
    scorer        = mtcfg.get("scorer", "deficit")
    scorer_params = mtcfg.get("scorer_params", {})

    n_world_full    = n_counts  + 2
    n_world_partial = partial_n + 2

    # Full world sequences — contain the new token(s)
    world_sequences = [
        generate_world_sequence(n_counts, seq_len, seed + i, p_read)
        for i in range(n_seeds)
    ]

    # Pass 1: filtered sequences — new token(s) removed entirely.
    # Models are scored only on steps where both current and next token
    # are known tokens; steps touching unknown tokens are silently skipped.
    filtered_sequences = [
        [t for t in seq if t < n_world_partial]
        for seq in world_sequences
    ]
    total_events    = sum(len(s) for s in world_sequences)
    filtered_events = sum(len(s) for s in filtered_sequences)
    filter_pct      = 100.0 * (1.0 - filtered_events / total_events)

    partial_model_results = {}
    full_model_results    = {}

    for entry in config["models"]:
        name, model = _load_model_entry(entry)
        print(f"  scoring {name} ...", end=" ", flush=True)

        partial_model_results[name] = brute_force_match(
            model, filtered_sequences,
            top_k=top_k, n_world_tokens=n_world_partial,
            scorer=scorer, scorer_params=scorer_params, verbose=False,
        )
        full_model_results[name] = brute_force_match(
            model, world_sequences,
            top_k=top_k, n_world_tokens=n_world_full,
            scorer=scorer, scorer_params=scorer_params, verbose=False,
        )
        print("done")

    skipped = " ".join(f"C{i}" for i in range(partial_n, n_counts))

    # --- Pass 1 table ---
    token_names_partial = ["INC", "DEC"] + [f"C{i}" for i in range(partial_n)]
    rows_partial = []
    for name, res in partial_model_results.items():
        for entry in res["results"]:
            rows_partial.append((entry["deficit"], name, entry["token_map"]))
    rows_partial.sort(key=lambda x: x[0])

    print(f"\n--- Pass 1: filtered observer  ({skipped} removed, {filter_pct:.1f}% of events dropped) ---\n")
    for line in _render_table(token_names_partial, rows_partial):
        print(line)

    # --- Pass 2 table ---
    token_names_full = ["INC", "DEC"] + [f"C{i}" for i in range(n_counts)]
    rows_full = []
    for name, res in full_model_results.items():
        for entry in res["results"]:
            rows_full.append((entry["deficit"], name, entry["token_map"]))
    rows_full.sort(key=lambda x: x[0])

    print(f"\n--- Pass 2: full observer  ({skipped} included, complete cap{n_counts} scoring) ---\n")
    for line in _render_table(token_names_full, rows_full):
        print(line)

    output = {
        "timestamp":  datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "match":      match_dir.name,
        "config":     config,
        "filter_pct": filter_pct,
        "results":    {"partial": partial_model_results, "full": full_model_results},
    }
    (match_dir / "results.json").write_text(json.dumps(output, indent=2))

    md_lines  = [f"# Pass 1 — filtered observer  ({skipped} removed, {filter_pct:.1f}% of events dropped)", ""]
    md_lines += _render_table(token_names_partial, rows_partial)
    md_lines += ["", f"# Pass 2 — full observer  (complete cap{n_counts} scoring)", ""]
    md_lines += _render_table(token_names_full, rows_full)
    (match_dir / "results.md").write_text("\n".join(md_lines) + "\n")

    results_path = match_dir / "results.json"
    md_path      = match_dir / "results.md"
    print(f"\nResults written → {results_path}")
    print(f"Results written → {md_path}")


def _run_incremental_multistage(match_dir: Path, config: dict):
    world         = config["world"]
    mtcfg         = config["matcher"]
    seq_len       = world["seq_len"]
    seed          = world["seed"]
    n_seeds       = world.get("n_seeds", 1)
    p_read        = world.get("p_read", 0.6)
    top_k         = mtcfg["top_k"]
    scorer        = mtcfg.get("scorer", "deficit")
    scorer_params = mtcfg.get("scorer_params", {})
    pruning_strategy = mtcfg.get("pruning_strategy", "cliff")
    pruning_params   = mtcfg.get("pruning_params", {})
    stage_n_counts   = mtcfg["stages"]   # e.g. [3, 4, 5]

    n_world_tokens_per_stage = [n + 2 for n in stage_n_counts]
    world_sequences_per_stage = [
        [generate_world_sequence(n, seq_len, seed + i, p_read) for i in range(n_seeds)]
        for n in stage_n_counts
    ]

    named_models = []
    for entry in config["models"]:
        name, model = _load_model_entry(entry)
        named_models.append((name, model))
        print(f"  loaded {name}")

    n_stages = len(stage_n_counts)
    print(f"\n  running {n_stages}-stage pooled match ({pruning_strategy} pruning) ...", flush=True)
    result = incremental_match_multistage(
        named_models,
        world_sequences_per_stage,
        n_world_tokens_per_stage,
        top_k=top_k,
        pruning_strategy=pruning_strategy,
        pruning_params=pruning_params,
        scorer=scorer,
        scorer_params=scorer_params,
    )

    strat_label = pruning_strategy
    if pruning_strategy == "threshold":
        strat_label += f"={pruning_params.get('pruning_threshold', 1.0)}"

    md_lines = []

    for si, stage in enumerate(result["stages"]):
        n_counts = stage_n_counts[si]
        token_names = ["INC", "DEC"] + [f"C{i}" for i in range(n_counts)]
        is_final    = (si == n_stages - 1)
        n_cont      = stage.get("n_contenders")
        cpm         = stage.get("contenders_per_model", {})

        if si == 0:
            print(f"\n--- Stage 1  (departure: cap{n_counts}, {strat_label} pruning) ---\n")
            for name, cnt in cpm.items():
                print(f"  {name}: {cnt} contenders")
            print()
            rows = [(e["deficit"], e["model"], e["token_map"]) for e in stage["results"]]
            for line in _render_table(token_names, rows):
                print(line)
            # markdown
            md_lines += [f"# Stage 1 — cap{n_counts} departure  ({strat_label} pruning)", ""]
            md_lines.append(f"Contenders surviving: **{n_cont}**")
            for name, cnt in cpm.items():
                md_lines.append(f"- **{name}**: {cnt}")
            md_lines.append("")
            md_lines += _render_table(token_names, rows)
        else:
            prev_n_counts = stage_n_counts[si - 1]
            stage_label   = f"Stage {si + 1}"
            if is_final:
                print(f"\n--- {stage_label}  (final: cap{n_counts}, best over all contenders) ---\n")
            else:
                print(f"\n--- {stage_label}  (cap{n_counts}, {strat_label} pruning) ---\n")
                for name, cnt in cpm.items():
                    print(f"  {name}: {cnt} contenders")
                print()

            rows_ext = [
                (e["deficit"], e["model"], e["token_map"], e["prev_deficit"])
                for e in stage["results"]
            ]
            for line in _render_table_s2(token_names, rows_ext):
                print(line)

            # markdown
            if is_final:
                md_lines += ["", f"# {stage_label} — cap{n_counts} final  (Prev = stage-{si} deficit)", ""]
            else:
                md_lines += ["", f"# {stage_label} — cap{n_counts} extension  ({strat_label} pruning)", ""]
                md_lines.append(f"Contenders surviving: **{n_cont}**")
                for name, cnt in cpm.items():
                    md_lines.append(f"- **{name}**: {cnt}")
                md_lines.append("")
            md_lines += _render_table_s2(token_names, rows_ext)

    output = {
        "timestamp": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "match":     match_dir.name,
        "config":    config,
        "results":   result,
    }
    (match_dir / "results.json").write_text(json.dumps(output, indent=2))
    (match_dir / "results.md").write_text("\n".join(md_lines) + "\n")

    results_path = match_dir / "results.json"
    md_path      = match_dir / "results.md"
    print(f"\nResults written → {results_path}")
    print(f"Results written → {md_path}")


def _render_breakdown_table(
    model_names: list,
    token_names: list,
    breakdowns: dict,
    counts_next: dict = None,
    title: str = "",
) -> list[str]:
    """
    Render per-next-token deficit breakdown.

    breakdowns : {model_name: {"total": float, "by_next": {tok_idx: float}}}
    counts_next: optional {model_name: {tok_idx: int}} — if given, adds a
                 deficit-per-step sub-row in italics-ish ASCII notation.
    """
    n_toks  = len(token_names)
    col_w   = max(max(len(n) for n in token_names), 7)
    mod_w   = max(max(len(n) for n in model_names), len("Model"))

    header = (
        f"| {'Model':<{mod_w}} | "
        + " | ".join(f"{n:^{col_w}}" for n in token_names)
        + f" | {'Total':>8} |"
    )
    sep = (
        f"| {'-'*mod_w} | "
        + " | ".join("-" * col_w for _ in token_names)
        + f" | {'-'*8} |"
    )
    lines = ([f"# {title}", ""] if title else []) + [header, sep]

    for name in model_names:
        bd    = breakdowns[name]
        total = bd["total"]
        cells = " | ".join(
            f"{bd['by_next'].get(t, 0.0):>{col_w}.4f}"
            for t in range(n_toks)
        )
        lines.append(f"| {name:<{mod_w}} | {cells} | {total:>8.4f} |")

        if counts_next and name in counts_next:
            cn = counts_next[name]
            per_step_cells = []
            for t in range(n_toks):
                steps = cn.get(t, 0)
                d     = bd["by_next"].get(t, 0.0)
                ps    = d / steps if steps > 0 else 0.0
                per_step_cells.append(f"{ps:>{col_w}.4f}")
            total_steps = sum(cn.get(t, 0) for t in range(n_toks))
            total_ps    = bd["total"] / (total_steps / len(model_names)) if total_steps else 0.0
            lines.append(
                f"| {'  /step':<{mod_w}} | "
                + " | ".join(per_step_cells)
                + f" | {'':>8} |"
            )

    return lines


def _run_scorer_robustness(match_dir: Path, config: dict):
    """
    Run the same match under multiple scorers and compare rankings.

    matcher.base_type    : "brute_force" (default) or "incremental_topk"
    matcher.scorers      : ["deficit", "tiered", "cross_entropy"]
    matcher.scorer_params: {scorer_name: {kwargs}}
    """
    world         = config["world"]
    mtcfg         = config["matcher"]
    n_counts      = world["n_counts"]
    seq_len       = world["seq_len"]
    seed          = world["seed"]
    n_seeds       = world.get("n_seeds", 1)
    p_read        = world.get("p_read", 0.6)
    top_k         = mtcfg["top_k"]
    scorers       = mtcfg["scorers"]
    scorer_params = mtcfg.get("scorer_params", {})
    base_type     = mtcfg.get("base_type", "brute_force")

    named_models = []
    for entry in config["models"]:
        named_models.append(_load_model_entry(entry))
        print(f"  loaded {named_models[-1][0]}")

    md_lines  = []
    all_results = {}

    if base_type == "brute_force":
        world_sequences = [
            generate_world_sequence(n_counts, seq_len, seed + i, p_read)
            for i in range(n_seeds)
        ]
        token_names = ["INC", "DEC"] + [f"C{i}" for i in range(n_counts)]

        for scorer in scorers:
            params = scorer_params.get(scorer, {})
            title  = f"Scorer: {scorer}"
            if params:
                title += "  (" + "  ".join(f"{k}={v}" for k, v in params.items()) + ")"
            print(f"\n--- {title} ---\n")

            model_results = {}
            for name, model in named_models:
                model_results[name] = brute_force_match(
                    model, world_sequences,
                    top_k=top_k, n_world_tokens=n_counts + 2,
                    scorer=scorer, scorer_params=params, verbose=False,
                )
            all_results[scorer] = model_results

            _, rows = _pool_rows(config, model_results)
            for line in _render_table(token_names, rows):
                print(line)
            md_lines += [f"# {title}", ""]
            md_lines += _render_table(token_names, rows)
            md_lines += [""]

    elif base_type == "incremental_topk":
        n_counts_s1      = mtcfg["departure_n_counts"]
        n_world_s1       = n_counts_s1 + 2
        n_world_s2       = n_counts    + 2
        pruning_strategy = mtcfg.get("pruning_strategy", "cliff")
        pruning_params   = mtcfg.get("pruning_params", {})
        token_names_s1   = ["INC", "DEC"] + [f"C{i}" for i in range(n_counts_s1)]
        token_names_s2   = ["INC", "DEC"] + [f"C{i}" for i in range(n_counts)]

        seqs_s1 = [generate_world_sequence(n_counts_s1, seq_len, seed + i, p_read)
                   for i in range(n_seeds)]
        seqs_s2 = [generate_world_sequence(n_counts,    seq_len, seed + i, p_read)
                   for i in range(n_seeds)]

        for scorer in scorers:
            params = scorer_params.get(scorer, {})
            title  = f"Scorer: {scorer}"
            if params:
                title += "  (" + "  ".join(f"{k}={v}" for k, v in params.items()) + ")"
            print(f"\n--- {title} ---\n")

            result = incremental_match_pooled(
                named_models, seqs_s1, seqs_s2, n_world_s1, n_world_s2,
                top_k=top_k,
                pruning_strategy=pruning_strategy,
                pruning_params=pruning_params,
                scorer=scorer,
                scorer_params=params,
            )
            all_results[scorer] = result

            rows_s1 = [(e["deficit"], e["model"], e["token_map"])
                       for e in result["stage1"]["results"]]
            rows_s2 = [(e["deficit"], e["model"], e["token_map"], e["s1_deficit"])
                       for e in result["stage2"]["results"]]

            print(f"  Stage 1 — cap{n_counts_s1}:")
            for line in _render_table(token_names_s1, rows_s1):
                print(line)
            print(f"\n  Stage 2 — cap{n_counts}:")
            for line in _render_table_s2(token_names_s2, rows_s2):
                print(line)

            md_lines += [f"# {title}", "",
                         f"## Stage 1 — cap{n_counts_s1}", ""]
            md_lines += _render_table(token_names_s1, rows_s1)
            md_lines += ["", f"## Stage 2 — cap{n_counts}  (S1 Base = stage-1 deficit)", ""]
            md_lines += _render_table_s2(token_names_s2, rows_s2)
            md_lines += [""]

    output = {
        "timestamp":  datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "match":      match_dir.name,
        "config":     config,
        "results":    all_results,
    }
    (match_dir / "results.json").write_text(json.dumps(output, indent=2))
    (match_dir / "results.md").write_text("\n".join(md_lines) + "\n")
    print(f"\nResults written → {match_dir / 'results.json'}")
    print(f"Results written → {match_dir / 'results.md'}")


def _run_error_structure(match_dir: Path, config: dict):
    """
    Two-scenario prediction error breakdown.

    Scenario A — world extension:
        Each model scored on the full (expanded) world using the canonical
        wiring (identity perm).  Deficit broken down by next-token type.
        Ghost deficit should be concentrated at the new count token.

    Scenario B — screen violation:
        Each model scored on the departure world with p_corrupt fraction of
        count tokens falsified.  Deficit broken down by next-token type.
        Both models should show equal, uniformly spread deficit — signal is
        non-discriminating.
    """
    world     = config["world"]
    n_full    = world["n_counts"]
    n_depart  = world["departure_n_counts"]
    seq_len   = world["seq_len"]
    seed      = world["seed"]
    n_seeds   = world.get("n_seeds", 1)
    p_read    = world.get("p_read", 0.6)
    p_corrupt = world.get("p_corrupt", 0.1)

    n_world_full   = n_full   + 2
    n_world_depart = n_depart + 2

    # Canonical perms: identity (world token i → model token i)
    perm_full   = tuple(range(n_world_full))
    perm_depart = tuple(range(n_world_depart))

    seqs_full = [
        generate_world_sequence(n_full, seq_len, seed + i, p_read)
        for i in range(n_seeds)
    ]
    seqs_corrupt = [
        generate_corrupt_world_sequence(n_depart, seq_len, seed + i, p_read, p_corrupt)
        for i in range(n_seeds)
    ]

    token_names_full   = ["INC", "DEC"] + [f"C{i}" for i in range(n_full)]
    token_names_depart = ["INC", "DEC"] + [f"C{i}" for i in range(n_depart)]

    model_names  = []
    bd_extension = {}
    bd_violation = {}

    for entry in config["models"]:
        name, model = _load_model_entry(entry)
        model_names.append(name)
        print(f"  scoring {name} ...", end=" ", flush=True)
        bd_extension[name] = score_sequences_breakdown(
            model, seqs_full, perm_full, n_world_full,
        )
        bd_violation[name] = score_sequences_breakdown(
            model, seqs_corrupt, perm_depart, n_world_depart,
        )
        print("done")

    new_tok = f"C{n_depart}"

    # Build per-step counts for the breakdown table
    cn_ext = {n: bd_extension[n]["counts_next"] for n in model_names}
    cn_vio = {n: bd_violation[n]["counts_next"] for n in model_names}

    print(f"\n--- Scenario A: world extension  (cap{n_full} world, canonical wiring, new token = {new_tok}) ---\n")
    for line in _render_breakdown_table(model_names, token_names_full, bd_extension,
                                        counts_next=cn_ext):
        print(line)

    print(f"\n--- Scenario B: screen violation  (cap{n_depart} world, canonical wiring, "
          f"p_corrupt={p_corrupt:.0%}) ---\n")
    for line in _render_breakdown_table(model_names, token_names_depart, bd_violation,
                                        counts_next=cn_vio):
        print(line)

    # Discrimination gap: max deficit diff between models at each token
    print(f"\n--- Discrimination gap (max deficit − min deficit across models, per token type) ---\n")
    ext_gaps  = []
    viol_gaps = []
    for t in range(n_world_full):
        vals = [bd_extension[n]["by_next"].get(t, 0.0) for n in model_names]
        ext_gaps.append(max(vals) - min(vals))
    for t in range(n_world_depart):
        vals = [bd_violation[n]["by_next"].get(t, 0.0) for n in model_names]
        viol_gaps.append(max(vals) - min(vals))

    col_w = 7
    print("Scenario A (extension):  " + "  ".join(
        f"{token_names_full[t]}:{ext_gaps[t]:.4f}" for t in range(n_world_full)
    ))
    print("Scenario B (violation):  " + "  ".join(
        f"{token_names_depart[t]}:{viol_gaps[t]:.4f}" for t in range(n_world_depart)
    ))
    print(f"\nTotal gap — A: {sum(ext_gaps):.4f}   B: {sum(viol_gaps):.4f}")

    output = {
        "timestamp":  datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "match":      match_dir.name,
        "config":     config,
        "p_corrupt":  p_corrupt,
        "extension": {
            n: {
                "total":       bd_extension[n]["total"],
                "by_next":     {str(k): v for k, v in bd_extension[n]["by_next"].items()},
                "counts_next": {str(k): v for k, v in bd_extension[n]["counts_next"].items()},
            } for n in model_names
        },
        "violation": {
            n: {
                "total":       bd_violation[n]["total"],
                "by_next":     {str(k): v for k, v in bd_violation[n]["by_next"].items()},
                "counts_next": {str(k): v for k, v in bd_violation[n]["counts_next"].items()},
            } for n in model_names
        },
    }
    (match_dir / "results.json").write_text(json.dumps(output, indent=2))

    md_lines = []
    md_lines += _render_breakdown_table(
        model_names, token_names_full, bd_extension, counts_next=cn_ext,
        title=f"Scenario A — World Extension  (cap{n_full} world, canonical wiring, new token = {new_tok})",
    )
    md_lines += [""]
    md_lines += _render_breakdown_table(
        model_names, token_names_depart, bd_violation, counts_next=cn_vio,
        title=f"Scenario B — Screen Violation  (cap{n_depart} world, canonical wiring, {p_corrupt:.0%} count corruption)",
    )
    md_lines += ["", "## Discrimination gap (max − min across models, per token)"]
    md_lines.append("")
    md_lines.append("Scenario A:  " + "  ".join(
        f"{token_names_full[t]}={ext_gaps[t]:.4f}" for t in range(n_world_full)
    ))
    md_lines.append("Scenario B:  " + "  ".join(
        f"{token_names_depart[t]}={viol_gaps[t]:.4f}" for t in range(n_world_depart)
    ))
    md_lines.append(f"\nTotal gap — A: {sum(ext_gaps):.4f}   B: {sum(viol_gaps):.4f}")
    (match_dir / "results.md").write_text("\n".join(md_lines) + "\n")

    results_path = match_dir / "results.json"
    md_path      = match_dir / "results.md"
    print(f"\nResults written → {results_path}")
    print(f"Results written → {md_path}")


def _run_error_structure_explicit(match_dir: Path, config: dict):
    """
    Error decomposition (per-next-token deficit breakdown) for an explicit list of
    (model, perm, label) triplets on the world specified in config.world.

    config.matcher.wirings — list of dicts:
        model  : path relative to repo root (same format as config.models)
        perm   : list of model-token indices, length = n_world_tokens
        label  : display name for the row
    """
    world  = config["world"]
    n_counts = world["n_counts"]
    seq_len  = world["seq_len"]
    seed     = world["seed"]
    n_seeds  = world.get("n_seeds", 1)
    p_read   = world.get("p_read", 0.6)
    n_world  = n_counts + 2

    seqs = [generate_world_sequence(n_counts, seq_len, seed + i, p_read) for i in range(n_seeds)]
    token_names = ["INC", "DEC"] + [f"C{i}" for i in range(n_counts)]

    wirings_cfg = config["matcher"]["wirings"]

    # Load models (cache by path)
    model_cache = {}
    entries = []   # (label, model, perm_tuple)
    for w in wirings_cfg:
        path = w["model"]
        if path not in model_cache:
            _, model = _load_model_entry(path)
            model_cache[path] = model
            print(f"  loaded {Path(path).name}")
        entries.append((w["label"], model_cache[path], tuple(w["perm"])))

    # Score each
    label_w = max(len(e[0]) for e in entries)
    breakdowns = {}
    for label, model, perm in entries:
        print(f"  scoring '{label}' ...", end=" ", flush=True)
        bd = score_sequences_breakdown(model, seqs, perm, n_world)
        breakdowns[label] = bd
        print("done")

    # Build combined breakdown table
    col_w = max(max(len(t) for t in token_names), 7)

    header = (
        f"| {'Wiring':<{label_w}} | "
        + " | ".join(f"{t:^{col_w}}" for t in token_names)
        + f" | {'Total':>8} |"
    )
    sep = (
        f"| {'-'*label_w} | "
        + " | ".join("-"*col_w for _ in token_names)
        + f" | {'-'*8} |"
    )

    print(f"\n--- Error decomposition  (cap{n_counts} world, canonical = identity extended) ---\n")
    print(header)
    print(sep)
    for label, model, perm in entries:
        bd    = breakdowns[label]
        total = bd["total"]
        cells = " | ".join(f"{bd['by_next'].get(t, 0.0):>{col_w}.4f}" for t in range(n_world))
        print(f"| {label:<{label_w}} | {cells} | {total:>8.4f} |")
        cn = bd["counts_next"]
        total_steps = sum(cn.get(t, 0) for t in range(n_world))
        ps_cells = " | ".join(
            f"{bd['by_next'].get(t, 0.0) / cn[t] if cn.get(t, 0) > 0 else 0.0:>{col_w}.4f}"
            for t in range(n_world)
        )
        print(f"| {'  /step':<{label_w}} | {ps_cells} | {'':>8} |")

    md_lines = [
        f"# Error Decomposition — cap{n_counts} world extension",
        "",
        "Per-next-token deficit breakdown.  `/step` rows show deficit per occurrence.",
        "",
        header, sep,
    ]
    for label, model, perm in entries:
        bd    = breakdowns[label]
        total = bd["total"]
        cn    = bd["counts_next"]
        cells = " | ".join(f"{bd['by_next'].get(t, 0.0):>{col_w}.4f}" for t in range(n_world))
        md_lines.append(f"| {label:<{label_w}} | {cells} | {total:>8.4f} |")
        ps_cells = " | ".join(
            f"{bd['by_next'].get(t, 0.0) / cn[t] if cn.get(t, 0) > 0 else 0.0:>{col_w}.4f}"
            for t in range(n_world)
        )
        md_lines.append(f"| {'  /step':<{label_w}} | {ps_cells} | {'':>8} |")

    output = {
        "timestamp": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "match":     match_dir.name,
        "config":    config,
        "results":   {
            label: {
                "total":       breakdowns[label]["total"],
                "by_next":     {str(k): v for k, v in breakdowns[label]["by_next"].items()},
                "counts_next": {str(k): v for k, v in breakdowns[label]["counts_next"].items()},
                "perm":        list(perm),
            }
            for label, _, perm in entries
        },
    }
    (match_dir / "results.json").write_text(json.dumps(output, indent=2))
    (match_dir / "results.md").write_text("\n".join(md_lines) + "\n")
    print(f"\nResults written → {match_dir / 'results.json'}")
    print(f"Results written → {match_dir / 'results.md'}")


def _run_error_structure_from(match_dir: Path, config: dict):
    """
    Score screen-violation deficit for every wiring in a source match's stage-N results.

    Each (model, perm) from the source stage is scored on corrupted departure-world
    sequences.  The table shows stage-1 deficit alongside the violation deficit so
    the reader can see whether the stage-1 ordering is preserved, inverted, or scrambled.

    config fields:
        world.n_counts      — departure world cap (cap3 → n_counts=3)
        world.p_corrupt     — corruption fraction (default 0.1)
        matcher.source_match — path to source match directory (relative to repo root)
        matcher.stage       — which stage to pull wirings from (1-indexed, default 1)
    """
    world         = config["world"]
    mtcfg         = config["matcher"]
    n_counts      = world["n_counts"]
    seq_len       = world["seq_len"]
    seed          = world["seed"]
    n_seeds       = world.get("n_seeds", 1)
    p_read        = world.get("p_read", 0.6)
    p_corrupt     = world.get("p_corrupt", 0.1)
    stage_idx     = mtcfg.get("stage", 1) - 1   # 0-indexed

    n_world = n_counts + 2

    source_dir    = ROOT / mtcfg["source_match"]
    source_results = json.loads((source_dir / "results.json").read_text())

    # Load models
    named_models = {}
    for entry in config["models"]:
        name, model = _load_model_entry(entry)
        named_models[name] = model
        print(f"  loaded {name}")

    # Gather all (s1_deficit, model_name, perm) from the source stage,
    # pooled across all models, sorted by stage-1 deficit
    src_res = source_results["results"]
    all_wirings = []   # (s1_deficit, model_name, perm_tuple)

    for model_name, model_data in src_res.items():
        stages = model_data if isinstance(model_data, dict) else {}
        # per-model structure: {"stage1": {"results": [...]}, "stage2": {...}}
        stage_key = f"stage{stage_idx + 1}"
        if stage_key not in stages:
            print(f"  WARNING: {model_name} has no {stage_key}")
            continue
        for entry in stages[stage_key]["results"]:
            all_wirings.append((
                entry["deficit"],
                model_name,
                tuple(entry["perm"]),
            ))

    all_wirings.sort(key=lambda x: x[0])
    print(f"\n  {len(all_wirings)} wirings loaded from {source_dir.name} stage {stage_idx + 1}")

    # Generate corrupted sequences
    seqs_corrupt = [
        generate_corrupt_world_sequence(n_counts, seq_len, seed + i, p_read, p_corrupt)
        for i in range(n_seeds)
    ]

    token_names = ["INC", "DEC"] + [f"C{i}" for i in range(n_counts)]

    # Score each wiring on screen-violation sequences
    model_w = max(len(n) for n in named_models)
    col_w   = max(len(t) for t in token_names)

    header = (
        f"| {'Place':>5} | {'S1 Def':>7} | {'Viol Def':>8} | {'Model':<{model_w}} | "
        + " | ".join(f"{t:^{col_w}}" for t in token_names)
        + " |"
    )
    sep = (
        f"| {'-'*5} | {'-'*7} | {'-'*8} | {'-'*model_w} | "
        + " | ".join("-" * col_w for _ in token_names)
        + " |"
    )

    results_rows = []
    for s1_def, model_name, perm in all_wirings:
        model = named_models.get(model_name)
        if model is None:
            print(f"  WARNING: model {model_name!r} not loaded — skipping")
            continue
        viol_def = sum(
            score_permutation(model, seq, perm) for seq in seqs_corrupt
        ) / len(seqs_corrupt)
        results_rows.append((s1_def, viol_def, model_name, perm))

    # Sort by violation deficit for the output table
    results_rows_by_viol = sorted(results_rows, key=lambda x: x[1])

    print(f"\n--- Screen violation deficit for all stage-{stage_idx + 1} wirings"
          f"  (cap{n_counts} world, canonical = identity, p_corrupt={p_corrupt:.0%}) ---\n")
    print(header)
    print(sep)
    for place, (s1_def, v_def, model_name, perm) in enumerate(results_rows_by_viol, 1):
        token_map = perm_to_map(perm, n_world, named_models[model_name].n_tokens)
        wiring = " | ".join(f"{token_map.get(t, '?'):^{col_w}}" for t in token_names)
        print(f"| {place:>5} | {s1_def:>7.4f} | {v_def:>8.4f} | {model_name:<{model_w}} | {wiring} |")

    # Also show sorted by s1 deficit for comparison
    results_rows_by_s1 = sorted(results_rows, key=lambda x: x[0])

    md_lines = [
        f"# Screen Violation — all stage-{stage_idx + 1} wirings  "
        f"(cap{n_counts} world, {p_corrupt:.0%} corruption)",
        "",
        "Sorted by violation deficit. S1 Def = original stage-1 deficit from source match.",
        "",
        header, sep,
    ]
    for place, (s1_def, v_def, model_name, perm) in enumerate(results_rows_by_viol, 1):
        token_map = perm_to_map(perm, n_world, named_models[model_name].n_tokens)
        wiring = " | ".join(f"{token_map.get(t, '?'):^{col_w}}" for t in token_names)
        md_lines.append(
            f"| {place:>5} | {s1_def:>7.4f} | {v_def:>8.4f} | {model_name:<{model_w}} | {wiring} |"
        )

    md_lines += [
        "",
        "## Same wirings sorted by stage-1 deficit",
        "",
        header, sep,
    ]
    for place, (s1_def, v_def, model_name, perm) in enumerate(results_rows_by_s1, 1):
        token_map = perm_to_map(perm, n_world, named_models[model_name].n_tokens)
        wiring = " | ".join(f"{token_map.get(t, '?'):^{col_w}}" for t in token_names)
        md_lines.append(
            f"| {place:>5} | {s1_def:>7.4f} | {v_def:>8.4f} | {model_name:<{model_w}} | {wiring} |"
        )

    output = {
        "timestamp": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "match":     match_dir.name,
        "config":    config,
        "results":   [
            {
                "s1_deficit":   s1,
                "viol_deficit": v,
                "model":        mn,
                "perm":         list(p),
            }
            for s1, v, mn, p in results_rows_by_s1
        ],
    }
    (match_dir / "results.json").write_text(json.dumps(output, indent=2))
    (match_dir / "results.md").write_text("\n".join(md_lines) + "\n")
    print(f"\nResults written → {match_dir / 'results.json'}")
    print(f"Results written → {match_dir / 'results.md'}")


def _run_retention_sweep(match_dir: Path, config: dict):
    """
    Run the same N-stage incremental match under multiple pruning policies.

    Stages 1..N are scored once; only the pruning decisions differ per policy.
    This avoids redundant re-scoring of the same permutations.

    config.matcher fields:
        stages          : [n_counts, ...]  e.g. [3, 4, 5]
        top_k           : int
        scorer          : str  (only "deficit" supported here)
        policies        : list of dicts, each with:
            name                — key for output
            label               — display string
            pruning_strategy    — "cliff" | "threshold" | "topk"
            pruning_params      — passed to _apply_pruning
    """
    world         = config["world"]
    mtcfg         = config["matcher"]
    seq_len       = world["seq_len"]
    seed          = world["seed"]
    n_seeds       = world.get("n_seeds", 1)
    p_read        = world.get("p_read", 0.6)
    top_k         = mtcfg["top_k"]
    stage_n_counts = mtcfg["stages"]
    policies       = mtcfg["policies"]

    n_stages   = len(stage_n_counts)
    nw         = [n + 2 for n in stage_n_counts]   # n_world_tokens per stage
    seqs       = [
        [generate_world_sequence(n, seq_len, seed + i, p_read) for i in range(n_seeds)]
        for n in stage_n_counts
    ]

    named_models = []
    for entry in config["models"]:
        name, model = _load_model_entry(entry)
        named_models.append((name, model))
        print(f"  loaded {name}")

    model_names = [nm for nm, _ in named_models]

    # ------------------------------------------------------------------
    # Stage 1 — score ALL perms once, cache
    # entry format: (deficit, name, perm_tuple, model)
    # ------------------------------------------------------------------
    print(f"\n  scoring stage 1 (cap{stage_n_counts[0]}, {nw[0]} tokens) ...", flush=True)
    all_s1 = []
    for name, model in named_models:
        for perm in _itertools.permutations(range(model.n_tokens), nw[0]):
            s = sum(score_permutation(model, seq, perm) for seq in seqs[0]) / len(seqs[0])
            all_s1.append((s, name, perm, model))
    all_s1.sort(key=lambda x: x[0])
    print(f"  stage 1 done — {len(all_s1)} total permutations scored")

    # Per-policy: apply pruning to stage-1 pool
    # contenders_s1[pname] = [(deficit, name, perm, model), ...]
    contenders_s1 = {}
    for policy in policies:
        pname    = policy["name"]
        strategy = policy.get("pruning_strategy", "cliff")
        params   = policy.get("pruning_params", {})
        contenders_s1[pname] = _apply_pruning(all_s1, strategy, params)

    # ------------------------------------------------------------------
    # Stages 2 .. N-1 (intermediate) and N (final)
    # For each stage: score the UNION of all policies' contenders once,
    # then branch per policy.
    # ------------------------------------------------------------------
    # stage_data[si] = sorted list of
    #   (deficit, name, full_perm, prev_perm, prev_deficit, model)
    # for the UNION of extensions scored at that stage.
    # We build these lazily, stage by stage.

    # Start from stage-1 contenders
    # prev_pool_by_policy[pname] = [(deficit, name, perm, model), ...]
    prev_pool_by_policy = contenders_s1

    # stage_results accumulates per-policy output dicts (matching the structure
    # used by the rest of the reporting code)
    policy_stage_results = {p["name"]: [] for p in policies}

    # Record stage-1 info for each policy
    from collections import Counter as _Counter
    for policy in policies:
        pname = policy["name"]
        pool  = prev_pool_by_policy[pname]
        cpm   = dict(_Counter(name for _, name, _, _ in pool))
        policy_stage_results[pname].append({
            "n_contenders":        len(pool),
            "contenders_per_model": cpm,
            "results": [
                {
                    "deficit":   s,
                    "model":     name,
                    "perm":      list(perm),
                    "token_map": perm_to_map(perm, nw[0], model.n_tokens),
                }
                for s, name, perm, model in pool[:top_k]
            ],
        })

    for stage_idx in range(1, n_stages):
        n_prev  = nw[stage_idx - 1]
        n_curr  = nw[stage_idx]
        n_new   = n_curr - n_prev
        is_final = (stage_idx == n_stages - 1)

        # Union of all contenders entering this stage across all policies
        union_key = {}   # (name, prev_perm) -> (prev_deficit, model)
        for policy in policies:
            for deficit, name, prev_perm, model in prev_pool_by_policy[policy["name"]]:
                key = (name, prev_perm)
                if key not in union_key:
                    union_key[key] = (deficit, model)

        print(
            f"  scoring stage {stage_idx + 1} (cap{stage_n_counts[stage_idx]}, "
            f"{len(union_key)} unique contenders → {len(union_key) * (2 if n_new == 1 else n_new)} extensions) ...",
            flush=True,
        )

        # Score all extensions in the union
        # ext_cache[(name, prev_perm, ext)] = (deficit, model)
        ext_cache = {}
        for (name, prev_perm), (prev_deficit, model) in union_key.items():
            remaining = [t for t in range(model.n_tokens) if t not in set(prev_perm)]
            for ext in _itertools.permutations(remaining, n_new):
                full_perm = prev_perm + ext
                s = sum(score_permutation(model, seq, full_perm) for seq in seqs[stage_idx]) / len(seqs[stage_idx])
                ext_cache[(name, prev_perm, ext)] = (s, prev_deficit, model)

        print(f"  stage {stage_idx + 1} done — {len(ext_cache)} extensions scored")

        # Per-policy: assemble extensions from their stage contenders, prune (if intermediate)
        new_prev_pool_by_policy = {}
        for policy in policies:
            pname    = policy["name"]
            strategy = policy.get("pruning_strategy", "cliff")
            params   = policy.get("pruning_params", {})

            # Build sorted extension list for this policy's contenders
            ext_list = []   # (deficit, name, full_perm, prev_perm, prev_deficit, model)
            for _, name, prev_perm, model in prev_pool_by_policy[pname]:
                remaining = [t for t in range(model.n_tokens) if t not in set(prev_perm)]
                for ext in _itertools.permutations(remaining, n_new):
                    key = (name, prev_perm, ext)
                    s, prev_d, m = ext_cache[key]
                    ext_list.append((s, name, prev_perm + ext, prev_perm, prev_d, m))
            ext_list.sort(key=lambda x: x[0])

            results_top = [
                {
                    "deficit":       s,
                    "model":         name,
                    "perm":          list(full_perm),
                    "token_map":     perm_to_map(full_perm, n_curr, model.n_tokens),
                    "prev_deficit":  prev_d,
                    "prev_token_map": perm_to_map(prev_perm, n_prev, model.n_tokens),
                }
                for s, name, full_perm, prev_perm, prev_d, model in ext_list[:top_k]
            ]

            if is_final:
                policy_stage_results[pname].append({"results": results_top})
                new_prev_pool_by_policy[pname] = []
            else:
                prunable = [(s, name, fp, m) for s, name, fp, pp, pd, m in ext_list]
                survived = _apply_pruning(prunable, strategy, params)
                cpm_curr = dict(_Counter(name for _, name, _, _ in survived))
                policy_stage_results[pname].append({
                    "n_contenders":         len(survived),
                    "contenders_per_model": cpm_curr,
                    "results":              results_top,
                })
                new_prev_pool_by_policy[pname] = survived

        prev_pool_by_policy = new_prev_pool_by_policy

    # ------------------------------------------------------------------
    # Build all_results in the same shape as incremental_match_multistage
    # ------------------------------------------------------------------
    all_results = {
        p["name"]: {"n_stages": n_stages, "stages": policy_stage_results[p["name"]]}
        for p in policies
    }

    # ------------------------------------------------------------------
    # Summary table
    # ------------------------------------------------------------------
    inter_stages = stage_n_counts[:-1]

    md_lines = [
        "# Retention Policy Sweep — Summary",
        "",
        "Each cell shows contenders surviving the intermediate stage for that model.",
        "A '0' means the model was eliminated before the final.",
        "",
    ]

    hcols = []
    for nc in inter_stages:
        for mname in model_names:
            hcols.append(f"cap{nc} {mname}")

    header = "| Policy | " + " | ".join(hcols) + " | Final winner | Final deficit |"
    sep    = "| --- | " + " | --- " * len(hcols) + "| --- | --- |"
    md_lines += [header, sep]

    for policy in policies:
        pname  = policy["name"]
        label  = policy.get("label", pname)
        result = all_results[pname]
        row    = f"| {label} |"
        for si in range(n_stages - 1):
            stage = result["stages"][si]
            cpm   = stage.get("contenders_per_model", {})
            for mname in model_names:
                row += f" {cpm.get(mname, 0)} |"
        final = result["stages"][-1]
        if final["results"]:
            w = final["results"][0]
            row += f" {w['model']} | {w['deficit']:.4f} |"
        else:
            row += " (none) | — |"
        md_lines.append(row)

    md_lines.append("")

    # ------------------------------------------------------------------
    # Per-policy detailed stage tables
    # ------------------------------------------------------------------
    for policy in policies:
        pname  = policy["name"]
        label  = policy.get("label", pname)
        result = all_results[pname]

        md_lines += [f"# Policy: {label}", ""]

        for si, stage in enumerate(result["stages"]):
            n_counts    = stage_n_counts[si]
            token_names = ["INC", "DEC"] + [f"C{i}" for i in range(n_counts)]
            is_final    = (si == n_stages - 1)

            if si == 0:
                n_cont = stage.get("n_contenders", 0)
                cpm    = stage.get("contenders_per_model", {})
                md_lines += [f"## Stage 1 — cap{n_counts}  (→ {n_cont} contenders survive)", ""]
                for mn, cnt in cpm.items():
                    md_lines.append(f"- **{mn}**: {cnt}")
                md_lines.append("")
                rows = [(e["deficit"], e["model"], e["token_map"]) for e in stage["results"]]
                md_lines += _render_table(token_names, rows)
                md_lines.append("")

            elif is_final:
                md_lines += [f"## Stage {si + 1} — cap{n_counts}  (final — no pruning)", ""]
                rows = [
                    (e["deficit"], e["model"], e["token_map"], e.get("prev_deficit", 0.0))
                    for e in stage["results"]
                ]
                md_lines += _render_table_s2(token_names, rows)
                md_lines.append("")

            else:
                n_cont = stage.get("n_contenders", 0)
                cpm    = stage.get("contenders_per_model", {})
                md_lines += [
                    f"## Stage {si + 1} — cap{n_counts}  (→ {n_cont} contenders survive)", ""
                ]
                for mn, cnt in cpm.items():
                    md_lines.append(f"- **{mn}**: {cnt}")
                md_lines.append("")
                rows = [
                    (e["deficit"], e["model"], e["token_map"], e.get("prev_deficit", 0.0))
                    for e in stage["results"]
                ]
                md_lines += _render_table_s2(token_names, rows)
                md_lines.append("")

    output = {
        "timestamp": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "match":     match_dir.name,
        "config":    config,
        "results":   {
            pname: {
                "n_stages": n_stages,
                "stages": [
                    {k: v for k, v in st.items() if k != "results"}
                    | {"n_results": len(st.get("results", []))}
                    for st in policy_stage_results[pname]
                ],
            }
            for pname in [p["name"] for p in policies]
        },
    }
    (match_dir / "results.json").write_text(json.dumps(output, indent=2))
    (match_dir / "results.md").write_text("\n".join(md_lines) + "\n")
    print(f"\nResults written → {match_dir / 'results.json'}")
    print(f"Results written → {match_dir / 'results.md'}")


def run_match(match_dir: Path):
    config_path = match_dir / "config.json"
    if not config_path.exists():
        print(f"No config.json in {match_dir}")
        sys.exit(1)

    config = json.loads(config_path.read_text())
    world  = config["world"]
    mtcfg  = config["matcher"]

    print(f"Match:   {match_dir.name}")
    print(f"Feed:    {world['feed']}  n_counts={world['n_counts']}  "
          f"seq_len={world['seq_len']}  seed={world['seed']}")
    if "models" in config:
        print(f"Models:  {len(config['models'])}")
    print()

    if mtcfg.get("type") == "incremental":
        _run_incremental(match_dir, config)
        results_path = match_dir / "results.json"
        md_path      = match_dir / "results.md"
        print(f"\nResults written → {results_path}")
        print(f"Results written → {md_path}")
        return

    if mtcfg.get("type") == "incremental_topk":
        _run_incremental_topk(match_dir, config)
        return

    if mtcfg.get("type") == "incremental_multistage":
        _run_incremental_multistage(match_dir, config)
        return

    if mtcfg.get("type") == "lateral_detection":
        _run_lateral_detection(match_dir, config)
        return

    if mtcfg.get("type") == "error_structure":
        _run_error_structure(match_dir, config)
        return

    if mtcfg.get("type") == "scorer_robustness":
        _run_scorer_robustness(match_dir, config)
        return

    if mtcfg.get("type") == "retention_sweep":
        _run_retention_sweep(match_dir, config)
        return

    if mtcfg.get("type") == "error_structure_from":
        _run_error_structure_from(match_dir, config)
        return

    if mtcfg.get("type") == "error_structure_explicit":
        _run_error_structure_explicit(match_dir, config)
        return

    model_results = {}

    for entry in config["models"]:
        if isinstance(entry, str):
            weights      = str(ROOT / entry / "weights.pt")
            name         = Path(entry).name
            model_kwargs = dict(weights_path=weights)
        elif "type" in entry:
            name         = entry.get("name", f"{entry['type']}_{entry.get('n_counts', '')}")
            model_kwargs = dict(model=build_model(entry))
        else:
            weights      = str(ROOT / entry["dir"] / "weights.pt")
            name         = entry.get("name", Path(entry["dir"]).name)
            params       = {k: v for k, v in entry.items() if k not in ("dir", "name")}
            model_kwargs = dict(weights_path=weights, model_params=params)

        print(f"  scoring {name} ...", end=" ", flush=True)

        result = match(
            **model_kwargs,
            seq_len       = world["seq_len"],
            seed          = world["seed"],
            n_seeds       = world.get("n_seeds", 1),
            top_k         = mtcfg["top_k"],
            p_read        = world.get("p_read", 0.6),
            n_counts      = world.get("n_counts"),
            embedder_path = world.get("embedder_path"),
            resolver_path = world.get("resolver_path"),
            scorer        = mtcfg.get("scorer", "deficit"),
            scorer_params = mtcfg.get("scorer_params", {}),
            verbose       = False,
        )
        model_results[name] = result
        print("done")

    print()
    print_results(config, model_results)
    print()

    output = {
        "timestamp": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "match":     match_dir.name,
        "config":    config,
        "results":   model_results,
    }

    results_path = match_dir / "results.json"
    results_path.write_text(json.dumps(output, indent=2))
    print(f"Results written → {results_path}")

    md_path = match_dir / "results.md"
    md_path.write_text(build_results_md(config, model_results))
    print(f"Results written → {md_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run_match.py <match_folder>")
        sys.exit(1)

    run_match(Path(sys.argv[1]))
