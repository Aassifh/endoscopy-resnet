"""Model registry for endoscopy classification architectures."""

from models.registry import ARCH_NAMES, build_model, get_arch_name

__all__ = ["ARCH_NAMES", "build_model", "get_arch_name"]
