#!/usr/bin/env bash
# Create symlinks into the repo after data folders live on the external drive.
# Use after mv/copy on Windows, or after migrate_data_to_external.sh succeeds on Mac.
#
# Usage:
#   bash scripts/link_external_data.sh "/Volumes/TOSHIBA EXT"

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

VOLUME="${1:-/Volumes/TOSHIBA EXT}"
EXTERNAL="${VOLUME}/endoscopy-resnet-data"

if [[ ! -d "$EXTERNAL/raw" && ! -d "$EXTERNAL/kvasir" ]]; then
  echo "No data at $EXTERNAL (expected raw/ or kvasir/)" >&2
  exit 1
fi

link_one() {
  local relpath="$1"
  local name="$2"
  local src="$ROOT/$relpath"
  local dst="$EXTERNAL/$name"

  [[ -d "$dst" ]] || { echo "Skip $name — not on drive"; return; }
  if [[ -e "$src" && ! -L "$src" ]]; then
    echo "Remove local $src (not yet moved?)"
    rm -rf "$src"
  fi
  ln -snf "$dst" "$src"
  echo "$src -> $dst"
}

mkdir -p "$ROOT/data"
link_one "data/raw" "raw"
link_one "data/kvasir" "kvasir"
link_one "data/hyperkvasir" "hyperkvasir"
link_one "data/colonoscopy_3class" "colonoscopy_3class"
link_one "data/hyperkvasir_pathology" "hyperkvasir_pathology"
link_one "data/jepa_frames" "jepa_frames"
link_one "checkpoints" "checkpoints"

cat > "$ROOT/data/DATA_ROOT.txt" <<EOF
EXTERNAL_DATA_ROOT=$EXTERNAL
MOUNT=$VOLUME
LINKED=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
EOF

echo ""
if command -v pixi >/dev/null 2>&1; then
  pixi run prepare-colonoscopy-3class
else
  python3 scripts/prepare_colonoscopy_3class.py
fi
echo "Linked."
