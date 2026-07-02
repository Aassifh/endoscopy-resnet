#!/usr/bin/env python3
"""
Download HyperKvasir unlabeled still images (~99k) for CNN-JEPA pretraining.

Usage:
  python scripts/download_hyperkvasir_unlabeled.py --output data/jepa_frames/hyperkvasir_unlabeled
  python scripts/download_hyperkvasir_unlabeled.py --skip-download --raw-dir data/raw/hyper-kvasir-unlabeled-images
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import zipfile
from pathlib import Path

UNLABELED_URL = (
    "https://datasets.simula.no/downloads/hyper-kvasir/hyper-kvasir-unlabeled-images.zip"
)
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}


def download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 100_000_000:
        print(f"Using existing archive: {dest}")
        return
    print(f"Downloading {url}")
    subprocess.run(
        ["curl", "-L", "--fail", "--continue-at", "-", "-o", str(dest), url],
        check=True,
    )


def find_unlabeled_root(extract_dir: Path) -> Path:
    for candidate in [
        extract_dir / "unlabeled-images",
        extract_dir / "unlabeled",
        extract_dir / "labeled-images" / "unlabeled",
        extract_dir,
    ]:
        if candidate.is_dir() and any(candidate.rglob("*.jpg")):
            return candidate
    for root in extract_dir.rglob("unlabeled*"):
        if root.is_dir() and any(root.rglob("*.jpg")):
            return root
    raise FileNotFoundError(f"No unlabeled image tree found under {extract_dir}")


def collect_images(root: Path) -> list[Path]:
    return sorted(
        p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_EXTS
    )


def materialize(images: list[Path], output: Path, max_link: int = 0) -> int:
    output.mkdir(parents=True, exist_ok=True)
    if max_link > 0:
        images = images[:max_link]
    for i, src in enumerate(images):
        dst = output / f"unlabeled_{i:06d}{src.suffix.lower()}"
        if dst.exists() or dst.is_symlink():
            continue
        try:
            dst.symlink_to(src.resolve())
        except OSError:
            shutil.copy2(src, dst)
    return len(images)


def main() -> None:
    p = argparse.ArgumentParser(description="Prepare HyperKvasir unlabeled stills for JEPA")
    p.add_argument("--output", type=str, default="data/jepa_frames/hyperkvasir_unlabeled")
    p.add_argument("--skip-download", action="store_true")
    p.add_argument("--raw-dir", type=str, default="")
    p.add_argument("--max-images", type=int, default=0, help="Cap symlinked images (0 = all)")
    args = p.parse_args()

    output = Path(args.output)
    raw_base = Path(args.raw_dir) if args.raw_dir else Path("data/raw")
    zip_path = raw_base / "hyper-kvasir-unlabeled-images.zip"
    extract_dir = raw_base / "hyper-kvasir-unlabeled-images"

    if not args.skip_download:
        download(UNLABELED_URL, zip_path)

    if not zip_path.exists():
        raise SystemExit(f"Archive missing: {zip_path}")

    marker = extract_dir / ".extracted"
    if not marker.exists():
        print(f"Extracting {zip_path.name} …")
        extract_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(extract_dir)
        marker.write_text("ok")

    root = find_unlabeled_root(extract_dir)
    images = collect_images(root)
    if not images:
        raise SystemExit(f"No images under {root}")

    if output.exists():
        shutil.rmtree(output)
    count = materialize(images, output, args.max_images)
    meta = {
        "source": "hyperkvasir_unlabeled_simula",
        "archive": str(zip_path),
        "root": str(root),
        "total_in_archive": len(images),
        "materialized": count,
        "output": str(output),
    }
    (output / "manifest.json").write_text(json.dumps(meta, indent=2))
    print(f"Prepared {count} unlabeled frames -> {output.resolve()}")


if __name__ == "__main__":
    main()
