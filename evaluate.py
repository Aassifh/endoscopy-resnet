#!/usr/bin/env python3
"""Evaluate a trained checkpoint on the validation (or test) split."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch
import torch.nn as nn
from sklearn.metrics import classification_report, confusion_matrix, f1_score

from checkpoint import load_checkpoint
from data import get_eval_loader
from training import validate, resolve_device


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Evaluate endoscopy classifier checkpoint")
    p.add_argument("--checkpoint", type=str, default="checkpoints/resnet_scratch.pt")
    p.add_argument("--data-dir", type=str, required=True, help="Root data directory")
    p.add_argument("--split", choices=["val", "test"], default="val")
    p.add_argument("--batch-size", type=int, default=16)
    p.add_argument("--img-size", type=int, default=224)
    p.add_argument("--output", type=str, default="", help="Optional JSON report path")
    p.add_argument("--device", type=str, default="auto")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    device = resolve_device(args.device)

    model, meta = load_checkpoint(args.checkpoint, map_location=device)
    model = model.to(device)
    dual = meta.get("dual_stream", False)

    hparams = meta.get("hparams", {})
    img_size = hparams.get("img_size", args.img_size)
    batch_size = hparams.get("batch_size", args.batch_size)

    val_loader, class_names = get_eval_loader(
        args.data_dir, args.split, batch_size, img_size, dual_stream=dual
    )
    if meta.get("class_names"):
        class_names = meta["class_names"]

    criterion = nn.CrossEntropyLoss()
    val_loss, val_acc, preds, labels = validate(model, val_loader, criterion, device, dual=dual)
    macro_f1 = f1_score(labels, preds, average="macro", zero_division=0)
    weighted_f1 = f1_score(labels, preds, average="weighted", zero_division=0)
    cm = confusion_matrix(labels, preds).tolist()
    report = classification_report(labels, preds, target_names=class_names, zero_division=0)

    print(f"Arch:         {meta.get('arch', 'unknown')}")
    print(f"Split:        {args.split}")
    print(f"Loss:         {val_loss:.4f}")
    print(f"Accuracy:     {val_acc:.4f}")
    print(f"Macro-F1:     {macro_f1:.4f}")
    print(f"Weighted-F1:  {weighted_f1:.4f}")
    print("\nClassification report:\n")
    print(report)

    report_dict = {
        "checkpoint": args.checkpoint,
        "arch": meta.get("arch"),
        "pretrained": meta.get("pretrained", False),
        "split": args.split,
        "class_names": class_names,
        "loss": val_loss,
        "accuracy": val_acc,
        "macro_f1": macro_f1,
        "weighted_f1": weighted_f1,
        "confusion_matrix": cm,
        "classification_report": report,
    }

    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report_dict, indent=2))
        print(f"\nReport saved: {out}")


if __name__ == "__main__":
    main()
