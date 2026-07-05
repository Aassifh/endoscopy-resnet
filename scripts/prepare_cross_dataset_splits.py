#!/usr/bin/env python3
"""Build Kvasir <-> HyperKvasir cross-dataset 3-class splits for external validation."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prepare_colonoscopy_3class import (
    DEFAULT_HK_LABELS_CSV,
    HYPERKVASIR_TO_3CLASS,
    KVASIR_TO_3CLASS,
    Sample,
    attach_groups,
    collect_from_imagefolder,
    load_hyperkvasir_group_map,
    stratified_group_split,
)


def link_samples(out_root: Path, split: str, items: list[Sample]) -> None:
    for i, sample in enumerate(items):
        dst_dir = out_root / split / sample.target_class
        dst_dir.mkdir(parents=True, exist_ok=True)
        src = Path(sample.src)
        dst = dst_dir / f"{sample.source}_{sample.target_class}_{split}_{i:05d}{src.suffix.lower()}"
        if dst.exists() or dst.is_symlink():
            continue
        try:
            dst.symlink_to(src.resolve())
        except OSError:
            shutil.copy2(src, dst)


def write_direction(
    output: Path,
    name: str,
    train_pool: list[Sample],
    test_pool: list[Sample],
    seed: int,
    val_ratio: float,
) -> dict:
    root = output / name
    if root.exists():
        shutil.rmtree(root)
    train, val, _ = stratified_group_split(train_pool, val_ratio, 0.0, seed)
    link_samples(root, "train", train)
    link_samples(root, "val", val)
    link_samples(root, "test", test_pool)
    return {
        "train": {"images": len(train), "groups": len({s.group_id for s in train})},
        "val": {"images": len(val), "groups": len({s.group_id for s in val})},
        "test": {"images": len(test_pool), "groups": len({s.group_id for s in test_pool})},
    }


def main() -> None:
    p = argparse.ArgumentParser(description="Prepare cross-dataset 3-class splits")
    p.add_argument("--output", type=str, default="data/colonoscopy_3class/cross")
    p.add_argument("--kvasir-dir", type=str, default="data/kvasir")
    p.add_argument("--hyperkvasir-dir", type=str, default="data/hyperkvasir")
    p.add_argument("--hyperkvasir-labels-csv", type=str, default=str(DEFAULT_HK_LABELS_CSV))
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--val-ratio", type=float, default=0.15)
    args = p.parse_args()

    samples: list[Sample] = []
    samples.extend(
        collect_from_imagefolder(Path(args.kvasir_dir), "simula", "kvasir", KVASIR_TO_3CLASS)
    )
    samples.extend(
        collect_from_imagefolder(
            Path(args.hyperkvasir_dir), "simula", "hyperkvasir", HYPERKVASIR_TO_3CLASS
        )
    )
    hk_groups = load_hyperkvasir_group_map(Path(args.hyperkvasir_labels_csv))
    samples = attach_groups(samples, hk_groups)

    kvasir = [s for s in samples if s.source == "kvasir"]
    hyperkvasir = [s for s in samples if s.source == "hyperkvasir"]
    if not kvasir or not hyperkvasir:
        raise SystemExit("Need both Kvasir and HyperKvasir samples for cross-dataset splits.")

    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    manifest = {
        "seed": args.seed,
        "val_ratio": args.val_ratio,
        "directions": {
            "kvasir_train_hyperkvasir_test": write_direction(
                output, "kvasir_train_hyperkvasir_test", kvasir, hyperkvasir, args.seed, args.val_ratio
            ),
            "hyperkvasir_train_kvasir_test": write_direction(
                output, "hyperkvasir_train_kvasir_test", hyperkvasir, kvasir, args.seed, args.val_ratio
            ),
        },
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"Cross-dataset splits -> {output.resolve()}")
    for name, stats in manifest["directions"].items():
        print(f"  {name}: train={stats['train']['images']} val={stats['val']['images']} test={stats['test']['images']}")


if __name__ == "__main__":
    main()
