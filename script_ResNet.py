#!/usr/bin/env python3
"""Train endoscopy classifiers (ResNet, SE-ResNet, dual-stream)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from checkpoint import build_checkpoint, save_checkpoint
from early_stopping import EarlyStoppingConfig
from models.registry import ARCH_NAMES
from training import TrainConfig, run_training


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Endoscopy classification training")
    p.add_argument("--data-dir", type=str, required=True, help="Path to data/ with train/ and val/")
    p.add_argument("--arch", type=str, default="resnet50", choices=ARCH_NAMES)
    p.add_argument("--pretrained", action="store_true", help="Load ImageNet weights (RGB / SE backbone)")
    p.add_argument("--mask-aware-se", action="store_true", help="Use mask-aware SE blocks (SE-ResNet)")
    p.add_argument("--jepa-checkpoint", type=str, default="", help="Load CNN-JEPA context encoder weights")
    p.add_argument("--epochs", type=int, default=20, help="Max epochs (early stopping may stop earlier)")
    p.add_argument("--max-epochs", type=int, default=0, help="Override max epochs for early stopping")
    p.add_argument("--patience", type=int, default=0, help="Early stopping patience (0 = auto)")
    p.add_argument("--min-epochs", type=int, default=0, help="Minimum epochs before early stop")
    p.add_argument("--early-metric", type=str, default="val_macro_f1", help="Metric to monitor")
    p.add_argument("--early-mode", choices=["min", "max"], default="max")
    p.add_argument("--min-delta", type=float, default=0.005)
    p.add_argument("--batch-size", type=int, default=16)
    p.add_argument("--lr", type=float, default=None, help="Default: 1e-4 if pretrained else 1e-3")
    p.add_argument("--weight-decay", type=float, default=1e-4)
    p.add_argument("--img-size", type=int, default=224)
    p.add_argument("--num-classes", type=int, default=0, help="0 = infer from dataset")
    p.add_argument("--optimizer", choices=["adamw", "sgd"], default="adamw")
    p.add_argument("--scheduler", choices=["none", "cosine", "step"], default="none")
    p.add_argument("--label-smoothing", type=float, default=0.0)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--output", type=str, default="checkpoints/resnet_scratch.pt")
    p.add_argument("--device", type=str, default="auto")
    p.add_argument("--pretrain-method", type=str, default="", help="Metadata: none, imagenet, cnn_jepa, …")
    p.add_argument("--center-split", type=str, default="", help="LOO fold id for metadata")
    p.add_argument("--label-fraction", type=float, default=-1.0, help="Fraction of train labels used")
    p.add_argument(
        "--freeze-backbone",
        action="store_true",
        help="Freeze backbone; train classifier head only (linear probe / frozen teacher)",
    )
    return p.parse_args()


def build_early_config(args: argparse.Namespace) -> EarlyStoppingConfig:
    cfg = EarlyStoppingConfig.finetune()
    cfg.max_epochs = args.max_epochs or args.epochs
    cfg.patience = args.patience or cfg.patience
    cfg.min_epochs = args.min_epochs or cfg.min_epochs
    cfg.monitor = args.early_metric
    cfg.mode = args.early_mode
    cfg.min_delta = args.min_delta
    return cfg


def main() -> None:
    args = parse_args()
    lr = args.lr if args.lr is not None else (1e-4 if args.pretrained else 1e-3)
    early_cfg = build_early_config(args)

    config = TrainConfig(
        data_dir=args.data_dir,
        epochs=early_cfg.max_epochs,
        batch_size=args.batch_size,
        lr=lr,
        weight_decay=args.weight_decay,
        img_size=args.img_size,
        num_classes=args.num_classes or 4,
        optimizer=args.optimizer,
        scheduler=args.scheduler,
        label_smoothing=args.label_smoothing,
        seed=args.seed,
        device=args.device,
        arch=args.arch,
        pretrained=args.pretrained,
        early_stopping=early_cfg,
        jepa_checkpoint=args.jepa_checkpoint,
        mask_aware_se=args.mask_aware_se,
        label_fraction=args.label_fraction if args.label_fraction >= 0 else 1.0,
        freeze_backbone=args.freeze_backbone,
    )

    print(f"Training {args.arch} (pretrained={args.pretrained}, early_stop={early_cfg})")
    result = run_training(config)

    if result.best_state_dict is None:
        raise RuntimeError("Training did not produce a best checkpoint.")

    out_path = Path(args.output)
    early_stop_payload = {}
    if result.early_stop is not None:
        report_path = out_path.with_name(out_path.stem + ".early_stop.json")
        result.early_stop.save_report(report_path)
        early_stop_payload = json.loads(report_path.read_text())

    hparams = {
        "arch": args.arch,
        "pretrained": args.pretrained,
        "mask_aware_se": args.mask_aware_se,
        "epochs": early_cfg.max_epochs,
        "batch_size": config.batch_size,
        "lr": config.lr,
        "weight_decay": config.weight_decay,
        "img_size": config.img_size,
        "optimizer": config.optimizer,
        "scheduler": config.scheduler,
        "label_smoothing": config.label_smoothing,
        "seed": config.seed,
        "num_classes": len(result.class_names),
        "jepa_checkpoint": args.jepa_checkpoint,
        "freeze_backbone": args.freeze_backbone,
        "early_stopping": early_cfg.__dict__,
    }
    metrics = {
        "best_val_acc": result.best_val_acc,
        "best_val_macro_f1": result.best_val_macro_f1,
        "stopped_epoch": result.stopped_epoch,
        "stop_reason": result.stop_reason,
    }
    label_fraction = args.label_fraction if args.label_fraction >= 0 else None
    payload = build_checkpoint(
        result.best_state_dict,
        result.class_names,
        hparams,
        metrics,
        epoch=result.stopped_epoch or early_cfg.max_epochs,
        arch=args.arch,
        pretrained=args.pretrained,
        pretrain_method=args.pretrain_method or None,
        center_split=args.center_split or None,
        label_fraction=label_fraction,
        early_stop=early_stop_payload or None,
    )
    save_checkpoint(payload, args.output)

    history_path = out_path.with_suffix(".history.json")
    history_path.write_text(json.dumps(result.history, indent=2))

    print(f"Best val acc:       {result.best_val_acc:.4f}")
    print(f"Best val macro-F1:  {result.best_val_macro_f1:.4f}")
    if result.stopped_epoch:
        print(f"Early stop:         epoch {result.stopped_epoch} ({result.stop_reason})")
    print(f"Classes ({len(result.class_names)}): {result.class_names[:5]}{'…' if len(result.class_names) > 5 else ''}")
    print(f"Checkpoint saved:   {args.output}")


if __name__ == "__main__":
    main()
