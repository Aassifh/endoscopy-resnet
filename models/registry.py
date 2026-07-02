"""Factory for ResNet, SE-ResNet, dual-stream, and JEPA-backed classifiers."""

from __future__ import annotations

from pathlib import Path

import torch

from models.dualstream import dualstream_resnet_color_texture
from models.resnet import resnet50_from_scratch
from models.resnet_legacy import resnet50_from_scratch as resnet50_legacy
from models.seresnet import seresnet50_from_scratch

ARCH_NAMES = (
    "resnet50",
    "resnet50_from_scratch",
    "seresnet50",
    "seresnet50_mask_aware",
    "seresnet50_cnn_jepa",
    "dualstream_resnet_color_texture",
)


def build_model(
    arch: str,
    num_classes: int,
    pretrained: bool = False,
    mask_aware_se: bool = False,
    **kwargs,
):
    arch = arch.lower()
    if arch == "resnet50":
        return resnet50_from_scratch(num_classes=num_classes, pretrained=pretrained, **kwargs)
    if arch == "resnet50_from_scratch":
        if pretrained:
            raise ValueError("Legacy resnet50_from_scratch does not support ImageNet pretrained.")
        return resnet50_legacy(num_classes=num_classes, **kwargs)
    if arch in ("seresnet50", "seresnet50_mask_aware", "seresnet50_cnn_jepa"):
        use_mask = mask_aware_se or arch in ("seresnet50_mask_aware", "seresnet50_cnn_jepa")
        return seresnet50_from_scratch(
            num_classes=num_classes,
            pretrained=pretrained,
            mask_aware_se=use_mask,
            **kwargs,
        )
    if arch == "dualstream_resnet_color_texture":
        return dualstream_resnet_color_texture(num_classes=num_classes, pretrained=pretrained, **kwargs)
    raise ValueError(f"Unknown arch {arch!r}. Choose from: {ARCH_NAMES}")


def get_arch_name(arch: str) -> str:
    return arch.lower()


def is_dual_stream(arch: str) -> bool:
    return arch.lower() == "dualstream_resnet_color_texture"


def load_jepa_into_classifier(model: torch.nn.Module, checkpoint_path: str | Path, device: str = "cpu") -> None:
    """Load CNN-JEPA context encoder weights into a supervised classifier backbone."""
    raw = torch.load(checkpoint_path, map_location=device, weights_only=False)
    state = raw.get("context_encoder", raw.get("state_dict", raw))
    if isinstance(state, dict) and "encoder" in state:
        state = state["encoder"]
    model_state = model.state_dict()
    loaded = 0
    for key, value in state.items():
        target_key = key.replace("encoder.", "") if key.startswith("encoder.") else key
        if target_key in model_state and model_state[target_key].shape == value.shape:
            model_state[target_key] = value
            loaded += 1
    model.load_state_dict(model_state)
    print(f"Loaded {loaded} tensors from JEPA checkpoint into classifier backbone.")
