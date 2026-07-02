"""SE-ResNet / ResNet encoder wrappers for CNN-JEPA."""

from __future__ import annotations

import copy

import torch
import torch.nn as nn

from models.resnet import ResNetBackbone
from models.seresnet import SEResNet, SEBottleneck, seresnet50_from_scratch


class JEPAEncoder(nn.Module):
    """Context encoder producing spatial feature maps [B, C, H, W]."""

    def __init__(
        self,
        backbone: str = "seresnet50",
        mask_aware_se: bool = True,
        pretrained: bool = False,
    ):
        super().__init__()
        self.backbone_name = backbone
        self.mask_aware_se = mask_aware_se
        if backbone == "seresnet50":
            self.encoder: nn.Module = seresnet50_from_scratch(
                num_classes=512,
                pretrained=pretrained,
                mask_aware_se=mask_aware_se,
            )
            if isinstance(self.encoder, SEResNet):
                self.encoder.fc = nn.Identity()
        elif backbone == "resnet50":
            wrapper = ResNetBackbone(num_classes=512, pretrained=pretrained)
            wrapper.fc = nn.Identity()
            self.encoder = wrapper
        else:
            raise ValueError(f"Unknown JEPA backbone: {backbone}")

        self.out_channels = 2048

    def forward(self, x: torch.Tensor, context_mask: torch.Tensor | None = None) -> torch.Tensor:
        if isinstance(self.encoder, SEResNet):
            return self.encoder.forward_features_map(x, spatial_mask=context_mask)
        feat = self.encoder.features(x)
        return feat

    def forward_pooled(self, x: torch.Tensor, context_mask: torch.Tensor | None = None) -> torch.Tensor:
        feat = self.forward(x, context_mask=context_mask)
        return torch.flatten(nn.functional.adaptive_avg_pool2d(feat, 1), 1)


def build_target_encoder(context_encoder: JEPAEncoder) -> JEPAEncoder:
    target = copy.deepcopy(context_encoder)
    for p in target.parameters():
        p.requires_grad = False
    return target
