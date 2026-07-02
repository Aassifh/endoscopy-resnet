"""SE-ResNet-50 with optional ImageNet weight transfer and mask-aware SE for CNN-JEPA."""

from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision.models import ResNet50_Weights, resnet50


class SEBlock(nn.Module):
    def __init__(self, channels: int, reduction: int = 16):
        super().__init__()
        hidden = max(channels // reduction, 8)
        self.pool = nn.AdaptiveAvgPool2d(1)
        self.fc = nn.Sequential(
            nn.Linear(channels, hidden, bias=False),
            nn.ReLU(inplace=True),
            nn.Linear(hidden, channels, bias=False),
            nn.Sigmoid(),
        )

    def forward(self, x: torch.Tensor, spatial_mask: torch.Tensor | None = None) -> torch.Tensor:
        if spatial_mask is not None:
            return MaskAwareSEBlock.forward_from_parent(self, x, spatial_mask)
        b, c, _, _ = x.size()
        w = self.fc(self.pool(x).view(b, c)).view(b, c, 1, 1)
        return x * w


class MaskAwareSEBlock(nn.Module):
    """SE block with optional mask-weighted global average pooling."""

    def __init__(self, channels: int, reduction: int = 16):
        super().__init__()
        hidden = max(channels // reduction, 8)
        self.fc = nn.Sequential(
            nn.Linear(channels, hidden, bias=False),
            nn.ReLU(inplace=True),
            nn.Linear(hidden, channels, bias=False),
            nn.Sigmoid(),
        )

    @staticmethod
    def forward_from_parent(parent: SEBlock, x: torch.Tensor, spatial_mask: torch.Tensor) -> torch.Tensor:
        b, c, h, w = x.size()
        if spatial_mask.shape[-2:] != (h, w):
            spatial_mask = F.interpolate(spatial_mask, size=(h, w), mode="nearest")
        mask = spatial_mask.expand(b, c, h, w)
        denom = mask.sum(dim=(2, 3)).clamp(min=1e-6)
        pooled = (x * mask).sum(dim=(2, 3)) / denom
        w = parent.fc(pooled).view(b, c, 1, 1)
        return x * w

    def forward(self, x: torch.Tensor, spatial_mask: torch.Tensor | None = None) -> torch.Tensor:
        b, c, h, w = x.size()
        if spatial_mask is None:
            pooled = F.adaptive_avg_pool2d(x, 1).view(b, c)
        else:
            if spatial_mask.shape[-2:] != (h, w):
                spatial_mask = F.interpolate(spatial_mask, size=(h, w), mode="nearest")
            mask = spatial_mask.expand(b, c, h, w)
            denom = mask.sum(dim=(2, 3)).clamp(min=1e-6)
            pooled = (x * mask).sum(dim=(2, 3)) / denom
        w = self.fc(pooled).view(b, c, 1, 1)
        return x * w


class SEBottleneck(nn.Module):
    expansion = 4

    def __init__(self, inplanes, planes, stride=1, downsample=None, mask_aware_se: bool = False):
        super().__init__()
        self.conv1 = nn.Conv2d(inplanes, planes, 1, bias=False)
        self.bn1 = nn.BatchNorm2d(planes)
        self.conv2 = nn.Conv2d(planes, planes, 3, stride=stride, padding=1, bias=False)
        self.bn2 = nn.BatchNorm2d(planes)
        self.conv3 = nn.Conv2d(planes, planes * self.expansion, 1, bias=False)
        self.bn3 = nn.BatchNorm2d(planes * self.expansion)
        self.relu = nn.ReLU(inplace=True)
        channels = planes * self.expansion
        self.se: nn.Module = MaskAwareSEBlock(channels) if mask_aware_se else SEBlock(channels)
        self.mask_aware_se = mask_aware_se
        self.downsample = downsample

    def forward(self, x, spatial_mask: torch.Tensor | None = None):
        identity = x
        out = self.relu(self.bn1(self.conv1(x)))
        out = self.relu(self.bn2(self.conv2(out)))
        out = self.bn3(self.conv3(out))
        if self.mask_aware_se and spatial_mask is not None:
            out = self.se(out, spatial_mask=spatial_mask)
        else:
            out = self.se(out)
        if self.downsample is not None:
            identity = self.downsample(x)
        return self.relu(out + identity)


class SEResNet(nn.Module):
    def __init__(self, block, layers, num_classes=4, mask_aware_se: bool = False):
        super().__init__()
        self.inplanes = 64
        self.mask_aware_se = mask_aware_se
        self.conv1 = nn.Conv2d(3, 64, 7, stride=2, padding=3, bias=False)
        self.bn1 = nn.BatchNorm2d(64)
        self.relu = nn.ReLU(inplace=True)
        self.maxpool = nn.MaxPool2d(3, stride=2, padding=1)
        self.layer1 = self._make_layer(block, 64, layers[0])
        self.layer2 = self._make_layer(block, 128, layers[1], stride=2)
        self.layer3 = self._make_layer(block, 256, layers[2], stride=2)
        self.layer4 = self._make_layer(block, 512, layers[3], stride=2)
        self.avgpool = nn.AdaptiveAvgPool2d((1, 1))
        self.fc = nn.Linear(512 * block.expansion, num_classes)
        self.out_features = 512 * block.expansion
        self._init_weights()

    def _make_layer(self, block, planes, blocks, stride=1):
        downsample = None
        if stride != 1 or self.inplanes != planes * block.expansion:
            downsample = nn.Sequential(
                nn.Conv2d(self.inplanes, planes * block.expansion, 1, stride=stride, bias=False),
                nn.BatchNorm2d(planes * block.expansion),
            )
        layers_list = [block(self.inplanes, planes, stride, downsample, mask_aware_se=self.mask_aware_se)]
        self.inplanes = planes * block.expansion
        for _ in range(1, blocks):
            layers_list.append(block(self.inplanes, planes, mask_aware_se=self.mask_aware_se))
        return nn.ModuleList(layers_list)

    def _run_layer(self, layer: nn.ModuleList, x, spatial_mask: torch.Tensor | None):
        for block in layer:
            x = block(x, spatial_mask=spatial_mask)
        return x

    def _init_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, mode="fan_out", nonlinearity="relu")
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)

    def forward_stem(self, x):
        return self.maxpool(self.relu(self.bn1(self.conv1(x))))

    def forward_features_map(self, x, spatial_mask: torch.Tensor | None = None):
        x = self.forward_stem(x)
        x = self._run_layer(self.layer1, x, spatial_mask)
        x = self._run_layer(self.layer2, x, spatial_mask)
        x = self._run_layer(self.layer3, x, spatial_mask)
        x = self._run_layer(self.layer4, x, spatial_mask)
        return x

    def forward_features(self, x, spatial_mask: torch.Tensor | None = None):
        return torch.flatten(self.avgpool(self.forward_features_map(x, spatial_mask)), 1)

    def forward(self, x, spatial_mask: torch.Tensor | None = None):
        return self.fc(self.forward_features(x, spatial_mask))


def _load_resnet50_into_seresnet(model: SEResNet) -> None:
    src = resnet50(weights=ResNet50_Weights.IMAGENET1K_V1)
    dst = model.state_dict()
    src_map = src.state_dict()
    for key in dst:
        if key.startswith("fc."):
            continue
        if key in src_map and dst[key].shape == src_map[key].shape:
            dst[key] = src_map[key]
    model.load_state_dict(dst)


def seresnet50_from_scratch(
    num_classes: int = 4,
    pretrained: bool = False,
    mask_aware_se: bool = False,
    **_,
) -> nn.Module:
    model = SEResNet(SEBottleneck, [3, 4, 6, 3], num_classes=num_classes, mask_aware_se=mask_aware_se)
    if pretrained:
        _load_resnet50_into_seresnet(model)
    return model
