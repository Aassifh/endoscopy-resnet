"""Multi-scale block masking for CNN-JEPA."""

from __future__ import annotations

import torch


class BlockMaskGenerator:
    """Generate binary context masks at image resolution (1 = visible)."""

    def __init__(
        self,
        img_size: int = 224,
        min_visible_ratio: float = 0.25,
        max_visible_ratio: float = 0.45,
    ):
        self.img_size = img_size
        self.min_visible_ratio = min_visible_ratio
        self.max_visible_ratio = max_visible_ratio

    def __call__(self, batch_size: int, device: torch.device) -> torch.Tensor:
        masks = []
        for _ in range(batch_size):
            visible = self.min_visible_ratio + torch.rand(1).item() * (
                self.max_visible_ratio - self.min_visible_ratio
            )
            mask = torch.zeros(1, self.img_size, self.img_size)
            area = int(self.img_size * self.img_size * visible)
            h = max(8, int((area * torch.rand(1).item()) ** 0.5))
            w = max(8, area // h)
            h = min(h, self.img_size)
            w = min(w, self.img_size)
            top = torch.randint(0, max(1, self.img_size - h + 1), (1,)).item()
            left = torch.randint(0, max(1, self.img_size - w + 1), (1,)).item()
            mask[:, top : top + h, left : left + w] = 1.0
            masks.append(mask)
        return torch.stack(masks, dim=0).to(device)
