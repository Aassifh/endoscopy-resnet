#!/usr/bin/env python3
"""Run inference on endoscopy images using a trained checkpoint."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import torch
from PIL import Image
from torchvision import transforms

from checkpoint import load_checkpoint
from data import IMAGENET_MEAN, IMAGENET_STD


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Endoscopy image inference")
    p.add_argument("--checkpoint", type=str, default="checkpoints/resnet_scratch.pt")
    p.add_argument("--image", type=str, default="", help="Single image path")
    p.add_argument("--image-dir", type=str, default="images_test", help="Directory of test images")
    p.add_argument("--device", type=str, default="cpu")
    return p.parse_args()


def build_infer_transform(img_size: int = 224) -> transforms.Compose:
    return transforms.Compose([
        transforms.Resize(int(img_size * 256 / 224)),
        transforms.CenterCrop(img_size),
        transforms.ToTensor(),
        transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
    ])


def predict_image(model, image_path: str, transform, device, class_names: list[str]) -> tuple[int, str]:
    img = Image.open(image_path).convert("RGB")
    tensor = transform(img).unsqueeze(0).to(device)
    with torch.no_grad():
        outputs = model(tensor)
        pred_idx = int(torch.max(outputs, 1)[1].item())
    label = class_names[pred_idx] if pred_idx < len(class_names) else str(pred_idx)
    return pred_idx, label


def main() -> None:
    args = parse_args()
    device = torch.device(args.device)
    model, meta = load_checkpoint(args.checkpoint, map_location=device)
    model = model.to(device)

    class_names = meta.get("class_names") or ["cecum", "pylorus", "polyp", "ulcer"]
    img_size = meta.get("hparams", {}).get("img_size", 224)
    transform = build_infer_transform(img_size)

    paths: list[str] = []
    if args.image:
        paths.append(args.image)
    elif os.path.isdir(args.image_dir):
        for name in sorted(os.listdir(args.image_dir)):
            full = os.path.join(args.image_dir, name)
            if os.path.isfile(full):
                paths.append(full)
    else:
        raise FileNotFoundError(f"No images found: {args.image or args.image_dir}")

    print(f"Checkpoint: {args.checkpoint}")
    print(f"Classes:    {class_names}\n")

    for path in paths:
        idx, label = predict_image(model, path, transform, device, class_names)
        print(f"{Path(path).name}: index={idx}, class={label}")


if __name__ == "__main__":
    main()
