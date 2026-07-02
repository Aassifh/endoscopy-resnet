# External data storage (TOSHIBA EXT)

Large image datasets and checkpoints live on the external drive. The repo uses **symlinks** under `data/` and `checkpoints/` so scripts keep working unchanged.

## Migrate (mkdir + cp)

Mount **TOSHIBA EXT**, then from the repo root:

```bash
bash scripts/migrate_data_to_external.sh "/Volumes/TOSHIBA EXT"
```

This runs:

1. `mkdir -p "/Volumes/TOSHIBA EXT/endoscopy-resnet-data"`
2. `cp -a` each of `data/raw`, `data/kvasir`, `data/hyperkvasir`, `data/colonoscopy_3class`, `checkpoints`, …
3. Removes the local copy and symlinks back into the repo
4. Re-runs `prepare-colonoscopy-3class`

## Layout on the drive

```
/Volumes/TOSHIBA EXT/endoscopy-resnet-data/
├── raw/
├── kvasir/
├── hyperkvasir/
├── colonoscopy_3class/
├── jepa_frames/          # 99k unlabeled stills go here
└── checkpoints/
```

## Download unlabeled HyperKvasir (~29 GB)

With the drive mounted and migrated:

```bash
pixi run prepare-hyperkvasir-unlabeled
```

## NTFS read-only?

If `cp` fails with **Read-only file system**, macOS cannot write to NTFS. Reformat the Toshiba as **exFAT** in Disk Utility (backup first), then run the migrate script again.

## Drive unplugged

Remount at `/Volumes/TOSHIBA EXT` before training or downloading.
