#!/usr/bin/env bash
# Move large endoscopy-resnet data to an external drive and symlink back.
#
# Usage:
#   ./scripts/migrate_data_to_external.sh
#   ./scripts/migrate_data_to_external.sh "/Volumes/TOSHIBA EXT"
#
# After migration, re-run:
#   pixi run prepare-colonoscopy-3class
#   ./scripts/migrate_data_to_external.sh "/Volumes/TOSHIBA_EXT_RW"   # after setup_toshiba_write.sh
#
# If the drive is NTFS (read-only on macOS), run first:
#   ./scripts/setup_toshiba_write.sh

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

VOLUME="${1:-/Volumes/TOSHIBA EXT}"
EXTERNAL="${VOLUME}/endoscopy-resnet-data"

if [[ ! -d "$VOLUME" ]]; then
  echo "External volume not found: $VOLUME" >&2
  echo "Mount the drive and retry, or pass the mount path as the first argument." >&2
  exit 1
fi

if ! touch "${VOLUME}/.endoscopy_write_test" 2>/dev/null; then
  echo "ERROR: $VOLUME is read-only." >&2
  echo "" >&2
  echo "TOSHIBA EXT is NTFS — macOS cannot write to it without extra software." >&2
  echo "Fix (one-time, in Terminal on your Mac):" >&2
  echo "  bash scripts/setup_toshiba_write.sh \"$VOLUME\"" >&2
  echo "" >&2
  echo "Or see docs/setup-external-data.md for exFAT / Paragon NTFS options." >&2
  exit 1
fi
rm -f "${VOLUME}/.endoscopy_write_test"

mkdir -p "$EXTERNAL"

move_and_link() {
  local name="$1"
  local src="$ROOT/$name"
  local dst="$EXTERNAL/$(basename "$name")"

  if [[ -L "$src" ]]; then
    echo "Skip $name — already a symlink -> $(readlink "$src")"
    return
  fi
  if [[ ! -e "$src" ]]; then
    echo "Skip $name — not present"
    return
  fi

  echo "=== $name ==="
  mkdir -p "$(dirname "$dst")"
  if [[ -e "$dst" ]]; then
    echo "  External copy exists; syncing $src -> $dst"
    rsync -a --info=progress2 "$src/" "$dst/"
    rm -rf "$src"
  else
    echo "  Moving $src -> $dst"
    mv "$src" "$dst"
  fi
  ln -s "$dst" "$src"
  echo "  Linked $src -> $dst"
}

# data subdirectories (large image corpora)
for sub in raw kvasir hyperkvasir colonoscopy_3class hyperkvasir_pathology jepa_frames private; do
  move_and_link "data/$sub"
done

# training checkpoints (gitignored)
move_and_link "checkpoints"

# record external root for tooling
cat > "$ROOT/data/DATA_ROOT.txt" <<EOF
# Large datasets live on external storage. Do not commit this file's target.
EXTERNAL_DATA_ROOT=$EXTERNAL
MOUNT=$VOLUME
MIGRATED=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
EOF

echo ""
echo "External data root: $EXTERNAL"
df -h "$VOLUME" | tail -1
echo ""
echo "Rebuilding derived splits (colonoscopy_3class symlinks) …"
if command -v pixi >/dev/null 2>&1; then
  pixi run prepare-colonoscopy-3class
else
  python3 scripts/prepare_colonoscopy_3class.py
fi
echo ""
echo "Done. Future downloads go to the external drive via data/* symlinks."
echo "To fetch ~99k unlabeled stills:"
echo "  pixi run prepare-hyperkvasir-unlabeled"
