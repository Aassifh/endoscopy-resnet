#!/usr/bin/env bash
# Copy large datasets to an external drive (mkdir + cp) and symlink back into the repo.
#
# Usage:
#   bash scripts/migrate_data_to_external.sh
#   bash scripts/migrate_data_to_external.sh "/Volumes/TOSHIBA EXT"
#
# After migration:
#   pixi run prepare-colonoscopy-3class

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

VOLUME="${1:-/Volumes/TOSHIBA EXT}"
EXTERNAL="${VOLUME}/endoscopy-resnet-data"

if [[ ! -d "$VOLUME" ]]; then
  echo "Volume not found: $VOLUME" >&2
  exit 1
fi

if ! mkdir -p "${VOLUME}/.endoscopy_write_test" 2>/dev/null; then
  echo "Cannot write to $VOLUME (read-only filesystem)." >&2
  echo "Reformat the drive as exFAT in Disk Utility, then re-run this script." >&2
  exit 1
fi
rmdir "${VOLUME}/.endoscopy_write_test"

mkdir -p "$EXTERNAL"

copy_and_link() {
  local relpath="$1"
  local src="$ROOT/$relpath"
  local name
  name="$(basename "$relpath")"
  local parent
  parent="$(dirname "$relpath")"
  local dst="$EXTERNAL/$name"

  if [[ "$parent" == "data" ]]; then
    dst="$EXTERNAL/$name"
  elif [[ "$relpath" == "checkpoints" ]]; then
    dst="$EXTERNAL/checkpoints"
  else
    dst="$EXTERNAL/$relpath"
  fi

  if [[ -L "$src" ]]; then
    echo "Skip $relpath — already linked -> $(readlink "$src")"
    return
  fi
  if [[ ! -e "$src" ]]; then
    echo "Skip $relpath — not present"
    return
  fi

  echo "=== $relpath ==="
  mkdir -p "$(dirname "$dst")"
  if [[ -d "$dst" ]]; then
    echo "  Merging into existing $dst"
  else
    echo "  cp -a $src -> $(dirname "$dst")/"
    cp -a "$src" "$(dirname "$dst")/"
  fi
  rm -rf "$src"
  ln -s "$dst" "$src"
  echo "  $src -> $dst"
}

for sub in raw kvasir hyperkvasir colonoscopy_3class hyperkvasir_pathology jepa_frames private; do
  copy_and_link "data/$sub"
done
copy_and_link "checkpoints"

mkdir -p "$ROOT/data"
cat > "$ROOT/data/DATA_ROOT.txt" <<EOF
EXTERNAL_DATA_ROOT=$EXTERNAL
MOUNT=$VOLUME
MIGRATED=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
EOF

echo ""
echo "External data root: $EXTERNAL"
df -h "$VOLUME" | tail -1
echo ""
echo "Rebuilding colonoscopy_3class splits …"
if command -v pixi >/dev/null 2>&1; then
  pixi run prepare-colonoscopy-3class
else
  python3 scripts/prepare_colonoscopy_3class.py
fi
echo "Done."
