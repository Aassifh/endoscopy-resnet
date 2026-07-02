#!/usr/bin/env bash
# Run a single LOO benchmark condition (C0–C10) with early stopping and JSON output.
#
# Usage:
#   ./scripts/run_loo_benchmark.sh C4 fold_simula
#   ./scripts/run_loo_benchmark.sh C8 fold_center_a --label-fraction 0.25

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

CONDITION="${1:?Condition C0-C10 required}"
FOLD="${2:?Fold id required (e.g. fold_simula)}"
shift 2 || true

LABEL_FRACTION=""
EXTRA=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --label-fraction) LABEL_FRACTION="$2"; shift 2 ;;
    *) EXTRA+=("$1"); shift ;;
  esac
done

DATA_DIR="data/colonoscopy_3class/folds/${FOLD}"
RESULTS_DIR="benchmarks/ml/results"
RUN_ID="${CONDITION}_${FOLD}"
OUT_JSON="${RESULTS_DIR}/${RUN_ID}_test.json"
CKPT="checkpoints/jepa/${RUN_ID}.pt"
JEPA_CKPT="checkpoints/jepa/c4_mask_aware_shared.pt"

mkdir -p "$RESULTS_DIR" checkpoints/jepa

if [[ -f "$OUT_JSON" ]]; then
  echo "Result exists, skip: $OUT_JSON"
  exit 0
fi

MAX_EPOCHS=30
PATIENCE=5

train_common=(
  --data-dir "$DATA_DIR"
  --epochs "$MAX_EPOCHS"
  --patience "$PATIENCE"
  --center-split "$FOLD"
  --output "$CKPT"
)

case "$CONDITION" in
  C0)
    pixi run train -- "${train_common[@]}" --arch seresnet50 --pretrain-method scratch
    ;;
  C1)
    pixi run train -- "${train_common[@]}" --arch seresnet50 --pretrained --pretrain-method imagenet
    ;;
  C2)
    pixi run train -- "${train_common[@]}" --arch resnet50 --jepa-checkpoint "$JEPA_CKPT" --pretrain-method cnn_jepa_resnet
    ;;
  C3)
    pixi run train -- "${train_common[@]}" --arch seresnet50 --jepa-checkpoint "$JEPA_CKPT" --pretrain-method cnn_jepa_se_standard
    ;;
  C4|C10)
    pixi run train -- "${train_common[@]}" --arch seresnet50 --mask-aware-se \
      --jepa-checkpoint "$JEPA_CKPT" --pretrain-method cnn_jepa_mask_aware
    ;;
  C5)
    pixi run train -- "${train_common[@]}" --arch seresnet50 --mask-aware-se \
      --jepa-checkpoint "$JEPA_CKPT" --pretrain-method frozen_teacher
    ;;
  C6)
    echo "C6 ViT foundation linear probe — placeholder; use external ViT checkpoint when available."
    exit 2
    ;;
  C7|C8|C9)
    frac="${LABEL_FRACTION:-0.25}"
    [[ "$CONDITION" == "C7" ]] && frac=0.10
    [[ "$CONDITION" == "C8" ]] && frac=0.25
    [[ "$CONDITION" == "C9" ]] && frac=0.50
    pixi run train -- "${train_common[@]}" --arch seresnet50 --mask-aware-se \
      --jepa-checkpoint "$JEPA_CKPT" --pretrain-method cnn_jepa_mask_aware \
      --label-fraction "$frac"
    ;;
  *)
    echo "Unknown condition: $CONDITION"
    exit 1
    ;;
esac

pixi run evaluate -- \
  --checkpoint "$CKPT" \
  --data-dir "$DATA_DIR" \
  --split test \
  --output "$OUT_JSON"

echo "Done: $OUT_JSON"
