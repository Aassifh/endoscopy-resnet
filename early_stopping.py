"""Early stopping utilities for supervised and JEPA training."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Literal


@dataclass
class EarlyStoppingConfig:
    monitor: str = "val_macro_f1"
    mode: Literal["min", "max"] = "max"
    patience: int = 5
    min_epochs: int = 5
    max_epochs: int = 30
    min_delta: float = 0.005

    @classmethod
    def pretrain_jepa(cls) -> EarlyStoppingConfig:
        return cls(
            monitor="val_latent_loss",
            mode="min",
            patience=10,
            min_epochs=20,
            max_epochs=80,
            min_delta=1e-4,
        )

    @classmethod
    def finetune(cls) -> EarlyStoppingConfig:
        return cls(
            monitor="val_macro_f1",
            mode="max",
            patience=5,
            min_epochs=5,
            max_epochs=30,
            min_delta=0.005,
        )

    @classmethod
    def linear_probe(cls) -> EarlyStoppingConfig:
        return cls(
            monitor="val_macro_f1",
            mode="max",
            patience=3,
            min_epochs=3,
            max_epochs=15,
            min_delta=0.005,
        )


@dataclass
class EarlyStoppingState:
    best_value: float = field(default_factory=lambda: float("inf"))
    best_epoch: int = 0
    wait: int = 0
    stopped_epoch: int | None = None
    stop_reason: str | None = None

    def __post_init__(self) -> None:
        if self.best_value == float("inf"):
            pass


class EarlyStopping:
    def __init__(self, config: EarlyStoppingConfig):
        self.config = config
        self.state = EarlyStoppingState(
            best_value=float("inf") if config.mode == "min" else float("-inf")
        )

    def _is_improvement(self, value: float) -> bool:
        if self.config.mode == "min":
            return value < self.state.best_value - self.config.min_delta
        return value > self.state.best_value + self.config.min_delta

    def step(self, epoch: int, metrics: dict[str, float]) -> tuple[bool, bool]:
        """Return (is_best, should_stop)."""
        value = metrics[self.config.monitor]

        if self._is_improvement(value):
            self.state.best_value = value
            self.state.best_epoch = epoch
            self.state.wait = 0
            is_best = True
        else:
            self.state.wait += 1
            is_best = False

        should_stop = False
        if epoch >= self.config.max_epochs:
            self.state.stopped_epoch = epoch
            self.state.stop_reason = "max_epochs"
            should_stop = True
        elif epoch >= self.config.min_epochs and self.state.wait >= self.config.patience:
            self.state.stopped_epoch = epoch
            self.state.stop_reason = "patience"
            should_stop = True

        return is_best, should_stop

    def save_report(self, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "config": asdict(self.config),
            "state": asdict(self.state),
        }
        path.write_text(json.dumps(payload, indent=2))
