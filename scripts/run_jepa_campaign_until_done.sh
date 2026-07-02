#!/usr/bin/env bash
# Run all pending CNN-JEPA article jobs sequentially until the queue is empty.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

LOG="$ROOT/benchmarks/ml/results/jepa_campaign.log"
STATE="$ROOT/benchmarks/ml/results/jepa_campaign_state.json"
mkdir -p benchmarks/ml/results checkpoints/jepa

echo "=== JEPA campaign started $(date -u +%Y-%m-%dT%H:%M:%SZ) ===" | tee -a "$LOG"

while true; do
  done_count="$(python3 - <<PY
import json
s = json.load(open("$STATE"))
q, c = s["queue"], set(s.get("completed", []))
pending = [j for j in q if j not in c]
print(len(pending))
PY
)"
  [[ "$done_count" -gt 0 ]] || break
  echo "--- tick $(date -u +%H:%M:%S) pending=$done_count ---" | tee -a "$LOG"
  if ! bash scripts/run_article_campaign_loop.sh 2>&1 | tee -a "$LOG"; then
    echo "ERROR: job failed at $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "$LOG"
    exit 1
  fi
  sleep 2
done

echo "=== JEPA campaign complete $(date -u +%Y-%m-%dT%H:%M:%SZ) ===" | tee -a "$LOG"
python3 - <<'PY' | tee -a "$LOG"
import json
from pathlib import Path
results = sorted(Path("benchmarks/ml/results").glob("*_test.json"))
jepa = [p for p in results if p.name.startswith(("C0_", "C1_", "C3_", "C4_", "C5_", "C7_", "C8_", "C9_", "C10_"))]
print("\n--- JEPA benchmark results ---")
for p in jepa:
    r = json.loads(p.read_text())
    mf1 = r.get("macro_f1", r.get("macro_f1_mean", "?"))
    print(f"  {p.stem}: macro_f1={mf1}")
PY
