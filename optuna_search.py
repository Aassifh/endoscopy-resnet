#!/usr/bin/env python3
"""Optuna hyperparameter search for endoscopy ResNet training."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import optuna
from optuna.pruners import MedianPruner

from checkpoint import build_checkpoint, save_checkpoint
from training import TrainConfig, run_training


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Optuna HPO for endoscopy ResNet")
    p.add_argument("--data-dir", type=str, required=True)
    p.add_argument("--trials", type=int, default=20)
    p.add_argument("--epochs-per-trial", type=int, default=12)
    p.add_argument("--study-name", type=str, default="endoscopy_resnet")
    p.add_argument("--storage", type=str, default="sqlite:///optuna_endoscopy.db")
    p.add_argument("--output-dir", type=str, default="checkpoints/optuna")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--device", type=str, default="auto")
    return p.parse_args()


def create_objective(data_dir: str, epochs: int, seed: int, device: str):
    def objective(trial: optuna.Trial) -> float:
        config = TrainConfig(
            data_dir=data_dir,
            epochs=epochs,
            batch_size=trial.suggest_categorical("batch_size", [8, 16, 32]),
            lr=trial.suggest_float("lr", 1e-5, 1e-2, log=True),
            weight_decay=trial.suggest_float("weight_decay", 1e-6, 1e-2, log=True),
            img_size=trial.suggest_categorical("img_size", [224, 256]),
            optimizer=trial.suggest_categorical("optimizer", ["adamw", "sgd"]),
            scheduler=trial.suggest_categorical("scheduler", ["none", "cosine", "step"]),
            label_smoothing=trial.suggest_float("label_smoothing", 0.0, 0.2),
            seed=seed + trial.number,
            device=device,
        )

        def on_epoch(epoch: int, val_acc: float, val_f1: float, val_loss: float) -> None:
            trial.report(val_f1, epoch)
            if trial.should_prune():
                raise optuna.TrialPruned()

        result = run_training(config, epoch_callback=on_epoch)
        trial.set_user_attr("best_val_acc", result.best_val_acc)
        trial.set_user_attr("class_names", result.class_names)
        return result.best_val_macro_f1

    return objective


def main() -> None:
    args = parse_args()
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    study = optuna.create_study(
        study_name=args.study_name,
        storage=args.storage,
        load_if_exists=True,
        direction="maximize",
        pruner=MedianPruner(n_startup_trials=3, n_warmup_steps=2),
    )

    study.optimize(
        create_objective(args.data_dir, args.epochs_per_trial, args.seed, args.device),
        n_trials=args.trials,
        show_progress_bar=True,
    )

    best = study.best_trial
    print("\n=== Best trial ===")
    print(f"  Trial:      {best.number}")
    print(f"  Macro-F1:   {best.value:.4f}")
    print(f"  Val acc:    {best.user_attrs.get('best_val_acc', 'n/a')}")
    print(f"  Params:     {best.params}")

    best_params_path = out_dir / "best_params.json"
    best_params_path.write_text(json.dumps({
        "trial_number": best.number,
        "macro_f1": best.value,
        "params": best.params,
        "user_attrs": best.user_attrs,
    }, indent=2))

    # Retrain best config with full epoch budget for export
    best_config = TrainConfig(
        data_dir=args.data_dir,
        epochs=args.epochs_per_trial,
        batch_size=best.params["batch_size"],
        lr=best.params["lr"],
        weight_decay=best.params["weight_decay"],
        img_size=best.params["img_size"],
        optimizer=best.params["optimizer"],
        scheduler=best.params["scheduler"],
        label_smoothing=best.params["label_smoothing"],
        seed=args.seed,
        device=args.device,
    )
    result = run_training(best_config)
    if result.best_state_dict is None:
        raise RuntimeError("Best trial retrain failed.")

    ckpt_path = out_dir / "best_optuna.pt"
    save_checkpoint(
        build_checkpoint(
            result.best_state_dict,
            result.class_names,
            {**best.params, "epochs": args.epochs_per_trial, "seed": args.seed},
            {"best_val_acc": result.best_val_acc, "best_val_macro_f1": result.best_val_macro_f1},
            epoch=args.epochs_per_trial,
        ),
        ckpt_path,
    )
    print(f"\nBest checkpoint: {ckpt_path}")
    print(f"Best params JSON: {best_params_path}")


if __name__ == "__main__":
    main()
