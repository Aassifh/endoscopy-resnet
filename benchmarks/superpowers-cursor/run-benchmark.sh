#!/usr/bin/env bash
# Superpowers Cursor benchmark runner
# Usage: ./run-benchmark.sh [analyze|results|hook-test|all]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$ROOT"

cmd="${1:-all}"

hook_test() {
  echo "=== Session Hook Test ==="
  export CURSOR_PLUGIN_ROOT="$ROOT/vendor/superpowers"
  bash vendor/superpowers/hooks/session-start | python3 -c "
import json, sys
d = json.load(sys.stdin)
assert 'additional_context' in d
assert 'using-superpowers' in d['additional_context']
print('PASS: session-start injects using-superpowers')
"
}

case "$cmd" in
  analyze)
    python3 "$SCRIPT_DIR/run_benchmark.py" analyze
    ;;
  results)
    python3 "$SCRIPT_DIR/run_benchmark.py" results
    ;;
  hook-test)
    hook_test
    ;;
  all)
    hook_test
    echo ""
    python3 "$SCRIPT_DIR/run_benchmark.py" analyze
    echo ""
    python3 "$SCRIPT_DIR/run_benchmark.py" results
    ;;
  *)
    echo "Usage: $0 [analyze|results|hook-test|all]"
    exit 1
    ;;
esac
