#!/usr/bin/env python3
"""
Build 3-class colonoscopy dataset (landmark, normal_mucosa, polyp) with center metadata
and leave-one-center-out (LOO) fold splits.

Sources:
  - Kvasir v1 (center: simula)
  - HyperKvasir labeled images (center: simula)
  - Private annotated frames under data/private/{center_id}/labeled/

Output layout:
  data/colonoscopy_3class/
    manifest.json
    folds/
      fold_simula/
        train/ val/ test/
      fold_center_a/
        ...
    all/
      train/ val/ test/   # pooled split for non-LOO runs

Usage:
  python scripts/prepare_colonoscopy_3class.py --output data/colonoscopy_3class
  python scripts/prepare_colonoscopy_3class.py --kvasir-dir data/kvasir --hyperkvasir-dir data/hyperkvasir
"""

from __future__ import annotations

import argparse
import json
import random
import shutil
from collections import defaultdict
from dataclasses import dataclass, asdict
from pathlib import Path

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}
TARGET_CLASSES = ("landmark", "normal_mucosa", "polyp")

# HyperKvasir 23-class -> 3-class (pathologies excluded from article task)
HYPERKVASIR_TO_3CLASS: dict[str, str | None] = {
    "cecum": "landmark",
    "pylorus": "landmark",
    "z-line": "landmark",
    "ileum": "landmark",
    "retroflex-rectum": "landmark",
    "retroflex-stomach": "landmark",
    "polyps": "polyp",
    "dyed-lifted-polyps": "polyp",
    "bbps-0-1": "normal_mucosa",
    "bbps-2-3": "normal_mucosa",
    "hemorrhoids": "normal_mucosa",
    "impacted-stool": "normal_mucosa",
    # Excluded pathologies / procedures (not in 3-class task)
    "barretts": None,
    "barretts-short-segment": None,
    "dyed-resection-margins": None,
    "esophagitis-a": None,
    "esophagitis-b-d": None,
    "ulcerative-colitis-grade-0-1": None,
    "ulcerative-colitis-grade-1": None,
    "ulcerative-colitis-grade-1-2": None,
    "ulcerative-colitis-grade-2": None,
    "ulcerative-colitis-grade-2-3": None,
    "ulcerative-colitis-grade-3": None,
}

# Kvasir 4-class benchmark -> 3-class
KVASIR_TO_3CLASS: dict[str, str | None] = {
    "cecum": "landmark",
    "pylorus": "landmark",
    "polyp": "polyp",
    "ulcer": None,
}


@dataclass
class Sample:
    src: str
    center_id: str
    source: str
    original_class: str
    target_class: str


def _iter_images(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    return [p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_EXTS]


def collect_from_imagefolder(root: Path, center_id: str, source: str, class_map: dict[str, str | None]) -> list[Sample]:
    samples: list[Sample] = []
    for split in ("train", "val", "test"):
        split_dir = root / split
        if not split_dir.is_dir():
            continue
        for cls_dir in split_dir.iterdir():
            if not cls_dir.is_dir():
                continue
            mapped = class_map.get(cls_dir.name)
            if mapped is None:
                continue
            for img in _iter_images(cls_dir):
                samples.append(
                    Sample(
                        src=str(img.resolve()),
                        center_id=center_id,
                        source=source,
                        original_class=cls_dir.name,
                        target_class=mapped,
                    )
                )
    return samples


def collect_private(private_root: Path) -> list[Sample]:
    samples: list[Sample] = []
    if not private_root.is_dir():
        return samples
    for center_dir in sorted(private_root.iterdir()):
        if not center_dir.is_dir():
            continue
        labeled = center_dir / "labeled"
        if not labeled.is_dir():
            continue
        for cls_dir in labeled.iterdir():
            if not cls_dir.is_dir() or cls_dir.name not in TARGET_CLASSES:
                continue
            for img in _iter_images(cls_dir):
                samples.append(
                    Sample(
                        src=str(img.resolve()),
                        center_id=center_dir.name,
                        source="private",
                        original_class=cls_dir.name,
                        target_class=cls_dir.name,
                    )
                )
    return samples


def stratified_split(samples: list[Sample], val_ratio: float, test_ratio: float, seed: int):
    by_class: dict[str, list[Sample]] = defaultdict(list)
    for s in samples:
        by_class[s.target_class].append(s)
    rng = random.Random(seed)
    train, val, test = [], [], []
    for cls, items in by_class.items():
        shuffled = items[:]
        rng.shuffle(shuffled)
        n = len(shuffled)
        n_test = max(1, int(n * test_ratio)) if n >= 3 else (1 if n > 1 else 0)
        n_val = max(1, int(n * val_ratio)) if n >= 3 else (1 if n > 2 else 0)
        n_train = n - n_val - n_test
        if n_train < 1 and n > 0:
            n_train, n_val, n_test = max(1, n - 2), min(1, n - 1), min(1, n - 1)
        train.extend(shuffled[:n_train])
        val.extend(shuffled[n_train : n_train + n_val])
        test.extend(shuffled[n_train + n_val :])
    return train, val, test


def link_samples(out_root: Path, split: str, items: list[Sample]) -> None:
    for i, sample in enumerate(items):
        dst_dir = out_root / split / sample.target_class
        dst_dir.mkdir(parents=True, exist_ok=True)
        src = Path(sample.src)
        dst = dst_dir / f"{sample.center_id}_{sample.target_class}_{split}_{i:05d}{src.suffix.lower()}"
        if dst.exists() or dst.is_symlink():
            continue
        try:
            dst.symlink_to(src)
        except OSError:
            shutil.copy2(src, dst)


def write_fold(fold_root: Path, held_out: str, all_samples: list[Sample], seed: int, val_ratio: float, test_ratio: float):
    train_pool = [s for s in all_samples if s.center_id != held_out]
    test_pool = [s for s in all_samples if s.center_id == held_out]
    train, val, _ = stratified_split(train_pool, val_ratio, test_ratio, seed)
    link_samples(fold_root, "train", train)
    link_samples(fold_root, "val", val)
    link_samples(fold_root, "test", test_pool)


def main() -> None:
    p = argparse.ArgumentParser(description="Prepare 3-class colonoscopy dataset with LOO folds")
    p.add_argument("--output", type=str, default="data/colonoscopy_3class")
    p.add_argument("--kvasir-dir", type=str, default="data/kvasir")
    p.add_argument("--hyperkvasir-dir", type=str, default="data/hyperkvasir")
    p.add_argument("--private-dir", type=str, default="data/private")
    p.add_argument("--val-ratio", type=float, default=0.15)
    p.add_argument("--test-ratio", type=float, default=0.15)
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()

    output = Path(args.output)
    samples: list[Sample] = []
    samples.extend(collect_from_imagefolder(Path(args.kvasir_dir), "simula", "kvasir", KVASIR_TO_3CLASS))
    samples.extend(
        collect_from_imagefolder(
            Path(args.hyperkvasir_dir), "simula", "hyperkvasir", HYPERKVASIR_TO_3CLASS
        )
    )
    samples.extend(collect_private(Path(args.private_dir)))

    if not samples:
        raise SystemExit(
            "No samples found. Run prepare-kvasir / prepare-hyperkvasir first, "
            "or add private data under data/private/{center_id}/labeled/."
        )

    centers = sorted({s.center_id for s in samples})
    counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for s in samples:
        counts[s.center_id][s.target_class] += 1

    # Pooled split (all centers)
    all_root = output / "all"
    train, val, test = stratified_split(samples, args.val_ratio, args.test_ratio, args.seed)
    link_samples(all_root, "train", train)
    link_samples(all_root, "val", val)
    link_samples(all_root, "test", test)

    # LOO folds
    folds_root = output / "folds"
    for center in centers:
        fold_dir = folds_root / f"fold_{center}"
        if fold_dir.exists():
            shutil.rmtree(fold_dir)
        write_fold(fold_dir, center, samples, args.seed, args.val_ratio, args.test_ratio)

    manifest = {
        "target_classes": list(TARGET_CLASSES),
        "centers": centers,
        "counts_by_center": {c: dict(counts[c]) for c in centers},
        "total_samples": len(samples),
        "seed": args.seed,
        "val_ratio": args.val_ratio,
        "test_ratio": args.test_ratio,
        "sources": {
            "kvasir_dir": args.kvasir_dir,
            "hyperkvasir_dir": args.hyperkvasir_dir,
            "private_dir": args.private_dir,
        },
        "folds": [f"fold_{c}" for c in centers],
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2))

    print(f"Prepared {len(samples)} samples across {len(centers)} centers -> {output}")
    print(f"Classes: {TARGET_CLASSES}")
    for c in centers:
        print(f"  {c}: {dict(counts[c])}")
    print(f"LOO folds: {manifest['folds']}")


if __name__ == "__main__":
    main()
