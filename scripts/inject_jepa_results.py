#!/usr/bin/env python3
"""Aggregate CNN-JEPA campaign JSON results into summary.md."""

from __future__ import annotations

import json
from pathlib import Path

RESULTS = Path("benchmarks/ml/results")
OUT_MD = RESULTS / "jepa_summary.md"


def load_macro_f1(path: Path) -> float | None:
    if not path.exists():
        return None
    data = json.loads(path.read_text())
    return data.get("macro_f1")


def polyp_recall(path: Path) -> float | None:
    if not path.exists():
        return None
    data = json.loads(path.read_text())
    names = data.get("class_names", [])
    cm = data.get("confusion_matrix")
    if not cm or "polyp" not in names:
        return None
    idx = names.index("polyp")
    row = cm[idx]
    total = sum(row)
    return row[idx] / total if total else 0.0


def main() -> None:
    runs = sorted(RESULTS.glob("C*_fold_*_test.json"))
    rows: list[dict] = []
    for path in runs:
        run_id = path.stem.replace("_test", "")
        rows.append({
            "run_id": run_id,
            "macro_f1": load_macro_f1(path),
            "polyp_recall": polyp_recall(path),
        })

    c10 = RESULTS / "C10_summary_test.json"
    c10_data = json.loads(c10.read_text()) if c10.exists() else {}

    lines = [
        "# CNN-JEPA Article Benchmark Results",
        "",
        "| Run ID | Macro-F1 | Polyp recall |",
        "|--------|----------|--------------|",
    ]
    for row in rows:
        mf1 = f"{row['macro_f1']:.4f}" if row["macro_f1"] is not None else "—"
        pr = f"{row['polyp_recall']:.4f}" if row["polyp_recall"] is not None else "—"
        lines.append(f"| {row['run_id']} | {mf1} | {pr} |")

    if c10_data:
        lines.extend([
            "",
            f"**C10 LOO mean macro-F1:** {c10_data.get('macro_f1_mean', 0):.4f} "
            f"({c10_data.get('folds', 0)} folds)",
        ])

    OUT_MD.write_text("\n".join(lines) + "\n")
    print(OUT_MD.read_text())


if __name__ == "__main__":
    main()
