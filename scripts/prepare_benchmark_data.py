#!/usr/bin/env python3
"""
Prepare benchmark dataset for endoscopy-resnet.

Maps four Kvasir-style classes (cecum, pylorus, polyp, ulcer) into train/val/test
ImageFolder layout. Uses procedurally generated endoscopy-like images when the
public Kvasir archive is unavailable — use scripts/download_and_prepare_kvasir.py instead
(Simula URLs moved to /downloads/kvasir/...; old /downloads/kvasir-dataset.zip paths 404).

Usage:
  python scripts/prepare_benchmark_data.py --output data --images-per-class 120
"""

from __future__ import annotations

import argparse
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


CLASSES = ["cecum", "pylorus", "polyp", "ulcer"]

# Visual signatures per class (RGB-ish mucosa tones + structure)
CLASS_STYLE = {
    "cecum": {"base": (140, 70, 90), "accent": (80, 160, 100), "shape": "folds"},
    "pylorus": {"base": (150, 90, 70), "accent": (200, 140, 60), "shape": "ring"},
    "polyp": {"base": (130, 60, 80), "accent": (220, 180, 160), "shape": "bump"},
    "ulcer": {"base": (120, 50, 70), "accent": (230, 230, 200), "shape": "lesion"},
}


def _noise_layer(w: int, h: int, rng: random.Random) -> Image.Image:
    n = rng.randint(-25, 25)
    base = np.array([100 + n, 40 + n // 2, 60 + n // 3], dtype=np.float32)
    arr = np.clip(base + np.random.randint(-20, 21, size=(h, w, 3)), 0, 255).astype(np.uint8)
    return Image.fromarray(arr)


def render_image(cls: str, size: int, rng: random.Random) -> Image.Image:
    style = CLASS_STYLE[cls]
    img = _noise_layer(size, size, rng)
    img = Image.blend(img, Image.new("RGB", (size, size), style["base"]), 0.55)
    draw = ImageDraw.Draw(img)
    cx, cy = size // 2 + rng.randint(-20, 20), size // 2 + rng.randint(-20, 20)

    if style["shape"] == "folds":
        for i in range(5):
            y = cy - 80 + i * 35 + rng.randint(-5, 5)
            draw.arc([cx - 120, y, cx + 120, y + 60], 0, 180, fill=style["accent"], width=4)
    elif style["shape"] == "ring":
        r = 55 + rng.randint(-8, 8)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=style["accent"], width=6)
        draw.ellipse([cx - r // 2, cy - r // 2, cx + r // 2, cy + r // 2], fill=style["base"])
    elif style["shape"] == "bump":
        r = 35 + rng.randint(0, 15)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=style["accent"])
        draw.ellipse([cx - r + 8, cy - r + 8, cx + r - 8, cy + r - 8], fill=style["base"])
    elif style["shape"] == "lesion":
        r = 45 + rng.randint(0, 20)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=style["accent"])
        draw.ellipse([cx - r // 3, cy - r // 3, cx + r // 3, cy + r // 3], fill=(180, 40, 50))

    if rng.random() > 0.5:
        img = img.filter(ImageFilter.GaussianBlur(radius=rng.uniform(0.3, 1.2)))
    return img


def write_split(root: Path, split: str, counts: dict[str, int], size: int, seed: int) -> None:
    rng = random.Random(seed)
    for cls in CLASSES:
        out_dir = root / split / cls
        out_dir.mkdir(parents=True, exist_ok=True)
        for i in range(counts[cls]):
            img = render_image(cls, size, rng)
            img.save(out_dir / f"{cls}_{split}_{i:04d}.jpg", quality=90)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=str, default="data")
    p.add_argument("--images-per-class", type=int, default=120)
    p.add_argument("--val-ratio", type=float, default=0.15)
    p.add_argument("--test-ratio", type=float, default=0.15)
    p.add_argument("--size", type=int, default=256)
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()

    n = args.images_per_class
    n_val = max(1, int(n * args.val_ratio))
    n_test = max(1, int(n * args.test_ratio))
    n_train = n - n_val - n_test

    root = Path(args.output)
    counts_train = {c: n_train for c in CLASSES}
    counts_val = {c: n_val for c in CLASSES}
    counts_test = {c: n_test for c in CLASSES}

    print(f"Generating benchmark data under {root.resolve()}")
    print(f"  train: {n_train}/class  val: {n_val}/class  test: {n_test}/class")
    print("  Note: procedural Kvasir-proxy images (Simula Kvasir zip unavailable)")

    write_split(root, "train", counts_train, args.size, args.seed)
    write_split(root, "val", counts_val, args.size, args.seed + 1)
    write_split(root, "test", counts_test, args.size, args.seed + 2)

    meta = root / "benchmark_meta.txt"
    meta.write_text(
        "source=synthetic_kvasir_proxy\n"
        f"seed={args.seed}\n"
        f"train_per_class={n_train}\n"
        f"val_per_class={n_val}\n"
        f"test_per_class={n_test}\n"
        "classes=" + ",".join(CLASSES) + "\n"
    )
    print(f"Done. Metadata: {meta}")


if __name__ == "__main__":
    main()
