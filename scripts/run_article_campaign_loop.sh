#!/usr/bin/env bash
# Orchestrate CNN-JEPA article campaign (C0–C10) with persistent state and skip-if-done.
#
# Usage:
#   ./scripts/run_article_campaign_loop.sh              # run next pending job
#   ./scripts/run_article_campaign_loop.sh --init       # reset queue
#   ./scripts/run_article_campaign_loop.sh --status       # print state
#   ./scripts/run_article_campaign_loop.sh --smoke        # smoke test (subset)
#
# Sentinel for /loop watcher:
#   AGENT_LOOP_TICK_jepa — re-run this script when GPU idle.

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

STATE_FILE="benchmarks/ml/results/jepa_campaign_state.json"
RESULTS_DIR="benchmarks/ml/results"
DATA_ALL="data/colonoscopy_3class/all"
JEPA_CKPT="checkpoints/jepa/c4_mask_aware_shared.pt"
JEPA_CKPT_RESNET="checkpoints/jepa/c2_resnet_jepa_shared.pt"
BENCHMARK_SEED="${BENCHMARK_SEED:-42}"

result_json_path() {
  local run_id="$1"
  if [[ "$BENCHMARK_SEED" == "42" ]]; then
    echo "${RESULTS_DIR}/${run_id}_test.json"
  else
    echo "${RESULTS_DIR}/${run_id}_seed${BENCHMARK_SEED}_test.json"
  fi
}

resolve_jepa_frames() {
  for d in data/jepa_frames/hyperkvasir_unlabeled data/jepa_frames; do
    if [[ -d "$d" ]] && [[ -n "$(find "$d" \( -name '*.jpg' -o -name '*.jpeg' -o -name '*.png' \) 2>/dev/null | head -1)" ]]; then
      echo "$d"
      return
    fi
  done
  echo "$DATA_ALL/train"
}

resolve_data_dir() {
  local fold="$1"
  local fold_dir="data/colonoscopy_3class/folds/${fold}"
  local train_count
  train_count=$(find "$fold_dir/train" \( -name '*.jpg' -o -name '*.jpeg' -o -name '*.png' \) 2>/dev/null | wc -l | tr -d ' ')
  if [[ "${train_count:-0}" -lt 10 ]]; then
    echo "$DATA_ALL"
  else
    echo "$fold_dir"
  fi
}
SMOKE=false
INIT=false
STATUS_ONLY=false
FORCE=false
RUN_ALL=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --smoke) SMOKE=true; shift ;;
    --init) INIT=true; shift ;;
    --status) STATUS_ONLY=true; shift ;;
    --force) FORCE=true; shift ;;
    --all) RUN_ALL=true; shift ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

mkdir -p "$RESULTS_DIR" checkpoints/jepa

default_queue() {
  python3 - <<'PY'
import json
centers = []
try:
    import pathlib
    m = pathlib.Path("data/colonoscopy_3class/manifest.json")
    if m.exists():
        centers = json.loads(m.read_text())["centers"]
except Exception:
    centers = ["simula"]
folds = [f"fold_{c}" for c in centers] if centers else ["fold_simula"]
queue = []
# Shared pretrain (SE mask-aware + ResNet for C2)
queue.append("pretrain_c4_shared")
queue.append("pretrain_c2_resnet_shared")
# Core screening runs C0--C5 on each fold
for fold in folds:
    for c in ("C0", "C1", "C2", "C3", "C4", "C5"):
        queue.append(f"{c}_{fold}")
# Label-efficiency C7--C9 on first fold
for pct in (10, 25, 50):
    queue.append(f"C{7 if pct==10 else 8 if pct==25 else 9}_{folds[0]}")
print(json.dumps({
    "phase": "pretrain_shared",
    "queue": queue,
    "completed": [],
    "current": None,
    "early_stop_defaults": {"max_epochs": 30, "patience": 5, "pretrain_max_epochs": 80, "pretrain_patience": 10},
}))
PY
}

if $FORCE; then
  rm -f "${RESULTS_DIR}"/C*_test.json "${RESULTS_DIR}"/C*_seed*_test.json
  rm -rf checkpoints/jepa/C*.pt checkpoints/jepa/c*_shared.pt 2>/dev/null || true
  default_queue > "$STATE_FILE"
  echo "Force reset: cleared JEPA results and re-initialized queue."
fi

if $INIT || [[ ! -f "$STATE_FILE" ]]; then
  default_queue > "$STATE_FILE"
  echo "Initialized $STATE_FILE"
fi

if $INIT; then
  exit 0
fi

if $STATUS_ONLY; then
  cat "$STATE_FILE"
  exit 0
fi

run_id="$(python3 - <<PY
import json
s = json.load(open("$STATE_FILE"))
for job in s["queue"]:
    if job not in s.get("completed", []):
        print(job)
        break
PY
)"

if [[ -z "${run_id:-}" ]]; then
  echo "Campaign complete. All jobs in completed list."
  exit 0
fi

result_json="$(result_json_path "$run_id")"
if [[ -f "$result_json" ]]; then
  echo "Skip $run_id — $result_json exists"
  python3 - <<PY
import json
s = json.load(open("$STATE_FILE"))
if "$run_id" not in s["completed"]:
    s["completed"].append("$run_id")
    s["current"] = None
    json.dump(s, open("$STATE_FILE", "w"), indent=2)
PY
  exit 0
fi

echo "=== Running $run_id ==="
python3 - <<PY
import json
s = json.load(open("$STATE_FILE"))
s["current"] = "$run_id"
json.dump(s, open("$STATE_FILE", "w"), indent=2)
PY

MAX_EPOCHS=30
PATIENCE=5
PRETRAIN_MAX=40
PRETRAIN_PAT=8
PRETRAIN_SAMPLES=4000
PRETRAIN_BATCH=16
if $SMOKE; then
  MAX_EPOCHS=5
  PRETRAIN_MAX=10
  PATIENCE=2
  PRETRAIN_PAT=2
fi

case "$run_id" in
  pretrain_c4_shared)
    FRAMES="$(resolve_jepa_frames)"
    if [[ "$FRAMES" == "$DATA_ALL/train" ]]; then
      echo "No dedicated JEPA frames; using labeled train images as proxy for pretrain."
    fi
    pixi run pretrain-jepa -- \
      --frames-dir "$FRAMES" \
      --backbone seresnet50 \
      --mask-aware-se \
      --output "$JEPA_CKPT" \
      --max-epochs "$PRETRAIN_MAX" \
      --patience "$PRETRAIN_PAT" \
      --batch-size "$PRETRAIN_BATCH" \
      --max-samples $($SMOKE && echo 500 || echo "$PRETRAIN_SAMPLES") \
      --seed "$BENCHMARK_SEED"
    ;;
  C0_*)
    fold="${run_id#C0_}"
    data_dir="$(resolve_data_dir "$fold")"
    pixi run train -- \
      --data-dir "$data_dir" \
      --arch seresnet50 \
      --epochs "$MAX_EPOCHS" --patience "$PATIENCE" \
      --pretrain-method scratch \
      --center-split "$fold" \
      --seed "$BENCHMARK_SEED" \
      --output "checkpoints/jepa/${run_id}.pt"
    pixi run evaluate -- \
      --checkpoint "checkpoints/jepa/${run_id}.pt" \
      --data-dir "$data_dir" \
      --split test \
      --output "$result_json"
    ;;
  C1_*)
    fold="${run_id#C1_}"
    data_dir="$(resolve_data_dir "$fold")"
    pixi run train -- \
      --data-dir "$data_dir" \
      --arch seresnet50 --pretrained \
      --epochs "$MAX_EPOCHS" --patience "$PATIENCE" \
      --pretrain-method imagenet \
      --center-split "$fold" \
      --seed "$BENCHMARK_SEED" \
      --output "checkpoints/jepa/${run_id}.pt"
    pixi run evaluate -- \
      --checkpoint "checkpoints/jepa/${run_id}.pt" \
      --data-dir "$data_dir" \
      --split test \
      --output "$result_json"
    ;;
  pretrain_c2_resnet_shared)
    FRAMES="$(resolve_jepa_frames)"
    if [[ "$FRAMES" == "$DATA_ALL/train" ]]; then
      echo "No dedicated JEPA frames; using labeled train images as proxy for ResNet pretrain."
    fi
    pixi run pretrain-jepa -- \
      --frames-dir "$FRAMES" \
      --backbone resnet50 \
      --output "$JEPA_CKPT_RESNET" \
      --max-epochs "$PRETRAIN_MAX" \
      --patience "$PRETRAIN_PAT" \
      --batch-size "$PRETRAIN_BATCH" \
      --max-samples $($SMOKE && echo 500 || echo "$PRETRAIN_SAMPLES") \
      --seed "$BENCHMARK_SEED"
    ;;
  C2_*)
    fold="${run_id#C2_}"
    data_dir="$(resolve_data_dir "$fold")"
    pixi run train -- \
      --data-dir "$data_dir" \
      --arch resnet50 \
      --jepa-checkpoint "$JEPA_CKPT_RESNET" \
      --epochs "$MAX_EPOCHS" --patience "$PATIENCE" \
      --pretrain-method cnn_jepa_resnet \
      --center-split "$fold" \
      --seed "$BENCHMARK_SEED" \
      --output "checkpoints/jepa/${run_id}.pt"
    pixi run evaluate -- \
      --checkpoint "checkpoints/jepa/${run_id}.pt" \
      --data-dir "$data_dir" \
      --split test \
      --output "$result_json"
    ;;
  C3_*|C4_*|C5_*)
    fold="${run_id#*_}"
    data_dir="$(resolve_data_dir "$fold")"
    cid="${run_id%%_*}"
    mask_flag=""
    jepa="$JEPA_CKPT"
    pretrain_method="cnn_jepa"
    if [[ "$cid" == "C3" ]]; then
      mask_flag=""
      pretrain_method="cnn_jepa_se_standard"
    elif [[ "$cid" == "C4" ]]; then
      mask_flag="--mask-aware-se"
      pretrain_method="cnn_jepa_mask_aware"
    elif [[ "$cid" == "C5" ]]; then
      mask_flag="--mask-aware-se"
      pretrain_method="frozen_teacher"
      jepa="$JEPA_CKPT"
    fi
    pixi run train -- \
      --data-dir "$data_dir" \
      --arch seresnet50 $mask_flag \
      --jepa-checkpoint "$jepa" \
      --epochs "$MAX_EPOCHS" --patience "$PATIENCE" \
      --pretrain-method "$pretrain_method" \
      --center-split "$fold" \
      --seed "$BENCHMARK_SEED" \
      --output "checkpoints/jepa/${run_id}.pt"
    pixi run evaluate -- \
      --checkpoint "checkpoints/jepa/${run_id}.pt" \
      --data-dir "$data_dir" \
      --split test \
      --output "$result_json"
    ;;
  C7_*|C8_*|C9_*)
    fold="${run_id#*_}"
    data_dir="$(resolve_data_dir "$fold")"
    cid="${run_id%%_*}"
    case "$cid" in
      C7) frac=0.10 ;;
      C8) frac=0.25 ;;
      C9) frac=0.50 ;;
    esac
    pixi run train -- \
      --data-dir "$data_dir" \
      --arch seresnet50 --mask-aware-se \
      --jepa-checkpoint "$JEPA_CKPT" \
      --epochs "$MAX_EPOCHS" --patience "$PATIENCE" \
      --pretrain-method cnn_jepa_mask_aware \
      --center-split "$fold" \
      --label-fraction "$frac" \
      --seed "$BENCHMARK_SEED" \
      --output "checkpoints/jepa/${run_id}.pt"
    pixi run evaluate -- \
      --checkpoint "checkpoints/jepa/${run_id}.pt" \
      --data-dir "$data_dir" \
      --split test \
      --output "$result_json"
    ;;
  *)
    echo "Unknown job: $run_id"
    exit 1
    ;;
esac

python3 - <<PY
import json
s = json.load(open("$STATE_FILE"))
if "$run_id" not in s["completed"]:
    s["completed"].append("$run_id")
s["current"] = None
json.dump(s, open("$STATE_FILE", "w"), indent=2)
print("Marked complete:", "$run_id")
PY

echo "AGENT_LOOP_TICK_jepa next job ready — re-run run_article_campaign_loop.sh if GPU idle."
