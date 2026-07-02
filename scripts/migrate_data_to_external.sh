#!/usr/bin/env bash
# Move large datasets to an external drive (mkdir + mv) and symlink back into the repo.
# Keeps the drive filesystem unchanged (NTFS stays NTFS).
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

mkdir -p "$EXTERNAL" || {
  echo "Cannot create $EXTERNAL — volume is not writable from this Mac." >&2
  echo "macOS mounts NTFS read-only by default; mv needs write access on the drive." >&2
  exit 1
}

move_and_link() {
  local relpath="$1"
  local src="$ROOT/$relpath"
  local name
  name="$(basename "$relpath")"
  local dst="$EXTERNAL/$name"

  if [[ -L "$src" ]]; then
    echo "Skip $relpath — already linked -> $(readlink "$src")"
    return
  fi
  if [[ ! -e "$src" ]]; then
    echo "Skip $relpath — not present"
    return
  fi

  echo "=== $relpath ==="
  if [[ -e "$dst" ]]; then
    echo "  Already on external: $dst (linking only)"
  else
    echo "  mv $src -> $EXTERNAL/"
    mv "$src" "$EXTERNAL/"
  fi
  ln -snf "$dst" "$src"
  echo "  $src -> $dst"
}

for sub in raw kvasir hyperkvasir colonoscopy_3class hyperkvasir_pathology jepa_frames private; do
  move_and_link "data/$sub"
done
move_and_link "checkpoints"

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
