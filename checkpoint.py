"""Checkpoint save/load with architecture registry and legacy compatibility."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import torch

from model import ARCH_NAME as LEGACY_ARCH
from models.registry import build_model, is_dual_stream


def build_checkpoint(
    state_dict: dict,
    class_names: list[str],
    hparams: dict,
    metrics: dict,
    epoch: int | None = None,
    arch: str | None = None,
    pretrained: bool = False,
    pretrain_method: str | None = None,
    center_split: str | None = None,
    label_fraction: float | None = None,
    early_stop: dict | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "arch": arch or hparams.get("arch", LEGACY_ARCH),
        "pretrained": pretrained or hparams.get("pretrained", False),
        "state_dict": state_dict,
        "class_names": class_names,
        "hparams": hparams,
        "metrics": metrics,
        "epoch": epoch,
    }
    if pretrain_method is not None:
        payload["pretrain_method"] = pretrain_method
    if center_split is not None:
        payload["center_split"] = center_split
    if label_fraction is not None:
        payload["label_fraction"] = label_fraction
    if early_stop is not None:
        payload["early_stop"] = early_stop
    return payload


def save_checkpoint(payload: dict[str, Any], path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(payload, path)


def load_checkpoint(path: str | Path, map_location: str | torch.device = "cpu") -> tuple[torch.nn.Module, dict[str, Any]]:
    raw = torch.load(path, map_location=map_location, weights_only=False)

    if isinstance(raw, dict) and "state_dict" in raw:
        meta = raw
        state_dict = raw["state_dict"]
        class_names = raw.get("class_names", [])
        arch = raw.get("arch", LEGACY_ARCH)
        pretrained = raw.get("pretrained", False)
        num_classes = len(class_names) if class_names else raw.get("hparams", {}).get("num_classes", 4)
    else:
        meta = {"arch": LEGACY_ARCH, "class_names": [], "hparams": {"num_classes": 4}, "metrics": {}, "pretrained": False}
        state_dict = raw
        arch = LEGACY_ARCH
        pretrained = False
        num_classes = 4

    model = build_model(arch, num_classes=num_classes, pretrained=False)
    model.load_state_dict(state_dict)
    model.eval()
    meta.setdefault("arch", arch)
    meta.setdefault("pretrained", pretrained)
    meta["dual_stream"] = is_dual_stream(arch)
    return model, meta
