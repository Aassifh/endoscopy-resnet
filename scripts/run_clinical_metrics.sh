#!/usr/bin/env bash
# Re-evaluate C-series checkpoints with polyp ROC/PR and sensitivity@95% specificity.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

DATA="data/colonoscopy_3class/all"
RESULTS="benchmarks/ml/results"
DEVICE="${DEVICE:-auto}"

for run in C0 C1 C2 C3 C4 C5 C7 C8 C9; do
  ckpt="checkpoints/jepa/${run}_fold_simula.pt"
  out="${RESULTS}/${run}_fold_simula_clinical_test.json"
  if [[ ! -f "$ckpt" ]]; then
    echo "Skip $run — missing $ckpt"
    continue
  fi
  echo "=== Clinical metrics: $run ==="
  pixi run evaluate -- \
    --checkpoint "$ckpt" --data-dir "$DATA" --split test \
    --clinical-metrics --target-specificity 0.95 \
    --output "$out" --device "$DEVICE"
done

echo "Clinical metrics complete."
