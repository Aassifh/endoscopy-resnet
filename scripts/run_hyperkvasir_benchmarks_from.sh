#!/usr/bin/env bash
# Resume B3–B6 (skip B2 if already done).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DATA="${DATA_DIR:-$ROOT/data/hyperkvasir}"
EPOCHS="${EPOCHS:-15}"
DEVICE="${DEVICE:-auto}"
RESULTS="$ROOT/benchmarks/ml/results"
CKPT="$ROOT/checkpoints/hyperkvasir"

mkdir -p "$CKPT" "$RESULTS"

run_one() {
  local id="$1" arch="$2" pretrain="$3" out="$4"
  if [[ -f "$RESULTS/hyperkvasir_${out}_test.json" ]]; then
    echo "=== $id: skip (results exist) ==="
    return 0
  fi
  echo "=== $id: $arch pretrained=$pretrain ==="
  if [[ "$pretrain" == "1" ]]; then
    pixi run train -- \
      --data-dir "$DATA" --arch "$arch" --pretrained \
      --epochs "$EPOCHS" --batch-size 16 --output "$CKPT/${out}.pt" --device "$DEVICE"
  else
    pixi run train -- \
      --data-dir "$DATA" --arch "$arch" \
      --epochs "$EPOCHS" --batch-size 16 --output "$CKPT/${out}.pt" --device "$DEVICE"
  fi
  for split in val test; do
    pixi run evaluate -- \
      --checkpoint "$CKPT/${out}.pt" --data-dir "$DATA" --split "$split" \
      --output "$RESULTS/hyperkvasir_${out}_${split}.json" --device "$DEVICE"
  done
}

run_one B3 seresnet50 0 b3_seresnet50_scratch
run_one B4 seresnet50 1 b4_seresnet50_imagenet
run_one B5 dualstream_resnet_color_texture 0 b5_dualstream_scratch
run_one B6 dualstream_resnet_color_texture 1 b6_dualstream_imagenet

echo "All HyperKvasir benchmarks complete."
