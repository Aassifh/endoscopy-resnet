"""Dual-stream: ResNet-50 RGB + lightweight color-texture CNN with feature fusion."""

from __future__ import annotations

import torch
import torch.nn as nn

from models.resnet import ResNetBackbone


class TextureColorNet(nn.Module):
    """Lightweight CNN for HSV / LBP 3-channel maps."""

    def __init__(self, out_features: int = 512):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(3, 32, 3, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.Conv2d(32, 64, 3, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.Conv2d(64, 128, 3, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.Conv2d(128, 256, 3, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
            nn.AdaptiveAvgPool2d((1, 1)),
        )
        self.fc = nn.Linear(256, out_features)
        self.out_features = out_features

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.net(x)
        return self.fc(torch.flatten(x, 1))


class DualStreamResNetColorTexture(nn.Module):
    def __init__(self, num_classes: int, pretrained: bool = False, tex_features: int = 512):
        super().__init__()
        self.rgb_stream = ResNetBackbone(num_classes=num_classes, pretrained=pretrained)
        self.rgb_stream.fc = nn.Identity()
        self.tex_stream = TextureColorNet(out_features=tex_features)
        fused = self.rgb_stream.out_features + tex_features
        self.classifier = nn.Linear(fused, num_classes)
        self.num_classes = num_classes

    def forward(self, rgb: torch.Tensor, texture: torch.Tensor | None = None) -> torch.Tensor:
        if texture is None:
            raise ValueError("Dual-stream model requires texture input.")
        f_rgb = self.rgb_stream.forward_features(rgb)
        f_tex = self.tex_stream(texture)
        return self.classifier(torch.cat([f_rgb, f_tex], dim=1))


def dualstream_resnet_color_texture(num_classes: int = 4, pretrained: bool = False, **_) -> nn.Module:
    return DualStreamResNetColorTexture(num_classes=num_classes, pretrained=pretrained)
