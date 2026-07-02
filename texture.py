"""Color-texture maps (HSV + LBP) for the dual-stream branch."""

from __future__ import annotations

import numpy as np
import torch
from PIL import Image
from skimage.feature import local_binary_pattern


def rgb_to_hsv_channels(rgb: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return H, S, V in [0, 1] from RGB uint8 array."""
    img = Image.fromarray(rgb.astype(np.uint8)).convert("HSV")
    hsv = np.asarray(img, dtype=np.float32) / 255.0
    return hsv[..., 0], hsv[..., 1], hsv[..., 2]


def compute_lbp(gray: np.ndarray, radius: int = 2, n_points: int = 8) -> np.ndarray:
    lbp = local_binary_pattern(gray, n_points, radius, method="uniform")
    lbp = np.nan_to_num(lbp, nan=0.0)
    if lbp.max() > 0:
        lbp = lbp / lbp.max()
    return lbp.astype(np.float32)


def rgb_to_texture_map(rgb: np.ndarray, radius: int = 2) -> np.ndarray:
    """Build 3-channel map: H, LBP(gray), S — shape (3, H, W)."""
    h, s, _ = rgb_to_hsv_channels(rgb)
    gray = np.asarray(Image.fromarray(rgb.astype(np.uint8)).convert("L"), dtype=np.float32) / 255.0
    lbp = compute_lbp(gray, radius=radius)
    return np.stack([h, lbp, s], axis=0)


def texture_to_tensor(rgb: np.ndarray, radius: int = 2) -> torch.Tensor:
    return torch.from_numpy(rgb_to_texture_map(rgb, radius=radius))
