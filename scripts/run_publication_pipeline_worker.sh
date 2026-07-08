#!/usr/bin/env bash
# Long-running publication pipeline: ablations, multi-seed, cross-dataset, 99k JEPA, stats, PDFs.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export PATH="/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:${PATH:-}"

STATE="benchmarks/ml/results/publication_pipeline_state.json"
LOG="benchmarks/ml/results/publication_pipeline.log"
mkdir -p benchmarks/ml/results

init_state() {
  python3 - <<'PY'
import json
from pathlib import Path
path = Path("benchmarks/ml/results/publication_pipeline_state.json")
if path.is_file():
    raise SystemExit("exists")
phases = [
    "verify_b2_b6",
    "ablation_fix",
    "clinical_metrics",
    "multi_seed",
    "cross_dataset",
    "unlabeled_download",
    "jepa_99k_pretrain",
    "c2_c5_99k_rerun",
    "benchmark_stats",
    "finalize",
]
path.write_text(json.dumps({"phases": phases, "completed": [], "current": None}, indent=2) + "\n")
print("Initialized publication pipeline state.")
PY
}

phase_done() {
  python3 - <<PY
import json
from pathlib import Path
p = Path("$STATE")
s = json.loads(p.read_text())
phase = "$1"
if phase not in s["completed"]:
    s["completed"].append(phase)
s["current"] = None
p.write_text(json.dumps(s, indent=2) + "\n")
PY
}

unlabeled_ready() {
  [[ -d data/jepa_frames/hyperkvasir_unlabeled ]] && \
    [[ -n "$(find data/jepa_frames/hyperkvasir_unlabeled -name '*.jpg' -o -name '*.jpeg' -o -name '*.png' 2>/dev/null | head -1)" ]]
}

should_skip_99k() {
  if [[ "${PUBLICATION_SKIP_99K:-}" == "1" ]]; then
    return 0
  fi
  if unlabeled_ready; then
    return 1
  fi
  # hyper-kvasir-unlabeled-images.zip is ~29.4 GB; need zip + extract headroom.
  local avail_kb
  avail_kb="$(df -k "$ROOT" | awk 'NR==2 {print $4}')"
  local min_kb=$((40 * 1024 * 1024))
  [[ "${avail_kb:-0}" -lt "$min_kb" ]]
}

skip_99k_phases() {
  local reason="$1"
  echo "SKIP 99k phases ($reason). Need ~30 GB zip + extract; set PUBLICATION_SKIP_99K=0 and free disk to run later." | tee -a "$LOG"
  phase_done unlabeled_download
  phase_done jepa_99k_pretrain
  phase_done c2_c5_99k_rerun
}

next_phase() {
  python3 - <<PY
import json
from pathlib import Path
s = json.loads(Path("$STATE").read_text())
for phase in s["phases"]:
    if phase not in s.get("completed", []):
        print(phase)
        break
PY
}

mark_current() {
  python3 - <<PY
import json
from pathlib import Path
s = json.loads(Path("$STATE").read_text())
s["current"] = "$1"
Path("$STATE").write_text(json.dumps(s, indent=2) + "\n")
PY
}

FORCE=false
while [[ $# -gt 0 ]]; do
  case "$1" in
    --force) FORCE=true; shift ;;
    --init) init_state; exit 0 ;;
    *) exit 1 ;;
  esac
done

if [[ ! -f "$STATE" ]]; then
  init_state
fi

if $FORCE; then
  echo '{"phases":["verify_b2_b6","ablation_fix","clinical_metrics","multi_seed","cross_dataset","unlabeled_download","jepa_99k_pretrain","c2_c5_99k_rerun","benchmark_stats","finalize"],"completed":[],"current":null}' > "$STATE"
fi

echo "=== publication pipeline worker started $(date -u +%Y-%m-%dT%H:%M:%SZ) pid=$$ ===" | tee -a "$LOG"

while true; do
  phase="$(next_phase)"
  if [[ -z "${phase:-}" ]]; then
    echo "=== publication pipeline complete $(date -u +%Y-%m-%dT%H:%M:%SZ) ===" | tee -a "$LOG"
    exit 0
  fi

  mark_current "$phase"
  echo "=== Phase: $phase ===" | tee -a "$LOG"

  case "$phase" in
    verify_b2_b6)
      missing=0
      for f in \
        benchmarks/ml/results/hyperkvasir_b2_resnet50_imagenet_test.json \
        benchmarks/ml/results/hyperkvasir_b3_seresnet50_scratch_test.json \
        benchmarks/ml/results/hyperkvasir_b4_seresnet50_imagenet_test.json \
        benchmarks/ml/results/hyperkvasir_b5_dualstream_scratch_test.json \
        benchmarks/ml/results/hyperkvasir_b6_dualstream_imagenet_test.json; do
        [[ -f "$f" ]] || missing=1
      done
      if [[ "$missing" == 1 ]]; then
        bash scripts/run_hyperkvasir_benchmarks.sh 2>&1 | tee -a "$LOG"
      else
        echo "B2–B6 JSON results present; skipping re-run." | tee -a "$LOG"
      fi
      ;;
    ablation_fix)
      bash scripts/rerun_ablation_jobs.sh 2>&1 | tee -a "$LOG"
      ;;
    clinical_metrics)
      bash scripts/run_clinical_metrics.sh 2>&1 | tee -a "$LOG"
      ;;
    multi_seed)
      bash scripts/run_multi_seed_campaign.sh 2>&1 | tee -a "$LOG"
      ;;
    cross_dataset)
      bash scripts/run_cross_dataset_eval.sh 2>&1 | tee -a "$LOG"
      ;;
    unlabeled_download)
      if should_skip_99k; then
        skip_99k_phases "disk or PUBLICATION_SKIP_99K"
      elif unlabeled_ready; then
        echo "Unlabeled frames already prepared." | tee -a "$LOG"
      else
        pixi run prepare-hyperkvasir-unlabeled 2>&1 | tee -a "$LOG"
      fi
      ;;
    jepa_99k_pretrain)
      if should_skip_99k; then
        skip_99k_phases "skipped — no unlabeled corpus"
      else
      FRAMES="data/jepa_frames/hyperkvasir_unlabeled"
      rm -f checkpoints/jepa/c4_mask_aware_shared.pt checkpoints/jepa/c3_se_standard_shared.pt checkpoints/jepa/c2_resnet_jepa_shared.pt
      pixi run pretrain-jepa -- \
        --frames-dir "$FRAMES" --backbone seresnet50 --mask-aware-se \
        --output checkpoints/jepa/c4_mask_aware_shared.pt \
        --max-epochs 80 --patience 10 --batch-size 16 --max-samples 0 --seed 42 2>&1 | tee -a "$LOG"
      pixi run pretrain-jepa -- \
        --frames-dir "$FRAMES" --backbone seresnet50 \
        --output checkpoints/jepa/c3_se_standard_shared.pt \
        --max-epochs 80 --patience 10 --batch-size 16 --max-samples 0 --seed 42 2>&1 | tee -a "$LOG"
      pixi run pretrain-jepa -- \
        --frames-dir "$FRAMES" --backbone resnet50 \
        --output checkpoints/jepa/c2_resnet_jepa_shared.pt \
        --max-epochs 80 --patience 10 --batch-size 16 --max-samples 0 --seed 42 2>&1 | tee -a "$LOG"
      fi
      ;;
    c2_c5_99k_rerun)
      if should_skip_99k; then
        skip_99k_phases "skipped — no 99k JEPA checkpoints"
      else
      for seed in 42 43 44; do
        BENCHMARK_SEED="$seed" bash scripts/rerun_c2_c5_after_99k.sh 2>&1 | tee -a "$LOG"
      done
      fi
      ;;
    benchmark_stats)
      pixi run benchmark-stats 2>&1 | tee -a "$LOG"
      pixi run benchmark-stats -- --metric polyp_recall 2>&1 | tee -a "$LOG"
      ;;
    finalize)
      python3 scripts/generate_paper_tables.py 2>&1 | tee -a "$LOG"
      bash scripts/validate_publication.sh all 2>&1 | tee -a "$LOG"
      ;;
    *)
      echo "Unknown phase: $phase" | tee -a "$LOG"
      exit 1
      ;;
  esac

  phase_done "$phase"
done
