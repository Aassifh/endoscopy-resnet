"""ResNet-50 from scratch or ImageNet-pretrained (torchvision)."""

from __future__ import annotations

import torch
import torch.nn as nn
from torchvision.models import ResNet50_Weights, resnet50


class ResNetBackbone(nn.Module):
    """Thin wrapper around torchvision ResNet-50 for feature extraction."""

    def __init__(self, num_classes: int, pretrained: bool = False):
        super().__init__()
        weights = ResNet50_Weights.IMAGENET1K_V1 if pretrained else None
        net = resnet50(weights=weights)
        self.features = nn.Sequential(
            net.conv1, net.bn1, net.relu, net.maxpool,
            net.layer1, net.layer2, net.layer3, net.layer4,
        )
        self.avgpool = net.avgpool
        self.fc = nn.Linear(net.fc.in_features, num_classes)
        self.out_features = net.fc.in_features

    def forward_features(self, x):
        x = self.features(x)
        x = self.avgpool(x)
        return torch.flatten(x, 1)

    def forward(self, x):
        return self.fc(self.forward_features(x))


def resnet50_from_scratch(num_classes: int = 4, pretrained: bool = False, **_) -> nn.Module:
    return ResNetBackbone(num_classes=num_classes, pretrained=pretrained)
