"""Backward-compatible re-exports of the legacy scratch ResNet-50."""

from models.resnet_legacy import ARCH_NAME, ResNet, resnet50_from_scratch

__all__ = ["ARCH_NAME", "ResNet", "resnet50_from_scratch"]
