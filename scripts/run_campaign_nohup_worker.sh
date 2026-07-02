#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export PATH="/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:${PATH:-}"

FORCE=false
while [[ $# -gt 0 ]]; do
  case "$1" in
    --force) FORCE=true; shift ;;
    *) exit 1 ;;
  esac
done

echo "=== campaign worker started $(date -u +%Y-%m-%dT%H:%M:%SZ) pid=$$ ==="

if $FORCE; then
  bash scripts/run_article_campaign_loop.sh --force
fi

while true; do
  if ! out="$(bash scripts/run_article_campaign_loop.sh 2>&1)"; then
    echo "$out"
    echo "=== campaign failed $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
    exit 1
  fi
  echo "$out"
  if echo "$out" | grep -q "Campaign complete"; then
    echo "=== campaign complete $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
    exit 0
  fi
done
