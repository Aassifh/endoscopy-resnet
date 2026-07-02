# External data storage

Large image datasets and checkpoints are stored on the **Toshiba external drive** to avoid filling the internal disk.

| Repo path | External location |
|-----------|-------------------|
| `data/raw/` | `/Volumes/TOSHIBA EXT/endoscopy-resnet-data/raw/` |
| `data/kvasir/` | `.../kvasir/` |
| `data/hyperkvasir/` | `.../hyperkvasir/` |
| `data/colonoscopy_3class/` | `.../colonoscopy_3class/` |
| `data/jepa_frames/` | `.../jepa_frames/` (99k unlabeled stills) |
| `checkpoints/` | `.../checkpoints/` |

## First-time setup (or new machine)

1. Mount **TOSHIBA EXT**.
2. From the repo root:

```bash
bash scripts/migrate_data_to_external.sh
# or explicit mount:
bash scripts/migrate_data_to_external.sh "/Volumes/TOSHIBA EXT"
```

3. Verify:

```bash
ls -la data/raw data/kvasir checkpoints
pixi run prepare-colonoscopy-3class
```

## Download unlabeled HyperKvasir (~29 GB)

With the drive mounted, downloads land on external storage automatically:

```bash
pixi run prepare-hyperkvasir-unlabeled
```

## If the drive is unplugged

Symlinks under `data/` and `checkpoints/` will break until the volume is remounted. On a different mount path, re-run the migrate script with the new path.

## NTFS read-only on macOS (TOSHIBA EXT)

The Toshiba drive is formatted **NTFS**. macOS mounts it **read-only** by default (~78 GB free on the volume, but not writable until fixed).

**Recommended fix** (keeps existing Windows files):

```bash
bash scripts/setup_toshiba_write.sh "/Volumes/TOSHIBA EXT"
bash scripts/migrate_data_to_external.sh "/Volumes/TOSHIBA_EXT_RW"
```

That installs macFUSE + ntfs-3g (sudo + one-time kernel extension approval in System Settings), remounts writable at `/Volumes/TOSHIBA_EXT_RW`, then moves data and symlinks back into the repo.

**Alternative:** reformat the drive as **exFAT** in Disk Utility (backup first — erases the disk), then:

```bash
bash scripts/migrate_data_to_external.sh "/Volumes/TOSHIBA EXT"
```

## Current root

See `data/DATA_ROOT.txt` (gitignored) after migration.
