"""Training loop shared by script_ResNet.py and optuna_search.py."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional

import torch
import torch.nn as nn
import torch.optim as optim
from torch.optim.lr_scheduler import CosineAnnealingLR, StepLR
from tqdm import tqdm

from data import get_data_loaders
from early_stopping import EarlyStopping, EarlyStoppingConfig
from model import ARCH_NAME as LEGACY_ARCH
from models.registry import build_model, is_dual_stream


def _subsample_train_indices(dataset, fraction: float, seed: int) -> list[int]:
    if fraction >= 1.0:
        return list(range(len(dataset)))
    from collections import defaultdict

    by_class: dict[int, list[int]] = defaultdict(list)
    for idx, (_, target) in enumerate(dataset.samples):
        by_class[target].append(idx)
    rng = __import__("random").Random(seed)
    chosen: list[int] = []
    for indices in by_class.values():
        n = max(1, int(len(indices) * fraction))
        chosen.extend(rng.sample(indices, min(n, len(indices))))
    rng.shuffle(chosen)
    return chosen


@dataclass
class TrainConfig:
    data_dir: str
    epochs: int = 20
    batch_size: int = 16
    lr: float = 1e-3
    weight_decay: float = 1e-4
    img_size: int = 224
    num_classes: int = 4
    optimizer: str = "adamw"
    scheduler: str = "none"
    label_smoothing: float = 0.0
    seed: int = 42
    num_workers: int = 0
    device: str = "auto"
    arch: str = "resnet50"
    pretrained: bool = False
    early_stopping: EarlyStoppingConfig | None = None
    jepa_checkpoint: str = ""
    mask_aware_se: bool = False
    label_fraction: float = 1.0


@dataclass
class TrainResult:
    best_val_acc: float = 0.0
    best_val_macro_f1: float = 0.0
    best_state_dict: Optional[dict] = None
    class_names: list[str] = field(default_factory=list)
    history: list[dict] = field(default_factory=list)
    stopped_epoch: int | None = None
    stop_reason: str | None = None
    early_stop: EarlyStopping | None = None


def resolve_device(device: str) -> torch.device:
    if device == "auto":
        if torch.cuda.is_available():
            return torch.device("cuda")
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return torch.device("mps")
        return torch.device("cpu")
    return torch.device(device)


def build_optimizer(model: nn.Module, config: TrainConfig) -> optim.Optimizer:
    params = filter(lambda p: p.requires_grad, model.parameters())
    if config.optimizer.lower() == "sgd":
        return optim.SGD(params, lr=config.lr, weight_decay=config.weight_decay, momentum=0.9)
    return optim.AdamW(params, lr=config.lr, weight_decay=config.weight_decay)


def build_scheduler(optimizer: optim.Optimizer, config: TrainConfig):
    if config.scheduler == "cosine":
        return CosineAnnealingLR(optimizer, T_max=config.epochs)
    if config.scheduler == "step":
        return StepLR(optimizer, step_size=max(1, config.epochs // 3), gamma=0.1)
    return None


def _forward(model, inputs, dual: bool):
    if dual:
        rgb, texture = inputs
        return model(rgb, texture)
    return model(inputs)


def train_one_epoch(model, dataloader, criterion, optimizer, device, dual: bool = False) -> tuple[float, float]:
    model.train()
    running_loss = 0.0
    running_corrects = 0
    total = 0
    for batch in tqdm(dataloader, desc="Train", leave=False):
        if dual:
            (inputs, labels) = batch
            rgb, texture = inputs
            rgb = rgb.to(device, non_blocking=True)
            texture = texture.to(device, non_blocking=True)
            labels = labels.to(device, non_blocking=True)
            optimizer.zero_grad()
            outputs = model(rgb, texture)
        else:
            inputs, labels = batch
            inputs = inputs.to(device, non_blocking=True)
            labels = labels.to(device, non_blocking=True)
            optimizer.zero_grad()
            outputs = model(inputs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        _, preds = torch.max(outputs, 1)
        batch_size = labels.size(0)
        running_loss += loss.item() * batch_size
        running_corrects += torch.sum(preds == labels.data)
        total += batch_size
    return running_loss / total, (running_corrects.float() / total).item()


def validate(model, dataloader, criterion, device, dual: bool = False) -> tuple[float, float, list[int], list[int]]:
    model.eval()
    running_loss = 0.0
    running_corrects = 0
    total = 0
    all_preds: list[int] = []
    all_labels: list[int] = []
    with torch.no_grad():
        for batch in tqdm(dataloader, desc="Val", leave=False):
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
            loss = criterion(outputs, labels)
            _, preds = torch.max(outputs, 1)
            batch_size = labels.size(0)
            running_loss += loss.item() * batch_size
            running_corrects += torch.sum(preds == labels.data)
            total += batch_size
            all_preds.extend(preds.cpu().tolist())
            all_labels.extend(labels.cpu().tolist())
    acc = (running_corrects.float() / total).item()
    return running_loss / total, acc, all_preds, all_labels


def macro_f1(preds: list[int], labels: list[int], num_classes: int) -> float:
    from sklearn.metrics import f1_score
    return float(f1_score(labels, preds, average="macro", zero_division=0, labels=list(range(num_classes))))


def run_training(
    config: TrainConfig,
    epoch_callback: Optional[Callable[[int, float, float, float], None]] = None,
) -> TrainResult:
    torch.manual_seed(config.seed)
    device = resolve_device(config.device)
    dual = is_dual_stream(config.arch)

    train_loader, val_loader, class_names = get_data_loaders(
        config.data_dir,
        config.batch_size,
        config.img_size,
        config.num_workers,
        dual_stream=dual,
    )
    if config.label_fraction < 1.0:
        from torch.utils.data import Subset

        base_ds = train_loader.dataset
        indices = _subsample_train_indices(base_ds, config.label_fraction, config.seed)
        train_loader = torch.utils.data.DataLoader(
            Subset(base_ds, indices),
            batch_size=config.batch_size,
            shuffle=True,
            num_workers=config.num_workers,
            pin_memory=torch.cuda.is_available(),
        )
    num_classes = len(class_names) if class_names else config.num_classes
    model = build_model(
        config.arch,
        num_classes=num_classes,
        pretrained=config.pretrained,
        mask_aware_se=config.mask_aware_se,
    ).to(device)

    if config.jepa_checkpoint:
        from models.registry import load_jepa_into_classifier

        load_jepa_into_classifier(model, config.jepa_checkpoint, device=str(device))

    criterion = nn.CrossEntropyLoss(label_smoothing=config.label_smoothing)
    optimizer = build_optimizer(model, config)
    scheduler = build_scheduler(optimizer, config)

    es_cfg = config.early_stopping or EarlyStoppingConfig(
        max_epochs=config.epochs,
        min_epochs=min(5, config.epochs),
        patience=max(3, config.epochs // 4),
    )
    es_cfg.max_epochs = min(es_cfg.max_epochs, config.epochs)
    early_stop = EarlyStopping(es_cfg)

    result = TrainResult(class_names=class_names)
    best_wts = None

    for epoch in range(1, es_cfg.max_epochs + 1):
        train_loss, train_acc = train_one_epoch(model, train_loader, criterion, optimizer, device, dual=dual)
        val_loss, val_acc, val_preds, val_labels = validate(model, val_loader, criterion, device, dual=dual)
        val_f1 = macro_f1(val_preds, val_labels, num_classes)

        if scheduler is not None:
            scheduler.step()

        result.history.append({
            "epoch": epoch,
            "train_loss": train_loss,
            "train_acc": train_acc,
            "val_loss": val_loss,
            "val_acc": val_acc,
            "val_macro_f1": val_f1,
        })

        if epoch_callback is not None:
            epoch_callback(epoch, val_acc, val_f1, val_loss)

        is_best, should_stop = early_stop.step(epoch, {"val_macro_f1": val_f1, "val_latent_loss": val_loss})
        if is_best:
            result.best_val_macro_f1 = val_f1
            result.best_val_acc = val_acc
            best_wts = {k: v.cpu().clone() for k, v in model.state_dict().items()}

        if should_stop:
            result.stopped_epoch = early_stop.state.stopped_epoch
            result.stop_reason = early_stop.state.stop_reason
            break

    result.early_stop = early_stop
    result.best_state_dict = best_wts
    return result
