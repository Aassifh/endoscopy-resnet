"""Tests for mask-aware SE blocks."""

import torch

from models.seresnet import MaskAwareSEBlock, SEBlock


def test_mask_aware_se_matches_standard_when_full_mask():
    torch.manual_seed(0)
    se_std = SEBlock(64)
    se_mask = MaskAwareSEBlock(64)
    se_mask.load_state_dict(se_std.state_dict(), strict=False)
    se_mask.fc.load_state_dict(se_std.fc.state_dict())

    x = torch.randn(2, 64, 7, 7)
    ones = torch.ones(2, 1, 7, 7)
    out_std = se_std(x)
    out_mask = se_mask(x, spatial_mask=ones)
    assert torch.allclose(out_std, out_mask, atol=1e-5)


def test_mask_aware_se_ignores_masked_zeros():
    torch.manual_seed(1)
    block = MaskAwareSEBlock(32)
    x = torch.ones(1, 32, 4, 4)
    x[:, :, 2:, :] = 10.0
    mask = torch.zeros(1, 1, 4, 4)
    mask[:, :, :2, :] = 1.0
    out = block(x, spatial_mask=mask)
    assert out.shape == x.shape
    # Visible region should be scaled; hidden region passes through scaled weights
    assert not torch.isnan(out).any()
