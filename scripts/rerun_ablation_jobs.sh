#!/usr/bin/env bash
# Re-run C3/C4/C5 after fixing standard-SE pretrain and frozen-teacher linear probe.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

RESULTS="benchmarks/ml/results"

echo "=== Ablation fix: clearing C3/C4/C5 artifacts ==="
rm -f "$RESULTS"/C3_fold_simula_test.json "$RESULTS"/C4_fold_simula_test.json "$RESULTS"/C5_fold_simula_test.json
rm -f checkpoints/jepa/C3_fold_simula.pt checkpoints/jepa/C4_fold_simula.pt checkpoints/jepa/C5_fold_simula.pt
rm -f checkpoints/jepa/c3_se_standard_shared.pt

python3 - <<'PY'
import json
from pathlib import Path
state_path = Path("benchmarks/ml/results/jepa_campaign_state.json")
if state_path.is_file():
    s = json.loads(state_path.read_text())
    s["completed"] = [j for j in s.get("completed", []) if j not in {
        "pretrain_c3_se_standard", "C3_fold_simula", "C4_fold_simula", "C5_fold_simula"
    }]
    if "pretrain_c3_se_standard" not in s["queue"]:
        idx = s["queue"].index("pretrain_c4_shared") + 1 if "pretrain_c4_shared" in s["queue"] else 0
        s["queue"].insert(idx, "pretrain_c3_se_standard")
    s["current"] = None
    state_path.write_text(json.dumps(s, indent=2) + "\n")
    print("Updated campaign state for ablation re-run.")
PY

export BENCHMARK_SEED=42
while true; do
  out="$(bash scripts/run_article_campaign_loop.sh 2>&1)" || { echo "$out"; exit 1; }
  echo "$out"
  for job in pretrain_c3_se_standard C3_fold_simula C4_fold_simula C5_fold_simula; do
    if [[ "$job" == pretrain_c3_se_standard ]]; then
      [[ -f checkpoints/jepa/c3_se_standard_shared.pt ]] || continue
    else
      [[ -f "$RESULTS/${job}_test.json" ]] || { pending=1; break; }
    fi
  done
  [[ "${pending:-0}" == 1 ]] && pending=0 && continue
  if [[ -f "$RESULTS/C3_fold_simula_test.json" && -f "$RESULTS/C4_fold_simula_test.json" && -f "$RESULTS/C5_fold_simula_test.json" ]]; then
    break
  fi
  if echo "$out" | grep -q "Campaign complete"; then
    break
  fi
done

echo "Ablation re-run complete."
