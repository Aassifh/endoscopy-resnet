#!/usr/bin/env python3
"""
Phase-1 CNN-JEPA pretraining on unlabeled endoscopy frames.

Usage:
  python scripts/pretrain_cnn_jepa.py --frames-dir data/jepa_frames/hyperkvasir_video \\
      --backbone seresnet50 --mask-aware-se --output checkpoints/jepa/c4_mask_aware.pt

Early stopping defaults (article): max 80 epochs, patience 10, monitor val_latent_loss.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import torch
import torch.nn as nn
import torch.optim as optim
from PIL import Image
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms
from tqdm import tqdm

from early_stopping import EarlyStopping, EarlyStoppingConfig
from models.jepa.module import JEPAModule
from training import resolve_device

IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp"}


class UnlabeledFrameDataset(Dataset):
    def __init__(self, root: Path, img_size: int, max_samples: int = 0):
        self.paths = sorted(
            p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_EXTS
        )
        if max_samples > 0 and len(self.paths) > max_samples:
            rng = random.Random(42)
            self.paths = rng.sample(self.paths, max_samples)
        self.transform = transforms.Compose([
            transforms.RandomResizedCrop(img_size),
            transforms.RandomHorizontalFlip(),
            transforms.ToTensor(),
            transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
        ])

    def __len__(self) -> int:
        return len(self.paths)

    def __getitem__(self, index: int) -> torch.Tensor:
        img = Image.open(self.paths[index]).convert("RGB")
        return self.transform(img)


def split_loader(dataset: UnlabeledFrameDataset, batch_size: int, val_ratio: float, num_workers: int):
    n = len(dataset)
    n_val = max(1, int(n * val_ratio))
    n_train = n - n_val
    train_ds, val_ds = torch.utils.data.random_split(
        dataset, [n_train, n_val], generator=torch.Generator().manual_seed(42)
    )
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=num_workers)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=num_workers)
    return train_loader, val_loader


@torch.no_grad()
def validate_jepa(model: JEPAModule, loader: DataLoader, device: torch.device) -> float:
    model.eval()
    total, count = 0.0, 0
    for images in loader:
        images = images.to(device)
        loss, _ = model(images)
        total += loss.item() * images.size(0)
        count += images.size(0)
    return total / max(count, 1)


def train_one_epoch(model: JEPAModule, loader: DataLoader, optimizer: optim.Optimizer, device: torch.device) -> float:
    model.train()
    total, count = 0.0, 0
    for images in tqdm(loader, desc="pretrain", leave=False):
        images = images.to(device)
        optimizer.zero_grad(set_to_none=True)
        loss, _ = model(images)
        loss.backward()
        optimizer.step()
        model.update_target_encoder()
        total += loss.item() * images.size(0)
        count += images.size(0)
    return total / max(count, 1)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="CNN-JEPA pretraining")
    p.add_argument("--frames-dir", type=str, required=True, help="Directory of unlabeled frames")
    p.add_argument("--backbone", choices=["seresnet50", "resnet50"], default="seresnet50")
    p.add_argument("--mask-aware-se", action="store_true")
    p.add_argument("--pretrained-backbone", action="store_true")
    p.add_argument("--output", type=str, default="checkpoints/jepa/cnn_jepa.pt")
    p.add_argument("--batch-size", type=int, default=16)
    p.add_argument("--lr", type=float, default=1e-4)
    p.add_argument("--weight-decay", type=float, default=1e-4)
    p.add_argument("--img-size", type=int, default=224)
    p.add_argument("--max-samples", type=int, default=0, help="Subsample frames (0 = all)")
    p.add_argument("--val-ratio", type=float, default=0.05)
    p.add_argument("--max-epochs", type=int, default=80)
    p.add_argument("--patience", type=int, default=10)
    p.add_argument("--min-epochs", type=int, default=20)
    p.add_argument("--min-delta", type=float, default=1e-4)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--num-workers", type=int, default=0)
    p.add_argument("--device", type=str, default="auto")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    torch.manual_seed(args.seed)
    device = resolve_device(args.device)

    frames_root = Path(args.frames_dir)
    if not frames_root.is_dir():
        raise SystemExit(f"Frames directory not found: {frames_root}")

    dataset = UnlabeledFrameDataset(frames_root, args.img_size, max_samples=args.max_samples)
    if len(dataset) == 0:
        raise SystemExit(f"No images under {frames_root}")

    train_loader, val_loader = split_loader(dataset, args.batch_size, args.val_ratio, args.num_workers)

    model = JEPAModule(
        backbone=args.backbone,
        mask_aware_se=args.mask_aware_se,
        img_size=args.img_size,
        pretrained_backbone=args.pretrained_backbone,
    ).to(device)

    optimizer = optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.max_epochs)

    early_cfg = EarlyStoppingConfig.pretrain_jepa()
    early_cfg.max_epochs = args.max_epochs
    early_cfg.patience = args.patience
    early_cfg.min_epochs = args.min_epochs
    early_cfg.min_delta = args.min_delta
    early_stop = EarlyStopping(early_cfg)

    best_state = None
    history: list[dict] = []

    for epoch in range(1, early_cfg.max_epochs + 1):
        train_loss = train_one_epoch(model, train_loader, optimizer, device)
        val_loss = validate_jepa(model, val_loader, device)
        scheduler.step()

        history.append({"epoch": epoch, "train_latent_loss": train_loss, "val_latent_loss": val_loss})
        print(f"Epoch {epoch:3d}  train={train_loss:.5f}  val={val_loss:.5f}")

        is_best, should_stop = early_stop.step(epoch, {"val_latent_loss": val_loss})
        if is_best:
            best_state = {
                "context_encoder": model.context_encoder.state_dict(),
                "predictor": model.predictor.state_dict(),
                "backbone": args.backbone,
                "mask_aware_se": args.mask_aware_se,
            }

        if should_stop:
            print(f"Early stop at epoch {epoch} ({early_stop.state.stop_reason})")
            break

    if best_state is None:
        best_state = {
            "context_encoder": model.context_encoder.state_dict(),
            "predictor": model.predictor.state_dict(),
            "backbone": args.backbone,
            "mask_aware_se": args.mask_aware_se,
        }

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "pretrain_method": "cnn_jepa",
        "context_encoder": best_state["context_encoder"],
        "predictor": best_state["predictor"],
        "hparams": vars(args),
        "metrics": {"best_val_latent_loss": early_stop.state.best_value},
        "history": history,
    }
    torch.save(payload, out)
    early_stop.save_report(out.with_suffix(".early_stop.json"))
    (out.with_suffix(".history.json")).write_text(json.dumps(history, indent=2))
    print(f"Saved JEPA checkpoint: {out}")


if __name__ == "__main__":
    main()
