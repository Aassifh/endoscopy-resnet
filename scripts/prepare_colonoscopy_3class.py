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
import csv
import json
import random
import re
import shutil
from collections import defaultdict
from dataclasses import dataclass, asdict
from pathlib import Path

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}
TARGET_CLASSES = ("landmark", "normal_mucosa", "polyp")
DEFAULT_HK_LABELS_CSV = (
    Path("data/raw/hyper-kvasir-labeled-images/labeled-images/image-labels.csv")
)
FRAME_GROUP_RE = re.compile(r"^(.+)_\d{6}$")

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
    group_id: str


def load_hyperkvasir_group_map(labels_csv: Path) -> dict[str, str]:
    """Map HyperKvasir image stem -> procedure group (Video file column)."""
    mapping: dict[str, str] = {}
    if not labels_csv.is_file():
        return mapping
    with labels_csv.open(newline="") as handle:
        for row in csv.DictReader(handle):
            image_id = row["Video file"].strip()
            mapping[image_id] = image_id
    return mapping


def infer_group_id(sample: Sample, hk_groups: dict[str, str]) -> str:
    src = Path(sample.src).resolve()
    stem = src.stem
    if sample.source == "hyperkvasir":
        return hk_groups.get(stem, f"hyperkvasir:{stem}")
    if sample.source == "kvasir":
        return f"kvasir:{stem}"
    if sample.source == "private":
        return f"{sample.center_id}:{stem}"
    frame_match = FRAME_GROUP_RE.match(stem)
    if frame_match:
        return f"video:{frame_match.group(1)}"
    return f"{sample.source}:{stem}"


def attach_groups(samples: list[Sample], hk_groups: dict[str, str]) -> list[Sample]:
    out: list[Sample] = []
    for sample in samples:
        out.append(
            Sample(
                src=sample.src,
                center_id=sample.center_id,
                source=sample.source,
                original_class=sample.original_class,
                target_class=sample.target_class,
                group_id=infer_group_id(sample, hk_groups),
            )
        )
    return out


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
                        group_id="",
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
                        group_id="",
                    )
                )
    return samples


def stratified_group_split(
    samples: list[Sample], val_ratio: float, test_ratio: float, seed: int
) -> tuple[list[Sample], list[Sample], list[Sample]]:
    """Split by procedure group so no group appears in more than one split."""
    by_group: dict[str, list[Sample]] = defaultdict(list)
    for sample in samples:
        by_group[sample.group_id].append(sample)

    groups_by_class: dict[str, list[str]] = defaultdict(list)
    for group_id, items in by_group.items():
        labels = {s.target_class for s in items}
        if len(labels) != 1:
            raise ValueError(f"Group {group_id} spans classes: {sorted(labels)}")
        groups_by_class[items[0].target_class].append(group_id)

    rng = random.Random(seed)
    train_groups: set[str] = set()
    val_groups: set[str] = set()
    test_groups: set[str] = set()

    for cls, group_ids in groups_by_class.items():
        shuffled = group_ids[:]
        rng.shuffle(shuffled)
        n = len(shuffled)
        n_test = max(1, int(n * test_ratio)) if n >= 3 else (1 if n > 1 else 0)
        n_val = max(1, int(n * val_ratio)) if n >= 3 else (1 if n > 2 else 0)
        n_train = n - n_val - n_test
        if n_train < 1 and n > 0:
            n_train, n_val, n_test = max(1, n - 2), min(1, n - 1), min(1, n - 1)
        train_groups.update(shuffled[:n_train])
        val_groups.update(shuffled[n_train : n_train + n_val])
        test_groups.update(shuffled[n_train + n_val :])

    def collect(selected: set[str]) -> list[Sample]:
        items: list[Sample] = []
        for group_id in selected:
            items.extend(by_group[group_id])
        return items

    return collect(train_groups), collect(val_groups), collect(test_groups)


def stratified_split(samples: list[Sample], val_ratio: float, test_ratio: float, seed: int):
    """Deprecated per-image split; kept for tests. Prefer stratified_group_split."""
    by_class: dict[str, list[Sample]] = defaultdict(list)
    for s in samples:
        by_class[s.target_class].append(s)
    rng = random.Random(seed)
    train, val, test = [], [], []
    for items in by_class.values():
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
    if train_pool:
        train, val, _ = stratified_group_split(train_pool, val_ratio, test_ratio, seed)
        link_samples(fold_root, "train", train)
        link_samples(fold_root, "val", val)
    link_samples(fold_root, "test", test_pool)


def split_group_stats(samples: list[Sample]) -> dict[str, int]:
    return {"images": len(samples), "groups": len({s.group_id for s in samples})}


def main() -> None:
    p = argparse.ArgumentParser(description="Prepare 3-class colonoscopy dataset with LOO folds")
    p.add_argument("--output", type=str, default="data/colonoscopy_3class")
    p.add_argument("--kvasir-dir", type=str, default="data/kvasir")
    p.add_argument("--hyperkvasir-dir", type=str, default="data/hyperkvasir")
    p.add_argument("--private-dir", type=str, default="data/private")
    p.add_argument("--val-ratio", type=float, default=0.15)
    p.add_argument("--test-ratio", type=float, default=0.15)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument(
        "--hyperkvasir-labels-csv",
        type=str,
        default=str(DEFAULT_HK_LABELS_CSV),
        help="HyperKvasir image-labels.csv for procedure grouping",
    )
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
    hk_groups = load_hyperkvasir_group_map(Path(args.hyperkvasir_labels_csv))
    samples = attach_groups(samples, hk_groups)

    if not samples:
        raise SystemExit(
            "No samples found. Run prepare-kvasir / prepare-hyperkvasir first, "
            "or add private data under data/private/{center_id}/labeled/."
        )

    centers = sorted({s.center_id for s in samples})
    counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for s in samples:
        counts[s.center_id][s.target_class] += 1

    # Pooled split (all centers) — group-aware
    all_root = output / "all"
    train, val, test = stratified_group_split(samples, args.val_ratio, args.test_ratio, args.seed)
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
        "split_mode": "grouped",
        "group_stats": {
            "total_groups": len({s.group_id for s in samples}),
            "all": {
                "train": split_group_stats(train),
                "val": split_group_stats(val),
                "test": split_group_stats(test),
            },
        },
        "sources": {
            "kvasir_dir": args.kvasir_dir,
            "hyperkvasir_dir": args.hyperkvasir_dir,
            "private_dir": args.private_dir,
            "hyperkvasir_labels_csv": args.hyperkvasir_labels_csv,
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
