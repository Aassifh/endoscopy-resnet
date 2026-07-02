#!/usr/bin/env python3
"""Inject HyperKvasir B2–B6 JSON results into summary.md and review HTML."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "benchmarks/ml/results"
SUMMARY = RESULTS / "summary.md"
HTML = ROOT / "docs/revue_comparative_architectures_fr.html"
SCI = ROOT / "docs/SCIENTIFIC_REVIEW.md"
PDF = ROOT / "docs/Revue_Comparative_Endoscopie_ResNet.pdf"

RUNS = [
    ("B2", "b2_resnet50_imagenet", "ResNet-50", "ImageNet"),
    ("B3", "b3_seresnet50_scratch", "SE-ResNet-50", "none"),
    ("B4", "b4_seresnet50_imagenet", "SE-ResNet-50", "ImageNet"),
    ("B5", "b5_dualstream_scratch", "Dual-stream", "none"),
    ("B6", "b6_dualstream_imagenet", "Dual-stream", "ImageNet (RGB)"),
]


def load_json(stem: str, split: str) -> dict | None:
    path = RESULTS / f"hyperkvasir_{stem}_{split}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text())


def fmt_pct(x: float) -> str:
    return f"{100 * x:.1f} %".replace(".", ",")


def fmt_f1(x: float) -> str:
    return f"{x:.3f}"


def build_summary_section(rows: list[dict]) -> str:
    lines = [
        "",
        "## HyperKvasir (23 classes) — B2–B6",
        "",
        "**Run date:** 2026-06-17  ",
        "**Dataset:** `data/hyperkvasir/` — 7 484 train / 1 589 val / 1 589 test (stratified, seed 42).  ",
        "**Training:** 15 epochs, batch 16, AdamW lr=1e-3 (scratch) or 1e-4 (ImageNet), img=224.  ",
        "**Selection:** checkpoint with best validation macro-F1.",
        "",
        "| Run | Model | Pretrain | Split | Accuracy | Macro-F1 | Weighted-F1 |",
        "|-----|-------|----------|-------|----------|----------|-------------|",
    ]
    for r in rows:
        lines.append(
            f"| {r['id']} | {r['model']} | {r['pretrain']} | {r['split']} | "
            f"{r['acc']:.3f} | {r['macro_f1']:.3f} | {r['weighted_f1']:.3f} |"
        )
    lines.extend(
        [
            "",
            "### Key takeaways (HyperKvasir)",
            "",
        ]
    )
    test_rows = [r for r in rows if r["split"] == "test"]
    if test_rows:
        best = max(test_rows, key=lambda r: r["macro_f1"])
        lines.append(
            f"1. **Best test macro-F1:** {best['id']} ({best['model']}, {best['pretrain']}) "
            f"— **{best['macro_f1']:.3f}** (acc {best['acc']:.3f})."
        )
        lines.append(
            "2. **Class imbalance** — accuracy can exceed macro-F1 substantially; "
            "macro-F1 remains the primary metric."
        )
        lines.append(
            "3. JSON reports: `hyperkvasir_b2_*` … `hyperkvasir_b6_*` in `benchmarks/ml/results/`."
        )
    lines.append("")
    return "\n".join(lines)


def update_summary(rows: list[dict]) -> None:
    text = SUMMARY.read_text()
    section = build_summary_section(rows)
    marker = "## HyperKvasir (23 classes) — B2–B6"
    if marker in text:
        text = re.sub(
            r"\n## HyperKvasir \(23 classes\) — B2–B6[\s\S]*?(?=\n## |\n---|\Z)",
            "\n" + section.strip() + "\n",
            text,
            count=1,
        )
    else:
        insert_at = text.find("\n---\n\n## Appendix")
        if insert_at == -1:
            text = text.rstrip() + "\n" + section
        else:
            text = text[:insert_at] + "\n" + section + text[insert_at:]
    SUMMARY.write_text(text)


def update_html(rows: list[dict]) -> None:
    html = HTML.read_text()

    # Abstract results sentence
    if rows:
        test = {r["id"]: r for r in rows if r["split"] == "test"}
        parts = []
        for rid in ["B2", "B3", "B4", "B5", "B6"]:
            if rid in test:
                r = test[rid]
                parts.append(f"{rid} {fmt_pct(r['acc'])} / F1 {fmt_f1(r['macro_f1'])}")
        results_text = (
            f"Sur <strong>HyperKvasir (23 classes)</strong>, les campagnes B2–B6 donnent "
            f"(test)&nbsp;: {', '.join(parts)}."
        )
        html = re.sub(
            r"Les campagnes HyperKvasir B2–B6 sont <em>en cours</em>[^<]*</p>",
            results_text + "</p>",
            html,
            count=1,
        )
        html = html.replace(
            "Cette revue v1.0 intègre l'intégralité du plan méthodologique&nbsp;; "
            "la v1.1 intégrera les résultats HyperKvasir finaux.",
            "Cette revue v1.1 intègre les résultats HyperKvasir B2–B6 finaux.",
        )

    # Table rows
    table_rows = []
    for run_id, stem, model, pretrain in RUNS:
        for split in ("val", "test"):
            data = load_json(stem, split)
            if data:
                table_rows.append(
                    f"  <tr><td>{run_id}</td><td>{model}</td><td>{pretrain}</td><td>{split}</td>"
                    f"<td>{fmt_pct(data['accuracy'])}</td>"
                    f"<td>{fmt_f1(data['macro_f1'])}</td>"
                    f"<td>{fmt_f1(data['weighted_f1'])}</td></tr>"
                )
            else:
                table_rows.append(
                    f"  <tr><td>{run_id}</td><td>{model}</td><td>{pretrain}</td><td>{split}</td>"
                    f'<td colspan="3"><em>À compléter post-benchmark</em></td></tr>'
                )

    html = re.sub(
        r"(<p class=\"caption\">Tableau 6 — Résultats HyperKvasir B2–B6 \(placeholders\)\.</p>\s*"
        r"<table>[\s\S]*?</table>)",
        lambda m: m.group(0).split("</tr>", 1)[0] + "</tr>\n" + "\n".join(table_rows) + "\n</table>",
        html,
        count=1,
    )
    html = html.replace(
        "<p class=\"caption\">Tableau 6 — Résultats HyperKvasir B2–B6 (placeholders).</p>",
        "<p class=\"caption\">Tableau 6 — Résultats HyperKvasir B2–B6 (test/val).</p>",
    )

    # Remove placeholder note
    html = re.sub(
        r'<div class="placeholder-note">[\s\S]*?</div>\s*',
        "",
        html,
        count=1,
    )

    # HyperKvasir sample images
    samples = [
        ("hk_landmark_cecum.jpg", "cecum", "Repère anatomique"),
        ("hk_polyp.jpg", "polyps", "Polype"),
        ("hk_colitis.jpg", "ulcerative-colitis-grade-2", "Colite ulcéreuse grade 2"),
        ("hk_esophagitis.jpg", "esophagitis-a", "Œsophagite grade A"),
    ]
    sample_html = ""
    for fname, code, label in samples:
        path = f"assets/pdf_samples/hyperkvasir/{fname}"
        if (ROOT / "docs" / path).exists():
            sample_html += f"""
  <div class="sample-card">
    <img src="{path}" alt="{label}" />
    <div class="sample-meta"><code>{code}</code><br/>{label}</div>
  </div>"""

    html = re.sub(
        r'(<p class="caption">Figure 2 — Placeholders HyperKvasir[\s\S]*?<div class="sample-grid">)[\s\S]*?(</div>\s*\n\n<h2>4\.)',
        r"\1" + sample_html + r"\n\2",
        html,
        count=1,
    )
    html = html.replace(
        "Figure 2 — Placeholders HyperKvasir par groupe clinique (à remplacer post-téléchargement).",
        "Figure 2 — Échantillons HyperKvasir par groupe clinique.",
    )

    # Implementation status table
    for old, new in [
        ("Planifié</td></tr>\n  <tr><td><strong>2</strong>", "Terminé</td></tr>\n  <tr><td><strong>2</strong>"),
        ("Planifié</td></tr>\n  <tr><td><strong>3</strong>", "Terminé</td></tr>\n  <tr><td><strong>3</strong>"),
        ("Planifié</td></tr>\n  <tr><td><strong>4</strong>", "Terminé</td></tr>\n  <tr><td><strong>4</strong>"),
    ]:
        html = html.replace(old, new, 1)

    HTML.write_text(html)


def update_scientific_review(rows: list[dict]) -> None:
    if not SCI.exists():
        return
    text = SCI.read_text()
    test = [r for r in rows if r["split"] == "test"]
    if not test:
        return
    block = "\n### 7.6 HyperKvasir benchmark results (B2–B6)\n\n"
    block += "| Run | Model | Pretrain | Test acc | Test macro-F1 | Test weighted-F1 |\n"
    block += "|-----|-------|----------|----------|---------------|------------------|\n"
    for r in test:
        block += (
            f"| {r['id']} | {r['model']} | {r['pretrain']} | "
            f"{r['acc']:.3f} | {r['macro_f1']:.3f} | {r['weighted_f1']:.3f} |\n"
        )
    block += "\n"
    if "### 7.6 HyperKvasir benchmark results" in text:
        text = re.sub(
            r"\n### 7\.6 HyperKvasir benchmark results[\s\S]*?(?=\n### |\n## |\Z)",
            block.rstrip(),
            text,
            count=1,
        )
    else:
        text = text.rstrip() + block
    SCI.write_text(text)


def generate_pdf() -> None:
    chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    if not Path(chrome).exists():
        print("Chrome not found; skip PDF generation", file=sys.stderr)
        return
    html_uri = HTML.resolve().as_uri()
    subprocess.run(
        [
            chrome,
            "--headless",
            "--disable-gpu",
            "--no-pdf-header-footer",
            f"--print-to-pdf={PDF}",
            html_uri,
        ],
        check=True,
        capture_output=True,
    )
    print(f"PDF written: {PDF}")


def main() -> None:
    rows: list[dict] = []
    missing = []
    for run_id, stem, model, pretrain in RUNS:
        for split in ("val", "test"):
            data = load_json(stem, split)
            if data is None:
                missing.append(f"{stem}_{split}")
                continue
            rows.append(
                {
                    "id": run_id,
                    "model": model,
                    "pretrain": pretrain,
                    "split": split,
                    "acc": data["accuracy"],
                    "macro_f1": data["macro_f1"],
                    "weighted_f1": data["weighted_f1"],
                }
            )

    if missing:
        print(f"Missing {len(missing)} JSON files: {', '.join(missing[:5])}…")
        if len(rows) < 4:
            sys.exit(1)

    update_summary(rows)
    update_html(rows)
    update_scientific_review(rows)
    generate_pdf()
    print(f"Updated {SUMMARY}, {HTML}, {SCI}")


if __name__ == "__main__":
    main()
