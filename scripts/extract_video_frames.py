#!/usr/bin/env python3
"""
Extract unlabeled video frames for CNN-JEPA pretraining.

Supports:
  - HyperKvasir unlabeled video archives (zip or extracted tree)
  - Private multi-center raw videos under data/private/{center_id}/raw/

Quality filters: Laplacian variance (blur), mean brightness (black frames).

Output:
  data/jepa_frames/{source}/frame_*.jpg
  data/jepa_frames/manifest.json

Usage:
  python scripts/extract_video_frames.py --hyperkvasir-video data/raw/hyper-kvasir-videos
  python scripts/extract_video_frames.py --private-dir data/private --fps 1.5
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

IMAGE_EXTS = {".jpg", ".jpeg", ".png"}
VIDEO_EXTS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}


def laplacian_variance(gray: np.ndarray) -> float:
    from skimage.filters import laplace

    lap = laplace(gray.astype(np.float64))
    return float(lap.var())


def frame_quality_ok(arr: np.ndarray, min_laplacian: float, min_brightness: float) -> bool:
    gray = arr.mean(axis=2) if arr.ndim == 3 else arr
    if gray.mean() < min_brightness:
        return False
    try:
        return laplacian_variance(gray) >= min_laplacian
    except Exception:
        return True


def save_frame(arr: np.ndarray, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(arr.astype(np.uint8)).save(path, quality=90)


def extract_with_ffmpeg(video: Path, out_dir: Path, fps: float, max_frames: int) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    pattern = out_dir / f"{video.stem}_%06d.jpg"
    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-i", str(video),
        "-vf", f"fps={fps}",
        "-frames:v", str(max_frames),
        str(pattern),
    ]
    try:
        subprocess.run(cmd, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        print(f"  ffmpeg skip {video.name}: {exc}", file=sys.stderr)
        return []
    return sorted(out_dir.glob(f"{video.stem}_*.jpg"))


def filter_and_relocate(frames: list[Path], dest_dir: Path, min_laplacian: float, min_brightness: float) -> int:
    kept = 0
    for i, fp in enumerate(frames):
        try:
            arr = np.array(Image.open(fp).convert("RGB"))
        except OSError:
            fp.unlink(missing_ok=True)
            continue
        if not frame_quality_ok(arr, min_laplacian, min_brightness):
            fp.unlink(missing_ok=True)
            continue
        dst = dest_dir / f"frame_{kept:06d}.jpg"
        fp.rename(dst)
        kept += 1
    return kept


def process_video_dir(
    video_root: Path,
    output_root: Path,
    source_name: str,
    fps: float,
    max_frames_per_video: int,
    min_laplacian: float,
    min_brightness: float,
) -> dict:
    videos = [p for p in video_root.rglob("*") if p.suffix.lower() in VIDEO_EXTS]
    dest = output_root / source_name
    dest.mkdir(parents=True, exist_ok=True)
    total = 0
    for vid in videos:
        tmp = output_root / "_tmp" / source_name / vid.stem
        if tmp.exists():
            for f in tmp.glob("*.jpg"):
                f.unlink()
        raw_frames = extract_with_ffmpeg(vid, tmp, fps, max_frames_per_video)
        kept = filter_and_relocate(raw_frames, dest, min_laplacian, min_brightness)
        total += kept
        print(f"  {vid.name}: kept {kept} frames")
    return {"source": source_name, "videos": len(videos), "frames": total, "path": str(dest)}


def main() -> None:
    p = argparse.ArgumentParser(description="Extract unlabeled frames from endoscopy videos")
    p.add_argument("--output", type=str, default="data/jepa_frames")
    p.add_argument("--hyperkvasir-video", type=str, default="", help="Path to HyperKvasir video tree or zip extract")
    p.add_argument("--private-dir", type=str, default="data/private")
    p.add_argument("--fps", type=float, default=1.5, help="Target frames per second")
    p.add_argument("--max-frames-per-video", type=int, default=120)
    p.add_argument("--min-laplacian", type=float, default=30.0, help="Blur threshold (variance of Laplacian)")
    p.add_argument("--min-brightness", type=float, default=15.0, help="Reject very dark frames")
    args = p.parse_args()

    output = Path(args.output)
    manifest_entries: list[dict] = []

    if args.hyperkvasir_video:
        hk_root = Path(args.hyperkvasir_video)
        if hk_root.is_dir():
            manifest_entries.append(
                process_video_dir(
                    hk_root, output, "hyperkvasir_video", args.fps,
                    args.max_frames_per_video, args.min_laplacian, args.min_brightness,
                )
            )

    private_root = Path(args.private_dir)
    if private_root.is_dir():
        for center in sorted(private_root.iterdir()):
            if not center.is_dir():
                continue
            raw = center / "raw"
            if not raw.is_dir():
                continue
            manifest_entries.append(
                process_video_dir(
                    raw, output, f"private_{center.name}", args.fps,
                    args.max_frames_per_video, args.min_laplacian, args.min_brightness,
                )
            )

    if not manifest_entries:
        print(
            "No video sources processed. Provide --hyperkvasir-video or private data under "
            "data/private/{center_id}/raw/*.mp4",
            file=sys.stderr,
        )
        # Write empty manifest for pipeline continuity
        manifest_entries = []

    manifest = {
        "fps": args.fps,
        "max_frames_per_video": args.max_frames_per_video,
        "quality_filters": {
            "min_laplacian": args.min_laplacian,
            "min_brightness": args.min_brightness,
        },
        "sources": manifest_entries,
        "total_frames": sum(e.get("frames", 0) for e in manifest_entries),
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"Done. Total frames: {manifest['total_frames']} -> {output}")


if __name__ == "__main__":
    main()
