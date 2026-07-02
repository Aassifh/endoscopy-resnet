# External data storage (TOSHIBA EXT)

Move datasets off the internal disk with **mkdir + mv** (no reformat, no copy duplicate).

## Migrate

Mount **TOSHIBA EXT**, then:

```bash
bash scripts/migrate_data_to_external.sh "/Volumes/TOSHIBA EXT"
```

Creates `/Volumes/TOSHIBA EXT/endoscopy-resnet-data/`, **moves** each folder there, symlinks back into the repo.

| Repo path | On drive |
|-----------|----------|
| `data/raw/` | `endoscopy-resnet-data/raw/` |
| `data/kvasir/` | `endoscopy-resnet-data/kvasir/` |
| `data/hyperkvasir/` | `endoscopy-resnet-data/hyperkvasir/` |
| `data/colonoscopy_3class/` | `endoscopy-resnet-data/colonoscopy_3class/` |
| `data/jepa_frames/` | `endoscopy-resnet-data/jepa_frames/` |
| `checkpoints/` | `endoscopy-resnet-data/checkpoints/` |

## Manual mv (same layout)

If you prefer Finder or another machine:

```bash
mkdir -p "/Volumes/TOSHIBA EXT/endoscopy-resnet-data"
mv data/raw data/kvasir data/hyperkvasir data/colonoscopy_3class checkpoints \
   "/Volumes/TOSHIBA EXT/endoscopy-resnet-data/"
ln -s "/Volumes/TOSHIBA EXT/endoscopy-resnet-data/raw" data/raw
ln -s "/Volumes/TOSHIBA EXT/endoscopy-resnet-data/kvasir" data/kvasir
ln -s "/Volumes/TOSHIBA EXT/endoscopy-resnet-data/hyperkvasir" data/hyperkvasir
ln -s "/Volumes/TOSHIBA EXT/endoscopy-resnet-data/colonoscopy_3class" data/colonoscopy_3class
ln -s "/Volumes/TOSHIBA EXT/endoscopy-resnet-data/checkpoints" checkpoints
pixi run prepare-colonoscopy-3class
```

## macOS + NTFS

macOS often mounts NTFS **read-only**. If `mv` fails, move the folders from **Windows** (same paths on the drive), then create the symlinks on the Mac after plugging the drive back in.

## Unlabeled download (~29 GB)

```bash
pixi run prepare-hyperkvasir-unlabeled
```

Writes to `data/jepa_frames/hyperkvasir_unlabeled/` (symlinked to the drive after migration).
