#!/usr/bin/env bash
# Enable read-write access to an NTFS external drive (e.g. TOSHIBA EXT) on macOS.
#
# macOS mounts NTFS read-only by default. This script installs macFUSE + ntfs-3g
# and remounts the volume writable. Requires sudo (one-time kernel extension approval
# in System Settings → Privacy & Security).
#
# Usage:
#   ./scripts/setup_toshiba_write.sh
#   ./scripts/setup_toshiba_write.sh "/Volumes/TOSHIBA EXT"

set -euo pipefail

VOLUME="${1:-/Volumes/TOSHIBA EXT}"
MOUNT_RW="/Volumes/TOSHIBA_EXT_RW"
DEVICE="${2:-}"

if [[ -z "$DEVICE" ]]; then
  DEVICE=$(diskutil info "$VOLUME" 2>/dev/null | awk '/Device Identifier/ {print $3}' || true)
fi
if [[ -z "$DEVICE" ]]; then
  echo "Could not resolve device for $VOLUME" >&2
  exit 1
fi
DEV_NODE="/dev/${DEVICE}"

echo "Volume:  $VOLUME"
echo "Device:  $DEV_NODE"
echo "RW mount: $MOUNT_RW"
echo ""

if touch "$VOLUME/_write_probe" 2>/dev/null; then
  rm -f "$VOLUME/_write_probe"
  echo "Volume is already writable at $VOLUME"
  echo "Run: bash scripts/migrate_data_to_external.sh \"$VOLUME\""
  exit 0
fi

echo "Volume is read-only (typical NTFS on macOS)."
echo ""
echo "Step 1 — install macFUSE + ntfs-3g (will prompt for password):"
echo "  brew install --cask macfuse"
echo "  brew install ntfs-3g"
echo ""
read -r -p "Install now? [y/N] " ans
if [[ "${ans,,}" == "y" ]]; then
  brew install --cask macfuse || true
  brew install ntfs-3g || true
  echo ""
  echo "If macFUSE install failed, open System Settings → Privacy & Security"
  echo "and allow the macFUSE system extension, then re-run this script."
fi

NTFS3G="$(command -v ntfs-3g || true)"
if [[ -z "$NTFS3G" && -x /usr/local/sbin/ntfs-3g ]]; then
  NTFS3G=/usr/local/sbin/ntfs-3g
fi
if [[ -z "$NTFS3G" && -x /opt/homebrew/sbin/ntfs-3g ]]; then
  NTFS3G=/opt/homebrew/sbin/ntfs-3g
fi
if [[ -z "$NTFS3G" ]]; then
  echo "ntfs-3g not found. Install with: brew install ntfs-3g" >&2
  exit 1
fi

echo ""
echo "Step 2 — remount read-write at $MOUNT_RW (sudo):"
diskutil unmount "$VOLUME" || true
sudo mkdir -p "$MOUNT_RW"
sudo "$NTFS3G" "$DEV_NODE" "$MOUNT_RW" -olocal,allow_other,rw

if touch "$MOUNT_RW/_write_probe" 2>/dev/null; then
  rm -f "$MOUNT_RW/_write_probe"
  echo ""
  echo "Success. Writable mount: $MOUNT_RW"
  echo "Next:"
  echo "  bash scripts/migrate_data_to_external.sh \"$MOUNT_RW\""
else
  echo "Remount failed — volume still read-only." >&2
  exit 1
fi
