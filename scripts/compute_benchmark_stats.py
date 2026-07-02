#!/usr/bin/env python3
"""Bootstrap significance and mean±std for benchmark JSON results."""

from __future__ import annotations

import argparse
import json
import random
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "benchmarks/ml/results"
SEEDS_FILE = ROOT / "benchmarks/ml/seeds.json"


def load_seeds() -> list[int]:
    if SEEDS_FILE.is_file():
        return json.loads(SEEDS_FILE.read_text())["seeds"]
    return [42]


def result_paths(run_id: str, fold: str = "fold_simula") -> list[Path]:
    paths: list[Path] = []
    for seed in load_seeds():
        if seed == 42:
            legacy = RESULTS / f"{run_id}_{fold}_test.json"
            if legacy.is_file():
                paths.append(legacy)
                continue
        p = RESULTS / f"{run_id}_{fold}_seed{seed}_test.json"
        if p.is_file():
            paths.append(p)
    return paths


def polyp_recall(data: dict) -> float | None:
    names = data.get("class_names", [])
    cm = data.get("confusion_matrix")
    if not cm:
        return None
    for cls in ("polyp", "polyps"):
        if cls in names:
            idx = names.index(cls)
            row = cm[idx]
            total = sum(row)
            return row[idx] / total if total else 0.0
    return None


def load_metric(run_id: str, metric: str) -> list[float]:
    values: list[float] = []
    for path in result_paths(run_id):
        data = json.loads(path.read_text())
        if metric == "macro_f1":
            values.append(float(data["macro_f1"]))
        elif metric == "polyp_recall":
            v = polyp_recall(data)
            if v is not None:
                values.append(v)
    return values


def bootstrap_diff(a: list[float], b: list[float], n: int = 5000, seed: int = 0) -> dict:
    if len(a) < 2 or len(b) < 2:
        return {"mean_a": statistics.mean(a) if a else None, "mean_b": statistics.mean(b) if b else None, "p_two_sided": None}
    rng = random.Random(seed)
    n_pairs = min(len(a), len(b))
    diffs = []
    for _ in range(n):
        idx = [rng.randrange(n_pairs) for _ in range(n_pairs)]
        diffs.append(statistics.mean([a[i] for i in idx]) - statistics.mean([b[i] for i in idx]))
    diffs.sort()
    obs = statistics.mean(a[:n_pairs]) - statistics.mean(b[:n_pairs])
    lo = sum(1 for d in diffs if d <= 0) / n
    hi = sum(1 for d in diffs if d >= 0) / n
    p = 2 * min(lo, hi)
    return {
        "mean_a": statistics.mean(a),
        "mean_b": statistics.mean(b),
        "mean_diff": obs,
        "p_two_sided": p,
        "ci95_low": diffs[int(0.025 * n)],
        "ci95_high": diffs[int(0.975 * n)],
    }


def fmt_stats(values: list[float]) -> str:
    if not values:
        return "n/a"
    if len(values) == 1:
        return f"{values[0]:.4f}"
    return f"{statistics.mean(values):.4f} ± {statistics.stdev(values):.4f} (n={len(values)})"


def main() -> None:
    p = argparse.ArgumentParser(description="Benchmark stats and significance")
    p.add_argument("--compare", nargs=2, metavar=("RUN_A", "RUN_B"), action="append", default=[])
    p.add_argument("--metric", default="macro_f1", choices=("macro_f1", "polyp_recall"))
    p.add_argument("--list", nargs="*", default=["C0", "C1", "C2", "C3", "C4", "C5"])
    args = p.parse_args()

    print(f"Seeds: {load_seeds()}\n")
    print(f"{'Run':<6} {args.metric}")
    print("-" * 40)
    for run in args.list:
        vals = load_metric(run, args.metric)
        print(f"{run:<6} {fmt_stats(vals)}")

    pairs = args.compare or [("C1", "C4"), ("B6", "B2"), ("C2", "C4")]
    print("\nPairwise bootstrap (two-sided p, same seed index when paired):")
    for a, b in pairs:
        va = load_metric(a, args.metric)
        vb = load_metric(b, args.metric)
        stats = bootstrap_diff(va, vb)
        print(f"  {a} vs {b}: diff={stats.get('mean_diff', 'n/a')}, p={stats.get('p_two_sided', 'n/a')}")


if __name__ == "__main__":
    main()
