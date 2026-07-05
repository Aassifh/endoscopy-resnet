#!/usr/bin/env bash
# Re-run C2–C5 fine-tunes after 99k-image JEPA pretrain (uses updated shared checkpoints).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

RESULTS="benchmarks/ml/results"
SEED="${BENCHMARK_SEED:-42}"

for run in C2 C3 C4 C5; do
  if [[ "$SEED" == "42" ]]; then
    out="$RESULTS/${run}_fold_simula_test.json"
  else
    out="$RESULTS/${run}_fold_simula_seed${SEED}_test.json"
  fi
  rm -f "$out"
  rm -f "checkpoints/jepa/${run}_fold_simula.pt"
done

python3 - <<PY
import json
from pathlib import Path
state_path = Path("benchmarks/ml/results/jepa_campaign_state.json")
s = json.loads(state_path.read_text())
drop = {"C2_fold_simula", "C3_fold_simula", "C4_fold_simula", "C5_fold_simula"}
s["completed"] = [j for j in s.get("completed", []) if j not in drop]
state_path.write_text(json.dumps(s, indent=2) + "\n")
PY

export BENCHMARK_SEED="$SEED"
while true; do
  out="$(bash scripts/run_article_campaign_loop.sh 2>&1)" || { echo "$out"; exit 1; }
  echo "$out"
  done_all=true
  for run in C2 C3 C4 C5; do
    if [[ "$SEED" == "42" ]]; then
      f="$RESULTS/${run}_fold_simula_test.json"
    else
      f="$RESULTS/${run}_fold_simula_seed${SEED}_test.json"
    fi
    [[ -f "$f" ]] || done_all=false
  done
  $done_all && break
  if echo "$out" | grep -q "Campaign complete"; then
    break
  fi
done

echo "C2–C5 unlabeled-pretrain re-run complete (seed=$SEED)."
