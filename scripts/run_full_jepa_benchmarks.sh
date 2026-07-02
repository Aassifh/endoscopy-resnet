#!/usr/bin/env bash
# Run the full CNN-JEPA article benchmark campaign (C0–C10) sequentially until complete.
#
# Usage:
#   ./scripts/run_full_jepa_benchmarks.sh           # resume pending jobs
#   ./scripts/run_full_jepa_benchmarks.sh --force   # wipe JEPA results and rerun all

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

FORCE=false
while [[ $# -gt 0 ]]; do
  case "$1" in
    --force) FORCE=true; shift ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

echo "=== Preparing 3-class colonoscopy dataset ==="
pixi run prepare-colonoscopy-3class

echo "=== Starting JEPA benchmark campaign ==="
USE_FORCE=$FORCE
while true; do
  set +e
  if $USE_FORCE; then
    bash scripts/run_article_campaign_loop.sh --force
    USE_FORCE=false
  else
    bash scripts/run_article_campaign_loop.sh
  fi
  code=$?
  set -e
  if [[ $code -ne 0 ]]; then
    echo "Campaign step failed with exit code $code"
    exit "$code"
  fi
  if bash scripts/run_article_campaign_loop.sh --status | python3 -c "
import json, sys
s = json.load(sys.stdin)
pending = [j for j in s['queue'] if j not in s.get('completed', [])]
sys.exit(0 if not pending else 1)
"; then
    break
  fi
done

echo "=== Generating summary ==="
python3 scripts/inject_jepa_results.py

echo "=== Campaign complete ==="
cat benchmarks/ml/results/jepa_summary.md
