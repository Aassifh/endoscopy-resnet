#!/usr/bin/env bash
# Validate a publication phase and archive EN/FR PDFs under docs/paper/build/.
#
# Usage:
#   ./scripts/validate_publication.sh 0    # thesis + paper sanity
#   ./scripts/validate_publication.sh 1    # grouped splits + tests
#   ./scripts/validate_publication.sh 5    # tables + PDFs
#   ./scripts/validate_publication.sh all  # every implemented check + final PDFs

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PHASE="${1:-all}"
BUILD_DIR="docs/paper/build"
mkdir -p "$BUILD_DIR"

archive_pdfs() {
  local tag="$1"
  local dest="${BUILD_DIR}/phase-${tag}"
  mkdir -p "$dest"
  make -C docs/paper all
  cp docs/paper/en/main.pdf "${dest}/paper-en.pdf"
  cp docs/paper/fr/main.pdf "${dest}/paper-fr.pdf"
  echo "Archived PDFs -> ${dest}/"
}

run_tests() {
  pixi run python -c "
import tests.test_prepare_colonoscopy_3class as t
t.test_group_split_keeps_groups_disjoint()
t.test_infer_group_id_for_video_frames()
print('split tests ok')
"
  pixi run python -m pytest tests/test_mask_aware_se.py -q
}

validate_phase_0() {
  echo "=== Phase 0: honest thesis in papers ==="
  grep -q "do not claim" docs/paper/en/sections/abstract.tex
  grep -q "ne prétendons pas" docs/paper/fr/sections/related.tex || grep -q "benchmark" docs/paper/fr/sections/abstract.tex
  echo "Phase 0 text checks passed"
  archive_pdfs "00-thesis"
}

validate_phase_1() {
  echo "=== Phase 1: grouped splits ==="
  pixi run prepare-colonoscopy-3class
  python3 - <<'PY'
import json
from pathlib import Path
m = json.loads(Path("data/colonoscopy_3class/manifest.json").read_text())
assert m.get("split_mode") == "grouped", m
train_g = m["group_stats"]["all"]["train"]["groups"]
val_g = m["group_stats"]["all"]["val"]["groups"]
test_g = m["group_stats"]["all"]["test"]["groups"]
assert train_g + val_g + test_g == m["group_stats"]["total_groups"]
print(f"grouped split ok: {m['group_stats']['total_groups']} groups")
PY
  run_tests
  archive_pdfs "01-grouped-splits"
}

validate_phase_5() {
  echo "=== Phase 5: tables + literature ==="
  python3 scripts/generate_paper_tables.py
  test -s docs/paper/shared/tables/results.tex
  grep -q "tab:hk23" docs/paper/shared/tables/results.tex
  grep -q "TP" docs/paper/en/sections/methods.tex || grep -q "polyp recall" docs/paper/en/sections/methods.tex
  archive_pdfs "05-tables"
}

validate_phase_6() {
  echo "=== Phase 6: limitations + clinical framing ==="
  grep -q "Limitations" docs/paper/en/sections/discussion.tex
  grep -q "Limites" docs/paper/fr/sections/discussion.tex
  archive_pdfs "06-limitations"
}

validate_phase_7() {
  echo "=== Phase 7: reproduce path ==="
  make reproduce-paper
  archive_pdfs "07-reproduce"
}

case "$PHASE" in
  0) validate_phase_0 ;;
  1) validate_phase_1 ;;
  5) validate_phase_5 ;;
  6) validate_phase_6 ;;
  7) validate_phase_7 ;;
  all)
    validate_phase_0
    validate_phase_1
    validate_phase_5
    validate_phase_6
    validate_phase_7
    ;;
  *)
    echo "Unknown phase: $PHASE (use 0, 1, 5, 6, 7, or all)"
    exit 1
    ;;
esac

echo "Validation complete for phase(s): $PHASE"
