"""Convolutional latent predictor for CNN-JEPA."""

from __future__ import annotations

import torch
import torch.nn as nn


class ConvPredictor(nn.Module):
    """Lightweight depthwise-separable conv predictor on feature maps."""

    def __init__(self, in_channels: int, hidden_channels: int | None = None):
        super().__init__()
        hidden = hidden_channels or in_channels // 2
        self.net = nn.Sequential(
            nn.Conv2d(in_channels, hidden, 1, bias=False),
            nn.BatchNorm2d(hidden),
            nn.ReLU(inplace=True),
            nn.Conv2d(hidden, hidden, 3, padding=1, groups=hidden, bias=False),
            nn.BatchNorm2d(hidden),
            nn.ReLU(inplace=True),
            nn.Conv2d(hidden, in_channels, 1, bias=False),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)
