#!/usr/bin/env python3
"""
pipeline_cutter.py — Cut video berdasarkan label dari topic_chunker.py

Baca chunks.json (output dari topic_chunker.py), filter by label,
dan cut video-nya pakai ffmpeg.

Usage:
  python pipeline_cutter.py chunks.json video.mp4 --label storytime
  python pipeline_cutter.py chunks.json video.mp4 --label reaction --output-dir clips/reaction/
  python pipeline_cutter.py chunks.json video.mp4 --label raw_clip --min-score 3
  python pipeline_cutter.py chunks.json video.mp4 --all --output-dir clips/

Options:
  --label TYPE       — Hanya cut chunk dengan label ini (bisa dipanggil berkali-kali)
  --all              — Cut semua chunk yang bukan unknown
  --min-score N      — Minimal score (default: 0)
  --min-duration N   — Minimal durasi detik (default: 0)
  --max-duration N   — Maksimal durasi detik (default: 99999)
  --output-dir DIR   — Output directory (default: cuts/)
  --dry-run          — Print ffmpeg commands tanpa execute
  --cuda             — Gunakan CUDA hardware acceleration (decode + encode)
"""

import json
import argparse
import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime


# ─── Config ───────────────────────────────────────────────────────────────────

# FFmpeg encode settings per label
ENCODE_PRESETS = {
    "storytime": {
        "_comment": "Storytime: kualitas tinggi, audio jelas",
        "video_codec": "libx264",
        "video_preset": "slow",
        "crf": "18",
        "audio_codec": "aac",
        "audio_bitrate": "192k",
    },
    "reaction": {
        "_comment": "Reaction: cepat, medium quality",
        "video_codec": "libx264",
        "video_preset": "medium",
        "crf": "22",
        "audio_codec": "aac",
        "audio_bitrate": "128k",
    },
    "lore": {
        "_comment": "Lore: kualitas tinggi",
        "video_codec": "libx264",
        "video_preset": "slow",
        "crf": "20",
        "audio_codec": "aac",
        "audio_bitrate": "192k",
    },
    "experience": {
        "_comment": "Experience: kualitas tinggi",
        "video_codec": "libx264",
        "video_preset": "slow",
        "crf": "19",
        "audio_codec": "aac",
        "audio_bitrate": "192k",
    },
    "raw_clip": {
        "_comment": "Raw clip: fast encode, good enough quality",
        "video_codec": "libx264",
        "video_preset": "fast",
        "crf": "23",
        "audio_codec": "aac",
        "audio_bitrate": "128k",
    },
    "shorts": {
        "_comment": "Shorts: optimized for vertical/mobile",
        "video_codec": "libx264",
        "video_preset": "medium",
        "crf": "22",
        "audio_codec": "aac",
        "audio_bitrate": "128k",
    },
    "shorts_story": {
        "_comment": "Shorts story: optimized for vertical/mobile",
        "video_codec": "libx264",
        "video_preset": "medium",
        "crf": "22",
        "audio_codec": "aac",
        "audio_bitrate": "128k",
    },
    "tutorial": {
        "_comment": "Tutorial: kualitas tinggi, audio jelas",
        "video_codec": "libx264",
        "video_preset": "slow",
        "crf": "19",
        "audio_codec": "aac",
        "audio_bitrate": "192k",
    },
    "default": {
        "video_codec": "libx264",
        "video_preset": "medium",
        "crf": "22",
        "audio_codec": "aac",
        "audio_bitrate": "128k",
    },
}

CUDA_FLAGS = {
    "input": "-hwaccel cuda -hwaccel_output_format cuda",
    "decode_hw": "-hwaccel cuda",
}


# ─── Helpers ──────────────────────────────────────────────────────────────────

def ts_to_sec(ts):
    """HH:MM:SS.mmm to seconds"""
    parts = ts.split(":")
    if len(parts) == 3:
        return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
    elif len(parts) == 2:
        return float(parts[0]) * 60 + float(parts[1])
    return 0.0


def build_ffmpeg_cmd(chunk, video_path, output_path, preset, use_cuda=False, av1_source=False):
    """Build ffmpeg command untuk cut satu chunk"""
    duration = chunk["duration_sec"]

    if use_cuda:
        # CUDA decode + NVENC encode
        # Untuk AV1 source: CUDA decode → NVENC encode H.264
        # Untuk H.264 source: CUDA decode → NVENC encode H.264
        cmd = [
            "ffmpeg",
            "-y",
            "-hwaccel", "cuda",
            "-hwaccel_output_format", "cuda",
            "-ss", chunk["start_ts"],
            "-i", str(video_path),
            "-t", str(duration),
            "-c:v", "h264_nvenc",
            "-preset", "p4",       # NVENC preset: p1(fast) to p7(slow)
            "-cq", preset["crf"],
            "-c:a", preset["audio_codec"],
            "-b:a", preset["audio_bitrate"],
            str(output_path),
        ]
    else:
        # CPU encode
        cmd = [
            "ffmpeg",
            "-y",
            "-ss", chunk["start_ts"],
            "-i", str(video_path),
            "-t", str(duration),
            "-c:v", preset["video_codec"],
            "-preset", preset["video_preset"],
            "-crf", preset["crf"],
            "-c:a", preset["audio_codec"],
            "-b:a", preset["audio_bitrate"],
            str(output_path),
        ]

    return cmd


def detect_source_codec(video_path):
    """Detect source video codec menggunakan ffprobe"""
    try:
        cmd = [
            "ffprobe",
            "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=codec_name",
            "-of", "json",
            str(video_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        data = json.loads(result.stdout)
        codec = data["streams"][0]["codec_name"]
        return codec
    except Exception:
        return "unknown"


def run_ffmpeg(cmd, dry_run=False):
    """Run ffmpeg command"""
    if dry_run:
        print(f"  [DRUN-RUN] {' '.join(cmd)}")
        return True

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,  # 10 min timeout per clip
        )
        if result.returncode != 0:
            print(f"  ❌ Error: {result.stderr[-200:]}")
            return False
        return True
    except subprocess.TimeoutExpired:
        print(f"  ❌ Timeout!")
        return False
    except Exception as e:
        print(f"  ❌ Exception: {e}")
        return False


# ─── Main ─────────────────────────────────────────────────────────────────────

def process(
    chunks_json,
    video_path,
    labels=None,
    all_labels=False,
    min_score=0,
    min_duration=0,
    max_duration=99999,
    output_dir="cuts/",
    dry_run=False,
    use_cuda=False,
):
    """Main: filter chunks → cut video"""

    print("=" * 60)
    print("PIPELINE CUTTER")
    print("=" * 60)

    # Load chunks
    with open(chunks_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    all_chunks = data["chunks"]
    print(f"\n📂 Chunks: {len(all_chunks)} total")
    print(f"🎬 Video: {video_path}")

    # Detect source codec
    source_codec = detect_source_codec(video_path)
    print(f"📹 Source codec: {source_codec}")
    is_av1 = source_codec in ("av1", "av01")
    if is_av1:
        print(f"⚠️  AV1 source detected —建议使用 --cuda flag untuk hardware decode")

    # Filter chunks
    if all_labels:
        filtered = [c for c in all_chunks if c["label"] != "unknown"]
    elif labels:
        filtered = [c for c in all_chunks if c["label"] in labels]
    else:
        print("❌ Specify --label TYPE or --all")
        return

    # Apply filters
    filtered = [
        c for c in filtered
        if c["score"] >= min_score
        and c["duration_sec"] >= min_duration
        and c["duration_sec"] <= max_duration
    ]

    if not filtered:
        print(f"\n❌ No chunks match filters")
        return

    # Group by label
    by_label = {}
    for c in filtered:
        lbl = c["label"]
        if lbl not in by_label:
            by_label[lbl] = []
        by_label[lbl].append(c)

    print(f"\n📊 Filtered chunks: {len(filtered)} (from {len(all_chunks)} total)")
    for lbl, chunks in sorted(by_label.items()):
        print(f"   {lbl:15s} — {len(chunks)} chunks")

    # Create output dir
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Process each chunk
    print(f"\n{'─'*60}")
    print(f"  CUTTING")
    print(f"{'─'*60}")

    results = {"success": 0, "failed": 0, "skipped": 0}

    for lbl, chunks in sorted(by_label.items()):
        lbl_dir = output_dir / lbl
        lbl_dir.mkdir(parents=True, exist_ok=True)

        preset = ENCODE_PRESETS.get(lbl, ENCODE_PRESETS["default"])

        print(f"\n🏷️  Label: {lbl} ({len(chunks)} chunks)")
        print(f"   Output: {lbl_dir}/")
        print(f"   Preset: {preset.get('_comment', '')}")

        for chunk in chunks:
            chunk_id = chunk["chunk_id"]
            dur = chunk["duration_sec"]
            dur_m = int(dur // 60)
            dur_s = int(dur % 60)

            # Output filename: {label}_{chunk_id}_{start_ts}.mp4
            safe_ts = chunk["start_ts"].replace(":", "-").replace(".", "_")
            out_filename = f"{chunk_id}_{lbl}_{safe_ts}.mp4"
            out_path = lbl_dir / out_filename

            # Skip if already exists
            if out_path.exists():
                print(f"  ⏭️  {chunk_id} ({dur_m}m{dur_s}s) — already exists, skip")
                results["skipped"] += 1
                continue

            print(f"  ✂️  {chunk_id} [{chunk['start_ts']} → {chunk['end_ts']}] ({dur_m}m{dur_s}s) score={chunk['score']}")

            cmd = build_ffmpeg_cmd(chunk, video_path, out_path, preset, use_cuda=use_cuda)

            success = run_ffmpeg(cmd, dry_run=dry_run)

            if success:
                results["success"] += 1
                # Get output file size
                if not dry_run and out_path.exists():
                    size_mb = out_path.stat().st_size / (1024 * 1024)
                    print(f"     ✅ {out_filename} ({size_mb:.1f}MB)")
            else:
                results["failed"] += 1

    # Summary
    print(f"\n{'='*60}")
    print(f"  RESULTS")
    print(f"{'='*60}")
    print(f"  ✅ Success: {results['success']}")
    print(f"  ⏭️  Skipped: {results['skipped']}")
    print(f"  ❌ Failed:  {results['failed']}")
    print(f"  📂 Output: {output_dir}/")

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Cut video berdasarkan label dari topic_chunker.py",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Cut storytime chunks
  python pipeline_cutter.py chunks.json video.mp4 --label storytime

  # Cut multiple labels
  python pipeline_cutter.py chunks.json video.mp4 --label reaction --label lore

  # Cut all non-unknown chunks
  python pipeline_cutter.py chunks.json video.mp4 --all

  # CUDA acceleration (untuk AV1 source)
  python pipeline_cutter.py chunks.json video.mp4 --label storytime --cuda

  # Dry run (print commands only)
  python pipeline_cutter.py chunks.json video.mp4 --label storytime --dry-run

  # With filters
  python pipeline_cutter.py chunks.json video.mp4 --label storytime --min-score 3 --min-duration 30
        """
    )
    parser.add_argument("chunks_json", help="Path ke chunks.json (output dari topic_chunker.py)")
    parser.add_argument("video", help="Path ke source video file")
    parser.add_argument("--label", "-l", action="append", metavar="TYPE",
                        help="Label untuk filter (bisa dipanggil berkali-kali)")
    parser.add_argument("--all", "-a", action="store_true",
                        help="Cut semua chunk yang bukan unknown")
    parser.add_argument("--min-score", type=float, default=0,
                        help="Minimal score (default: 0)")
    parser.add_argument("--min-duration", type=float, default=0,
                        help="Minimal durasi dalam detik (default: 0)")
    parser.add_argument("--max-duration", type=float, default=99999,
                        help="Maksimal durasi dalam detik (default: 99999)")
    parser.add_argument("--output-dir", "-o", default="cuts/",
                        help="Output directory (default: cuts/)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print ffmpeg commands tanpa execute")
    parser.add_argument("--cuda", action="store_true",
                        help="Gunakan CUDA hardware acceleration")

    args = parser.parse_args()

    process(
        chunks_json=args.chunks_json,
        video_path=Path(args.video),
        labels=args.label,
        all_labels=args.all,
        min_score=args.min_score,
        min_duration=args.min_duration,
        max_duration=args.max_duration,
        output_dir=args.output_dir,
        dry_run=args.dry_run,
        use_cuda=args.cuda,
    )


if __name__ == "__main__":
    main()
