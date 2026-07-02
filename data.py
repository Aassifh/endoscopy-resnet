"""Dataset loaders and transforms for endoscopy ImageFolder layout."""

from __future__ import annotations

import os
from typing import Tuple

import torch
from PIL import Image
from torch.utils.data import DataLoader, Dataset
from torchvision import datasets, transforms

from texture import texture_to_tensor

IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]

TEXTURE_MEAN = [0.5, 0.5, 0.5]
TEXTURE_STD = [0.5, 0.5, 0.5]


def build_transforms(img_size: int, train: bool) -> transforms.Compose:
    if train:
        return transforms.Compose([
            transforms.RandomResizedCrop(img_size),
            transforms.RandomHorizontalFlip(),
            transforms.RandomVerticalFlip(),
            transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2, hue=0.1),
            transforms.ToTensor(),
            transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
        ])
    return transforms.Compose([
        transforms.Resize(int(img_size * 256 / 224)),
        transforms.CenterCrop(img_size),
        transforms.ToTensor(),
        transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
    ])


class DualStreamDataset(Dataset):
    """ImageFolder samples with paired RGB and color-texture tensors."""

    def __init__(self, root: str, rgb_transform: transforms.Compose, img_size: int):
        self.base = datasets.ImageFolder(root)
        self.rgb_transform = rgb_transform
        self.img_size = img_size
        self.classes = self.base.classes
        self.class_to_idx = self.base.class_to_idx
        self.samples = self.base.samples
        self.texture_norm = transforms.Normalize(mean=TEXTURE_MEAN, std=TEXTURE_STD)

    def __len__(self) -> int:
        return len(self.base)

    def _texture_from_pil(self, pil: Image.Image) -> torch.Tensor:
        pil = pil.resize((self.img_size, self.img_size), Image.BILINEAR)
        import numpy as np
        arr = np.array(pil.convert("RGB"))
        tex = texture_to_tensor(arr)
        return self.texture_norm(tex)

    def __getitem__(self, index: int):
        path, target = self.samples[index]
        pil = Image.open(path).convert("RGB")
        rgb = self.rgb_transform(pil)
        texture = self._texture_from_pil(pil)
        return (rgb, texture), target


def get_data_loaders(
    data_dir: str,
    batch_size: int,
    img_size: int = 224,
    num_workers: int = 0,
    dual_stream: bool = False,
) -> Tuple[DataLoader, DataLoader, list[str]]:
    train_dir = os.path.join(data_dir, "train")
    val_dir = os.path.join(data_dir, "val")

    if dual_stream:
        train_dataset = DualStreamDataset(train_dir, build_transforms(img_size, train=True), img_size)
        val_dataset = DualStreamDataset(val_dir, build_transforms(img_size, train=False), img_size)
        class_names = train_dataset.classes
    else:
        train_dataset = datasets.ImageFolder(train_dir, transform=build_transforms(img_size, train=True))
        val_dataset = datasets.ImageFolder(val_dir, transform=build_transforms(img_size, train=False))
        class_names = train_dataset.classes

    pin = torch.cuda.is_available()
    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=pin,
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=pin,
    )
    return train_loader, val_loader, class_names


def get_eval_loader(
    data_dir: str,
    split: str,
    batch_size: int,
    img_size: int = 224,
    num_workers: int = 0,
    dual_stream: bool = False,
) -> tuple[DataLoader, list[str]]:
    """Load a single split (val/ or test/) for evaluation."""
    split_dir = os.path.join(data_dir, split)
    if dual_stream:
        dataset = DualStreamDataset(split_dir, build_transforms(img_size, train=False), img_size)
    else:
        dataset = datasets.ImageFolder(split_dir, transform=build_transforms(img_size, train=False))
    loader = DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=torch.cuda.is_available(),
    )
    return loader, dataset.classes
