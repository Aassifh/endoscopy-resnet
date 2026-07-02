"""CNN-JEPA module with EMA target encoder."""

from __future__ import annotations

import copy

import torch
import torch.nn as nn

from models.jepa.encoder import JEPAEncoder, build_target_encoder
from models.jepa.loss import latent_prediction_loss
from models.jepa.masking import BlockMaskGenerator
from models.jepa.predictor import ConvPredictor


class JEPAModule(nn.Module):
    def __init__(
        self,
        backbone: str = "seresnet50",
        mask_aware_se: bool = True,
        img_size: int = 224,
        ema_momentum: float = 0.996,
        pretrained_backbone: bool = False,
    ):
        super().__init__()
        self.context_encoder = JEPAEncoder(
            backbone=backbone,
            mask_aware_se=mask_aware_se,
            pretrained=pretrained_backbone,
        )
        self.target_encoder = build_target_encoder(self.context_encoder)
        self.predictor = ConvPredictor(self.context_encoder.out_channels)
        self.mask_generator = BlockMaskGenerator(img_size=img_size)
        self.ema_momentum = ema_momentum

    @torch.no_grad()
    def update_target_encoder(self) -> None:
        m = self.ema_momentum
        for t_p, c_p in zip(self.target_encoder.parameters(), self.context_encoder.parameters()):
            t_p.data.mul_(m).add_(c_p.data, alpha=1.0 - m)

    def forward(self, images: torch.Tensor) -> tuple[torch.Tensor, dict[str, torch.Tensor]]:
        context_mask = self.mask_generator(images.size(0), images.device)
        masked_input = images * context_mask

        context_feat = self.context_encoder(masked_input, context_mask=context_mask)
        pred = self.predictor(context_feat)

        with torch.no_grad():
            target_feat = self.target_encoder(images, context_mask=None)
            target_feat = target_feat.detach()

        loss = latent_prediction_loss(pred, target_feat)
        return loss, {
            "context_mask": context_mask,
            "pred": pred,
            "target": target_feat,
        }

    def encode_for_finetune(self) -> nn.Module:
        """Return backbone suitable for loading into classifier (without predictor)."""
        return self.context_encoder.encoder

    def state_dict_for_backbone(self) -> dict:
        return copy.deepcopy(self.context_encoder.state_dict())
