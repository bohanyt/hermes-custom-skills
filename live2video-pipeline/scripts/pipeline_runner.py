#!/usr/bin/env python3
"""
pipeline_runner.py — Orchestrator untuk Live2Video pipeline

Flow:
  Step 1: srt_cleaner.py     → Bersihkan SRT
  Step 2: topic_chunker.py   → Chunk + label
  Step 3: pipeline_cutter.py → Cut video per label

Usage:
  # Full pipeline
  python pipeline_runner.py video.mp4 stream.id.srt

  # Skip cleaning (kalau SRT udah bersih)
  python pipeline_runner.py video.mp4 stream.id.srt --skip-clean

  # Hanya specific labels
  python pipeline_runner.py video.mp4 stream.id.srt --labels storytime reaction

  # Hanya chunking (tanpa cut)
  python pipeline_runner.py video.mp4 stream.id.srt --chunk-only

  # Dry run
  python pipeline_runner.py video.mp4 stream.id.srt --dry-run

  # CUDA acceleration
  python pipeline_runner.py video.mp4 stream.id.srt --cuda
"""

import argparse
import subprocess
import sys
import json
import os
from pathlib import Path
from datetime import datetime


# ─── Config ───────────────────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).parent

SCRIPTS = {
    "srt_cleaner": SCRIPT_DIR / "srt_cleaner.py",
    "topic_chunker": SCRIPT_DIR / "topic_chunker.py",
    "pipeline_cutter": SCRIPT_DIR / "pipeline_cutter.py",
}

DEFAULT_LABELS = ["storytime", "reaction", "lore", "experience", "raw_clip", "shorts", "shorts_story", "tutorial"]


# ─── Helpers ──────────────────────────────────────────────────────────────────

def run_script(cmd, description="", dry_run=False):
    """Run a Python script"""
    if dry_run:
        print(f"  [DRY-RUN] {' '.join(str(c) for c in cmd)}")
        return True

    print(f"  ▶️  {description}")
    try:
        result = subprocess.run(
            [str(c) for c in cmd],
            capture_output=True,
            text=True,
            timeout=300,
        )
        if result.stdout:
            for line in result.stdout.strip().split("\n"):
                print(f"     {line}")
        if result.returncode != 0:
            print(f"  ❌ Error: {result.stderr[-300:]}")
            return False
        return True
    except subprocess.TimeoutExpired:
        print(f"  ❌ Timeout!")
        return False
    except Exception as e:
        print(f"  ❌ Exception: {e}")
        return False


def check_scripts():
    """Check that all required scripts exist"""
    missing = []
    for name, path in SCRIPTS.items():
        if not path.exists():
            missing.append(f"  ❌ {name}: {path}")
    if missing:
        print("❌ Missing scripts:")
        for m in missing:
            print(m)
        return False
    return True


# ─── Pipeline Steps ───────────────────────────────────────────────────────────

def step1_clean_srt(srt_path, output_dir, dry_run=False):
    """Step 1: Clean SRT"""
    cleaned_path = output_dir / "cleaned.srt"

    if cleaned_path.exists():
        print(f"  ⏭️  Cleaned SRT already exists: {cleaned_path}")
        return cleaned_path

    cmd = [
        sys.executable, str(SCRIPTS["srt_cleaner"]),
        str(srt_path),
        "--output", str(cleaned_path),
        "--merge-gap", "0.5",
        "--min-duration", "0.3",
    ]

    success = run_script(cmd, "Cleaning SRT (remove noise, merge segments)", dry_run)
    return cleaned_path if success else None


def step2_chunk(cleaned_srt, output_dir, target_minutes=2.5, shift_threshold=0.7, dry_run=False):
    """Step 2: Chunk + label"""
    chunks_path = output_dir / "chunks.json"

    if chunks_path.exists():
        print(f"  ⏭️  Chunks already exists: {chunks_path}")
        return chunks_path

    cmd = [
        sys.executable, str(SCRIPTS["topic_chunker"]),
        str(cleaned_srt),
        "--output", str(chunks_path),
        "--target-minutes", str(target_minutes),
        "--shift-threshold", str(shift_threshold),
    ]

    success = run_script(cmd, f"Chunking + labeling (~{target_minutes}min windows)", dry_run)
    return chunks_path if success else None


def step3_cut(video_path, chunks_path, output_dir, labels=None, use_cuda=False, dry_run=False):
    """Step 3: Cut video per label"""
    cuts_dir = output_dir / "cuts"

    if labels:
        label_args = []
        for l in labels:
            label_args.extend(["--label", l])
    else:
        label_args = ["--all"]

    cmd = [
        sys.executable, str(SCRIPTS["pipeline_cutter"]),
        str(chunks_path),
        str(video_path),
        "--output-dir", str(cuts_dir),
        "--min-score", "0",
    ] + label_args

    if use_cuda:
        cmd.append("--cuda")
    if dry_run:
        cmd.append("--dry-run")

    success = run_script(cmd, f"Cutting video → {cuts_dir}/", dry_run)
    return cuts_dir if success else None


# ─── Main ─────────────────────────────────────────────────────────────────────

def run_pipeline(
    video_path,
    srt_path,
    output_dir=None,
    labels=None,
    skip_clean=False,
    chunk_only=False,
    dry_run=False,
    use_cuda=False,
    target_minutes=2.5,
    shift_threshold=0.7,
):
    """Run full pipeline"""

    video_path = Path(video_path)
    srt_path = Path(srt_path)

    if not video_path.exists():
        print(f"❌ Video not found: {video_path}")
        return False
    if not srt_path.exists():
        print(f"❌ SRT not found: {srt_path}")
        return False

    # Determine output directory
    if output_dir is None:
        output_dir = video_path.parent / "pipeline_output"
    else:
        output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Check scripts
    if not check_scripts():
        return False

    # Determine labels
    if labels is None or len(labels) == 0:
        labels = DEFAULT_LABELS

    print("=" * 60)
    print("LIVE2VIDEO PIPELINE RUNNER")
    print("=" * 60)
    print(f"🎬 Video: {video_path}")
    print(f"📝 SRT: {srt_path}")
    print(f"📂 Output: {output_dir}")
    print(f"🏷️  Labels: {', '.join(labels)}")
    print(f"⚙️  Target: {target_minutes}min windows, shift_threshold={shift_threshold}")
    if use_cuda:
        print(f"🚀 CUDA: enabled")
    if dry_run:
        print(f"🔍 DRY RUN: no actual processing")
    print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # ── Step 1: Clean SRT ──
    print(f"\n{'─'*60}")
    print(f"STEP 1/3: Clean SRT")
    print(f"{'─'*60}")

    if skip_clean:
        print(f"  ⏭️  Skipped (--skip-clean)")
        cleaned_srt = srt_path
    else:
        cleaned_srt = step1_clean_srt(srt_path, output_dir, dry_run)
        if not cleaned_srt:
            print("❌ Step 1 failed")
            return False

    # ── Step 2: Chunk + Label ──
    print(f"\n{'─'*60}")
    print(f"STEP 2/3: Chunk + Label")
    print(f"{'─'*60}")

    chunks_path = step2_chunk(cleaned_srt, output_dir, target_minutes, shift_threshold, dry_run)
    if not chunks_path:
        print("❌ Step 2 failed")
        return False

    # Print chunk summary
    if chunks_path.exists() and not dry_run:
        with open(chunks_path, "r", encoding="utf-8") as f:
            chunks_data = json.load(f)
        label_counts = {}
        for c in chunks_data["chunks"]:
            lbl = c["label"]
            label_counts[lbl] = label_counts.get(lbl, 0) + 1
        print(f"\n  📊 Chunk summary:")
        for lbl, count in sorted(label_counts.items(), key=lambda x: -x[1]):
            print(f"     {lbl:15s} — {count:3d} chunks")

    if chunk_only:
        print(f"\n✅ Chunk-only mode — skipping cut")
        return True

    # ── Step 3: Cut Video ──
    print(f"\n{'─'*60}")
    print(f"STEP 3/3: Cut Video")
    print(f"{'─'*60}")

    cuts_dir = step3_cut(video_path, chunks_path, output_dir, labels, use_cuda, dry_run)
    if not cuts_dir:
        print("❌ Step 3 failed")
        return False

    # ── Summary ──
    print(f"\n{'='*60}")
    print(f"PIPELINE COMPLETE")
    print(f"{'='*60}")
    print(f"📂 Output: {output_dir}/")
    print(f"   ├── cleaned.srt")
    print(f"   ├── chunks.json")
    print(f"   └── cuts/")
    for lbl in labels:
        lbl_dir = cuts_dir / lbl
        if lbl_dir.exists():
            n_files = len(list(lbl_dir.glob("*.mp4")))
            print(f"       ├── {lbl}/ ({n_files} clips)")
    print(f"\n⏰ Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Live2Video Pipeline Runner — Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full pipeline
  python pipeline_runner.py video.mp4 stream.id.srt

  # Specific labels only
  python pipeline_runner.py video.mp4 stream.id.srt --labels storytime reaction

  # Skip cleaning (SRT udah bersih)
  python pipeline_runner.py video.mp4 stream.id.srt --skip-clean

  # Chunk only (no video cutting)
  python pipeline_runner.py video.mp4 stream.id.srt --chunk-only

  # Dry run
  python pipeline_runner.py video.mp4 stream.id.srt --dry-run

  # CUDA acceleration
  python pipeline_runner.py video.mp4 stream.id.srt --cuda

  # Custom output directory
  python pipeline_runner.py video.mp4 stream.id.srt --output-dir my_output/
        """
    )
    parser.add_argument("video", help="Path ke video file")
    parser.add_argument("srt", help="Path ke SRT/VTT subtitle file")
    parser.add_argument("--output-dir", "-o", default=None, help="Output directory")
    parser.add_argument("--labels", "-l", nargs="+", default=None,
                        help="Labels to process (default: all)")
    parser.add_argument("--skip-clean", action="store_true",
                        help="Skip SRT cleaning step")
    parser.add_argument("--chunk-only", action="store_true",
                        help="Only chunk + label, don't cut video")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print commands without executing")
    parser.add_argument("--cuda", action="store_true",
                        help="Use CUDA hardware acceleration")
    parser.add_argument("--target-minutes", "-t", type=float, default=2.5,
                        help="Chunk window size in minutes (default: 2.5)")
    parser.add_argument("--shift-threshold", "-s", type=float, default=0.7,
                        help="Topic shift threshold (default: 0.7)")

    args = parser.parse_args()

    run_pipeline(
        video_path=args.video,
        srt_path=args.srt,
        output_dir=args.output_dir,
        labels=args.labels,
        skip_clean=args.skip_clean,
        chunk_only=args.chunk_only,
        dry_run=args.dry_run,
        use_cuda=args.cuda,
        target_minutes=args.target_minutes,
        shift_threshold=args.shift_threshold,
    )


if __name__ == "__main__":
    main()
