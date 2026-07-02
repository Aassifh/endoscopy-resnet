"""Tests for group-aware splits in prepare_colonoscopy_3class."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "prepare_colonoscopy_3class.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("prepare_colonoscopy_3class", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _sample(src: str, target: str, source: str = "kvasir", group_id: str = "") -> object:
    mod = _load_module()
    return mod.Sample(
        src=src,
        center_id="simula",
        source=source,
        original_class=target,
        target_class=target,
        group_id=group_id,
    )


def test_group_split_keeps_groups_disjoint():
    mod = _load_module()
    samples = []
    for cls in ("landmark", "normal_mucosa", "polyp"):
        for gid in range(6):
            group_id = f"g{cls}_{gid}"
            for idx in range(3):
                samples.append(
                    _sample(f"/tmp/{group_id}_{idx}.jpg", cls, group_id=group_id)
                )

    train, val, test = mod.stratified_group_split(samples, 0.15, 0.15, seed=42)
    train_g = {s.group_id for s in train}
    val_g = {s.group_id for s in val}
    test_g = {s.group_id for s in test}
    assert not (train_g & val_g)
    assert not (train_g & test_g)
    assert not (val_g & test_g)
    assert train_g | val_g | test_g == {s.group_id for s in samples}


def test_infer_group_id_for_video_frames():
    mod = _load_module()
    sample = _sample("/frames/colon_clip_000042.jpg", "polyp", source="hyperkvasir_video")
    sample = mod.Sample(
        src=sample.src,
        center_id=sample.center_id,
        source=sample.source,
        original_class=sample.original_class,
        target_class=sample.target_class,
        group_id=mod.infer_group_id(sample, {}),
    )
    assert sample.group_id == "video:colon_clip"
