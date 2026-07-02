"""Latent prediction loss for JEPA."""

from __future__ import annotations

import torch
import torch.nn.functional as F


def latent_prediction_loss(pred: torch.Tensor, target: torch.Tensor, normalize: bool = True) -> torch.Tensor:
    if normalize:
        pred = F.normalize(pred, dim=1, eps=1e-6)
        target = F.normalize(target, dim=1, eps=1e-6)
    return F.mse_loss(pred, target)
