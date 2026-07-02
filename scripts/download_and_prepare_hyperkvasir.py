#!/usr/bin/env python3
"""
Download HyperKvasir labeled images and build train/val/test ImageFolder layout.

23-class taxonomy (official Simula folder names). No histological polyp subtypes.

Usage:
  python scripts/download_and_prepare_hyperkvasir.py --output data/hyperkvasir
  python scripts/download_and_prepare_hyperkvasir.py --skip-download --raw-dir data/raw/hyper-kvasir-labeled-images
"""

from __future__ import annotations

import argparse
import json
import random
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

HYPERKVASIR_URL = "https://datasets.simula.no/downloads/hyper-kvasir/hyper-kvasir-labeled-images.zip"
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}


def download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 50_000_000:
        print(f"Using existing archive: {dest}")
        return
    print(f"Downloading {url}")
    subprocess.run(
        ["curl", "-L", "--fail", "--continue-at", "-", "-o", str(dest), url],
        check=True,
    )


def find_labeled_root(extract_dir: Path) -> Path:
    """Locate labeled-images root (nested upper/lower GI layout)."""
    for candidate in [
        extract_dir / "labeled-images",
        extract_dir,
    ]:
        if candidate.is_dir() and any(candidate.rglob("*.jpg")):
            return candidate
    for root in extract_dir.rglob("labeled-images"):
        if root.is_dir():
            return root
    raise FileNotFoundError(f"No HyperKvasir labeled-images tree found under {extract_dir}")


def collect_images(dataset_root: Path) -> dict[str, list[Path]]:
    """Collect images grouped by leaf class folder name."""
    by_class: dict[str, list[Path]] = {}
    for img in dataset_root.rglob("*"):
        if not img.is_file() or img.suffix.lower() not in IMAGE_EXTS:
            continue
        cls = img.parent.name
        by_class.setdefault(cls, []).append(img)
    if len(by_class) < 20:
        raise FileNotFoundError(
            f"Expected ~23 classes, found {len(by_class)} under {dataset_root}."
        )
    for cls, files in sorted(by_class.items()):
        print(f"  {cls}: {len(files)}")
    return by_class


def split_files(files: list[Path], val_ratio: float, test_ratio: float, seed: int):
    rng = random.Random(seed)
    shuffled = files[:]
    rng.shuffle(shuffled)
    n = len(shuffled)
    n_test = max(1, int(n * test_ratio))
    n_val = max(1, int(n * val_ratio))
    n_train = n - n_val - n_test
    if n_train < 1:
        raise ValueError(f"Not enough images ({n}) for split.")
    return shuffled[:n_train], shuffled[n_train : n_train + n_val], shuffled[n_train + n_val :]


def materialize(output: Path, split: str, cls: str, files: list[Path]) -> None:
    out_dir = output / split / cls
    out_dir.mkdir(parents=True, exist_ok=True)
    for i, src in enumerate(files):
        dst = out_dir / f"{cls}_{split}_{i:04d}{src.suffix.lower()}"
        if dst.exists() or dst.is_symlink():
            continue
        try:
            dst.symlink_to(src.resolve())
        except OSError:
            shutil.copy2(src, dst)


def main() -> None:
    p = argparse.ArgumentParser(description="Download HyperKvasir and prepare ImageFolder splits")
    p.add_argument("--output", type=str, default="data/hyperkvasir")
    p.add_argument("--skip-download", action="store_true")
    p.add_argument("--raw-dir", type=str, default="")
    p.add_argument("--val-ratio", type=float, default=0.15)
    p.add_argument("--test-ratio", type=float, default=0.15)
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()

    output = Path(args.output)
    raw_base = Path(args.raw_dir) if args.raw_dir else Path("data/raw")
    zip_path = raw_base / "hyper-kvasir-labeled-images.zip"
    extract_dir = raw_base / "hyper-kvasir-labeled-images"

    if not args.skip_download:
        download(HYPERKVASIR_URL, zip_path)

    if not zip_path.exists():
        print(f"Archive missing: {zip_path}", file=sys.stderr)
        sys.exit(1)

    marker = extract_dir / ".extracted"
    if not marker.exists():
        print(f"Extracting {zip_path.name} …")
        extract_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(extract_dir)
        marker.write_text("ok")

    dataset_root = find_labeled_root(extract_dir)
    print(f"Dataset root: {dataset_root}")

    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)

    print("Collecting images …")
    by_class = collect_images(dataset_root)
    classes = sorted(by_class.keys())
    print(f"\nTotal classes: {len(classes)}")

    counts: dict[str, dict[str, int]] = {"train": {}, "val": {}, "test": {}}
    for i, (cls, files) in enumerate(by_class.items()):
        train, val, test = split_files(files, args.val_ratio, args.test_ratio, args.seed + i)
        materialize(output, "train", cls, train)
        materialize(output, "val", cls, val)
        materialize(output, "test", cls, test)
        counts["train"][cls] = len(train)
        counts["val"][cls] = len(val)
        counts["test"][cls] = len(test)

    meta = {
        "source": "hyperkvasir_labeled_simula",
        "seed": args.seed,
        "num_classes": len(classes),
        "classes": classes,
        "counts": counts,
    }
    (output / "class_counts.json").write_text(json.dumps(meta, indent=2))
    lines = [f"source={meta['source']}", f"seed={args.seed}", f"num_classes={len(classes)}"]
    for split in ("train", "val", "test"):
        lines.append(f"{split}_total={sum(counts[split].values())}")
    (output / "benchmark_meta.txt").write_text("\n".join(lines) + "\n")

    print(f"\nDone: {output.resolve()}")
    print(f"Classes: {len(classes)}, train={sum(counts['train'].values())}, "
          f"val={sum(counts['val'].values())}, test={sum(counts['test'].values())}")


if __name__ == "__main__":
    main()
