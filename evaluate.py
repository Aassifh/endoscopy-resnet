#!/usr/bin/env python3
"""Evaluate a trained checkpoint on the validation (or test) split."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from sklearn.metrics import (
    auc,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    roc_curve,
)

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
    p.add_argument(
        "--clinical-metrics",
        action="store_true",
        help="Add polyp ROC/PR and sensitivity at fixed specificity",
    )
    p.add_argument(
        "--target-specificity",
        type=float,
        default=0.95,
        help="Specificity for polyp sensitivity reporting (default 0.95)",
    )
    return p.parse_args()


def collect_predictions(model, loader, device, dual: bool) -> tuple[list[int], list[int], np.ndarray]:
    model.eval()
    all_labels: list[int] = []
    all_preds: list[int] = []
    all_probs: list[np.ndarray] = []
    with torch.no_grad():
        for batch in loader:
            if dual:
                (inputs, labels) = batch
                rgb, texture = inputs
                rgb = rgb.to(device, non_blocking=True)
                texture = texture.to(device, non_blocking=True)
                labels = labels.to(device, non_blocking=True)
                outputs = model(rgb, texture)
            else:
                inputs, labels = batch
                inputs = inputs.to(device, non_blocking=True)
                labels = labels.to(device, non_blocking=True)
                outputs = model(inputs)
            probs = torch.softmax(outputs, dim=1).cpu().numpy()
            preds = outputs.argmax(dim=1)
            all_labels.extend(labels.cpu().tolist())
            all_preds.extend(preds.cpu().tolist())
            all_probs.append(probs)
    prob_matrix = np.vstack(all_probs) if all_probs else np.zeros((0, 0))
    return all_labels, all_preds, prob_matrix


def polyp_clinical_metrics(
    labels: list[int],
    prob_matrix: np.ndarray,
    class_names: list[str],
    target_specificity: float,
) -> dict | None:
    polyp_idx = None
    for name in ("polyp", "polyps"):
        if name in class_names:
            polyp_idx = class_names.index(name)
            break
    if polyp_idx is None or prob_matrix.size == 0:
        return None

    y_true = np.array([1 if y == polyp_idx else 0 for y in labels])
    y_score = prob_matrix[:, polyp_idx]
    if len(np.unique(y_true)) < 2:
        return None

    fpr, tpr, _ = roc_curve(y_true, y_score)
    prec, rec, _ = precision_recall_curve(y_true, y_score)
    roc_auc = float(auc(fpr, tpr))
    pr_auc = float(auc(rec, prec))

    spec = 1.0 - fpr
    idx = np.searchsorted(spec, target_specificity, side="left")
    idx = min(max(int(idx), 0), len(tpr) - 1)
    sensitivity_at_spec = float(tpr[idx])
    achieved_spec = float(spec[idx])

    return {
        "polyp_roc_auc": roc_auc,
        "polyp_pr_auc": pr_auc,
        "polyp_sensitivity_at_target_specificity": sensitivity_at_spec,
        "target_specificity": target_specificity,
        "achieved_specificity": achieved_spec,
        "roc_curve": {"fpr": fpr.tolist(), "tpr": tpr.tolist()},
        "pr_curve": {"precision": prec.tolist(), "recall": rec.tolist()},
    }


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
    if args.clinical_metrics:
        labels, preds, prob_matrix = collect_predictions(model, val_loader, device, dual)
        val_acc = float(np.mean(np.array(labels) == np.array(preds))) if labels else 0.0
        if labels:
            val_loss = float(
                -np.mean(np.log(prob_matrix[np.arange(len(labels)), labels] + 1e-12))
            )
        else:
            val_loss = 0.0
    else:
        val_loss, val_acc, preds, labels = validate(model, val_loader, criterion, device, dual=dual)
        prob_matrix = np.zeros((0, len(class_names)))

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

    if args.clinical_metrics:
        clinical = polyp_clinical_metrics(labels, prob_matrix, class_names, args.target_specificity)
        if clinical:
            report_dict["clinical"] = clinical
            print(
                f"\nPolyp ROC-AUC: {clinical['polyp_roc_auc']:.4f} | "
                f"PR-AUC: {clinical['polyp_pr_auc']:.4f} | "
                f"Sens@{clinical['target_specificity']:.2f} spec: "
                f"{clinical['polyp_sensitivity_at_target_specificity']:.4f}"
            )

    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report_dict, indent=2))
        print(f"\nReport saved: {out}")


if __name__ == "__main__":
    main()
