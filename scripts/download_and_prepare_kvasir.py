#!/usr/bin/env python3
"""
Download real Kvasir data from Simula and build train/val/test ImageFolder layout.

Why synthetic data was used initially:
  Old guessed URLs like datasets.simula.no/downloads/kvasir-dataset.zip return 404.
  Current official paths (2026) live under /downloads/kvasir/...

Official sources (research use only):
  Kvasir v1: https://datasets.simula.no/downloads/kvasir/kvasir-dataset.zip   (~1.2 GB)
  Kvasir v2: https://datasets.simula.no/downloads/kvasir/kvasir-dataset-v2.zip (~2.3 GB)
  Kvasir v3: Dropbox link on https://datasets.simula.no/kvasir/
  HyperKvasir labeled images: .../hyper-kvasir/hyper-kvasir-labeled-images.zip (~3.9 GB)

Usage:
  python scripts/download_and_prepare_kvasir.py --output data/kvasir
  python scripts/download_and_prepare_kvasir.py --output data/kvasir --skip-download \\
      --raw-dir data/raw/kvasir-dataset
"""

from __future__ import annotations

import argparse
import random
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

# Kvasir v1/v2 folder names -> our 4-class benchmark taxonomy
KVASIR_CLASS_MAP: dict[str, str] = {
    "normal-cecum": "cecum",
    "cecum": "cecum",
    "normal-pylorus": "pylorus",
    "pylorus": "pylorus",
    "polyps": "polyp",
    "polyp": "polyp",
    "ulcerative-colitis": "ulcer",
    "ulcerative_colitis": "ulcer",
}

KVASIR_V1_URL = "https://datasets.simula.no/downloads/kvasir/kvasir-dataset.zip"
KVASIR_V2_URL = "https://datasets.simula.no/downloads/kvasir/kvasir-dataset-v2.zip"
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}


def download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 10_000_000:
        print(f"Using existing archive: {dest}")
        return
    print(f"Downloading {url}")
    print(f"  -> {dest}")
    # curl avoids Python SSL cert issues on some macOS/Pixi setups
    subprocess.run(
        ["curl", "-L", "--fail", "--continue-at", "-", "-o", str(dest), url],
        check=True,
    )
    print()


def find_dataset_root(extract_dir: Path) -> Path:
    for root in [extract_dir, *extract_dir.rglob("*")]:
        if not root.is_dir():
            continue
        subdirs = {d.name.lower() for d in root.iterdir() if d.is_dir()}
        if subdirs & set(KVASIR_CLASS_MAP.keys()):
            return root
    raise FileNotFoundError(
        f"Could not locate Kvasir class folders under {extract_dir}. "
        f"Expected one of: {sorted(KVASIR_CLASS_MAP)}"
    )


def extract(zip_path: Path, extract_dir: Path) -> Path:
    print(f"Extracting {zip_path.name} …")
    extract_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(extract_dir)
    root = find_dataset_root(extract_dir)
    print(f"  Dataset root: {root}")
    return root


def collect_images(dataset_root: Path) -> dict[str, list[Path]]:
    by_class: dict[str, list[Path]] = {v: [] for v in set(KVASIR_CLASS_MAP.values())}
    for folder in sorted(dataset_root.iterdir()):
        if not folder.is_dir():
            continue
        target = KVASIR_CLASS_MAP.get(folder.name.lower())
        if target is None:
            continue
        for img in folder.rglob("*"):
            if img.is_file() and img.suffix.lower() in IMAGE_EXTS:
                by_class[target].append(img)
    missing = [c for c, files in by_class.items() if not files]
    if missing:
        raise FileNotFoundError(
            f"No images found for classes {missing} under {dataset_root}. "
            "Check archive version or CLASS_MAP."
        )
    for cls, files in by_class.items():
        print(f"  {cls}: {len(files)} images")
    return by_class


def split_files(
    files: list[Path],
    val_ratio: float,
    test_ratio: float,
    seed: int,
) -> tuple[list[Path], list[Path], list[Path]]:
    rng = random.Random(seed)
    shuffled = files[:]
    rng.shuffle(shuffled)
    n = len(shuffled)
    n_test = max(1, int(n * test_ratio))
    n_val = max(1, int(n * val_ratio))
    n_train = n - n_val - n_test
    if n_train < 1:
        raise ValueError(f"Not enough images ({n}) for train/val/test split.")
    train = shuffled[:n_train]
    val = shuffled[n_train : n_train + n_val]
    test = shuffled[n_train + n_val :]
    return train, val, test


def materialize(output: Path, split: str, cls: str, files: list[Path]) -> None:
    out_dir = output / split / cls
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for i, src in enumerate(files):
        dst = out_dir / f"{cls}_{split}_{i:04d}{src.suffix.lower()}"
        shutil.copy2(src, dst)


def write_meta(output: Path, source: str, counts: dict[str, dict[str, int]], seed: int) -> None:
    lines = [
        f"source={source}",
        f"seed={seed}",
        "classes=cecum,pylorus,polyp,ulcer",
    ]
    for split in ("train", "val", "test"):
        for cls in ("cecum", "pylorus", "polyp", "ulcer"):
            lines.append(f"{split}_{cls}={counts[split][cls]}")
    (output / "benchmark_meta.txt").write_text("\n".join(lines) + "\n")


def main() -> None:
    p = argparse.ArgumentParser(description="Download Kvasir and prepare ImageFolder splits")
    p.add_argument("--output", type=str, default="data/kvasir")
    p.add_argument("--version", choices=["v1", "v2"], default="v1")
    p.add_argument("--skip-download", action="store_true")
    p.add_argument("--raw-dir", type=str, default="")
    p.add_argument("--val-ratio", type=float, default=0.15)
    p.add_argument("--test-ratio", type=float, default=0.15)
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()

    output = Path(args.output)
    raw_base = Path(args.raw_dir) if args.raw_dir else Path("data/raw")

    url = KVASIR_V1_URL if args.version == "v1" else KVASIR_V2_URL
    zip_name = "kvasir-dataset.zip" if args.version == "v1" else "kvasir-dataset-v2.zip"
    zip_path = raw_base / zip_name
    extract_dir = raw_base / zip_path.stem

    if not args.skip_download:
        download(url, zip_path)

    if not zip_path.exists():
        print(f"Archive missing: {zip_path}. Run without --skip-download.", file=sys.stderr)
        sys.exit(1)

    marker = extract_dir / ".extracted"
    if not marker.exists():
        dataset_root = extract(zip_path, extract_dir)
        marker.write_text("ok")
    else:
        dataset_root = find_dataset_root(extract_dir)
        print(f"Using extracted data: {dataset_root}")

    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)

    print("Collecting images …")
    by_class = collect_images(dataset_root)

    counts: dict[str, dict[str, int]] = {"train": {}, "val": {}, "test": {}}
    for i, (cls, files) in enumerate(sorted(by_class.items())):
        train, val, test = split_files(files, args.val_ratio, args.test_ratio, args.seed + i)
        materialize(output, "train", cls, train)
        materialize(output, "val", cls, val)
        materialize(output, "test", cls, test)
        counts["train"][cls] = len(train)
        counts["val"][cls] = len(val)
        counts["test"][cls] = len(test)

    source = f"kvasir_{args.version}_simula"
    write_meta(output, source, counts, args.seed)

    print(f"\nDone. Real Kvasir layout: {output.resolve()}")
    print(f"Metadata: {output / 'benchmark_meta.txt'}")
    print("\nNext:")
    print(f"  pixi run train -- --data-dir {output} --epochs 15 --output checkpoints/kvasir_baseline.pt")
    print(f"  pixi run tune -- --data-dir {output} --trials 12 --epochs-per-trial 8")


if __name__ == "__main__":
    main()
