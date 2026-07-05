#!/usr/bin/env bash
# Cross-dataset external validation: Kvasir <-> HyperKvasir (3-class T3).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

CROSS="data/colonoscopy_3class/cross"
RESULTS="benchmarks/ml/results"
CKPT="checkpoints/cross_dataset"
DEVICE="${DEVICE:-auto}"
EPOCHS="${EPOCHS:-20}"
PATIENCE="${PATIENCE:-5}"

mkdir -p "$CKPT" "$RESULTS"

python3 scripts/prepare_cross_dataset_splits.py --output "$CROSS"

run_direction() {
  local tag="$1"
  local data_dir="$CROSS/$tag"
  local out_prefix="$RESULTS/cross_${tag}"

  echo "=== Cross-dataset: $tag (C1 ImageNet) ==="
  pixi run train -- \
    --data-dir "$data_dir" --arch seresnet50 --pretrained \
    --epochs "$EPOCHS" --patience "$PATIENCE" --pretrain-method imagenet \
    --seed 42 --output "$CKPT/${tag}_c1.pt" --device "$DEVICE"
  pixi run evaluate -- \
    --checkpoint "$CKPT/${tag}_c1.pt" --data-dir "$data_dir" --split test \
    --clinical-metrics --output "${out_prefix}_c1_test.json" --device "$DEVICE"

  echo "=== Cross-dataset: $tag (C4 JEPA) ==="
  pixi run train -- \
    --data-dir "$data_dir" --arch seresnet50 --mask-aware-se \
    --jepa-checkpoint checkpoints/jepa/c4_mask_aware_shared.pt \
    --epochs "$EPOCHS" --patience "$PATIENCE" --pretrain-method cnn_jepa_mask_aware \
    --seed 42 --output "$CKPT/${tag}_c4.pt" --device "$DEVICE"
  pixi run evaluate -- \
    --checkpoint "$CKPT/${tag}_c4.pt" --data-dir "$data_dir" --split test \
    --clinical-metrics --output "${out_prefix}_c4_test.json" --device "$DEVICE"
}

run_direction kvasir_train_hyperkvasir_test
run_direction hyperkvasir_train_kvasir_test

echo "Cross-dataset evaluation complete."
