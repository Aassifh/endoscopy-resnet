#!/usr/bin/env bash
# Run the JEPA article campaign for every seed in benchmarks/ml/seeds.json.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

seeds=$(python3 -c "import json; print(' '.join(map(str, json.load(open('benchmarks/ml/seeds.json'))['seeds'])))")
for seed in $seeds; do
  echo "========== Benchmark seed $seed =========="
  export BENCHMARK_SEED="$seed"
  while true; do
    if ! output=$(bash scripts/run_article_campaign_loop.sh 2>&1); then
      echo "$output"
      exit 1
    fi
    echo "$output"
    if echo "$output" | grep -q "Campaign complete"; then
      break
    fi
  done
done
echo "Multi-seed campaign complete."
