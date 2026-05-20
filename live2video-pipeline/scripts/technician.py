"""
TECHNICIAN: Cut video menjadi potongan-potongan terpisah
Simpan di hermes_skills/technician.py

Baca topics.json atau edit_plan.json, cut per segment, output terpisah (gak di-merge).
Format nama: a_00h21m20s_00h22m45s.mp4

Cara pakai:
  python technician.py "path/to/topics.json" --video "path/to/video.mp4" --mode topics
  python technician.py "path/to/edit_plan.json" --video "path/to/video.mp4" --mode editplan

Output:
  <video_folder>/../final_cuts/<video_name>/
    ├── a_00h21m20s_00h22m45s.mp4      ← potongan A
    ├── b_00h45m10s_00h46m30s.mp4      ← potongan B
    ├── c_01h15m00s_01h18m20s.mp4      ← potongan C
    └── render_log.json                 ← log render
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

# ── config ─────────────────────────────────────────────────────────────
FFMPEG = "ffmpeg"  # harus ada di PATH
FINAL_CUTS_DIR_NAME = "final_cuts"


def find_video_file(chunks_dir: Path) -> Path | None:
    """Cari file video di folder raw_footages (parent dari chunks)."""
    video_dir = chunks_dir.parent  # raw_footages/<video_name>/
    for ext in [".mp4", ".mkv", ".webm", ".avi", ".mov"]:
        for f in video_dir.glob(f"*{ext}"):
            if f.is_file() and f.stat().st_size > 1_000_000:  # > 1MB (bukan .part)
                return f
    return None


def timestamp_to_seconds(ts: str) -> float:
    """Convert HH:MM:SS or MM:SS to seconds."""
    parts = ts.strip().split(":")
    if len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    elif len(parts) == 2:
        return int(parts[0]) * 60 + float(parts[1])
    return 0.0


def format_ts_filename(ts: str) -> str:
    """Convert HH:MM:SS -> 00h21m20s untuk filename Windows-compatible."""
    parts = ts.strip().split(":")
    if len(parts) == 3:
        h, m, s = parts[0], parts[1], parts[2].split(".")[0]  # hapus milidetik
        return f"{h}h{m}m{s}s"
    elif len(parts) == 2:
        m, s = parts[0], parts[1].split(".")[0]
        return f"00h{m}m{s}s"
    return "unknown"


def get_alphabet_label(index: int) -> str:
    """Convert index ke alphabet: 0=a, 1=b, ..., 25=z, 26=aa, ..."""
    label = ""
    while index >= 0:
        label = chr(97 + (index % 26)) + label
        index = (index // 26) - 1
    return label


def generate_cut_segments(edit_plan: dict) -> list:
    """
    Generate cut segments dari edit_plan.
    Return list of {start, end, start_sec, end_sec, label}.
    """
    segments = []
    bagian_dipertahankan = edit_plan.get("bagian_dipertahankan", [])

    if bagian_dipertahankan:
        for b in bagian_dipertahankan:
            ts = b.get("timestamp", "")
            if " - " in ts:
                start, end = ts.split(" - ", 1)
                start_sec = timestamp_to_seconds(start)
                end_sec = timestamp_to_seconds(end)
                if end_sec > start_sec:
                    segments.append({
                        "start": start.strip(),
                        "end": end.strip(),
                        "start_sec": start_sec,
                        "end_sec": end_sec,
                        "label": b.get("tipe", "highlight")
                    })

    return segments


def cut_single_segment(video_path: Path, start: str, end: str, output_path: Path) -> bool:
    """Cut 1 segment dari video, save ke output_path. Stream copy (cepat)."""
    duration = timestamp_to_seconds(end) - timestamp_to_seconds(start)

    cmd = [
        FFMPEG,
        "-y",
        "-ss", start,
        "-i", str(video_path),
        "-t", str(duration),
        "-c", "copy",
        "-avoid_negative_ts", "make_zero",
        str(output_path)
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True, text=True,
            timeout=300
        )
        if result.returncode == 0 and output_path.exists() and output_path.stat().st_size > 0:
            return True
        else:
            print(f"    ❌ ffmpeg error: {result.stderr[:200]}")
            return False
    except subprocess.TimeoutExpired:
        print(f"    ❌ Timeout cutting {start} -> {end}")
        return False
    except Exception as e:
        print(f"    ❌ Error: {e}")
        return False


def run_technician(edit_plan_path: str, video_path: str = None):
    """
    Baca edit_plan.json → cut per segment → output terpisah ke final_cuts/.
    """
    plan_file = Path(edit_plan_path)
    if not plan_file.exists():
        print(f"❌ File tidak ditemukan: {plan_file}")
        sys.exit(1)

    chunks_dir = plan_file.parent
    video_dir = chunks_dir.parent  # raw_footages/<video_name>/

    # Load edit plan
    with open(plan_file, "r", encoding="utf-8") as f:
        edit_plans = json.load(f)
    if isinstance(edit_plans, dict):
        edit_plans = [edit_plans]

    # Cari video file
    if video_path:
        video_file = Path(video_path)
    else:
        video_file = find_video_file(chunks_dir)

    if not video_file or not video_file.exists():
        print(f"❌ Video file tidak ditemukan")
        print(f"   Cari di: {video_dir}")
        sys.exit(1)

    # Setup output dir
    final_cuts_dir = video_dir.parent / FINAL_CUTS_DIR_NAME / video_dir.name
    final_cuts_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("TECHNICIAN — Video Cutter (ffmpeg stream copy)")
    print("=" * 60)
    print(f"  📂 Video: {video_file}")
    print(f"  📂 Output: {final_cuts_dir}")
    print(f"  📊 Konten: {len(edit_plans)}")
    print()

    # Cek ffmpeg available
    try:
        result = subprocess.run([FFMPEG, "-version"], capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            print("❌ ffmpeg tidak ditemukan di PATH")
            print("   Install: https://ffmpeg.org/download.html")
            sys.exit(1)
    except FileNotFoundError:
        print("❌ ffmpeg tidak ditemukan di PATH")
        sys.exit(1)

    render_log = []
    global_seg_index = 0  # counter global untuk alphabet label

    for i, plan in enumerate(edit_plans):
        konten_id = plan.get("konten_id", i + 1)
        jenis = plan.get("jenis", "Unknown")
        durasi = plan.get("durasi_estimasi_final", "?")

        print(f"[{konten_id}/{len(edit_plans)}] Cutting: {jenis} (est: {durasi})")

        # Generate segments dari edit_plan
        segments = generate_cut_segments(plan)
        if not segments:
            print(f"  ⚠️  No segments defined, skipping")
            render_log.append({
                "konten_id": konten_id,
                "status": "skipped",
                "reason": "No segments defined"
            })
            continue

        print(f"  📊 Segments: {len(segments)}")

        konten_clips = []
        for seg in segments:
            label = get_alphabet_label(global_seg_index)
            start_fmt = format_ts_filename(seg["start"])
            end_fmt = format_ts_filename(seg["end"])
            filename = f"{label}_{start_fmt}_{end_fmt}.mp4"
            output_path = final_cuts_dir / filename

            print(f"    [{label}] {seg['start']} -> {seg['end']} ({seg['label']})")

            success = cut_single_segment(video_file, seg["start"], seg["end"], output_path)

            if success:
                size_mb = output_path.stat().st_size / (1024 * 1024)
                print(f"    ✅ {filename} ({size_mb:.1f} MB)")
                konten_clips.append({
                    "filename": filename,
                    "label": label,
                    "start": seg["start"],
                    "end": seg["end"],
                    "size_mb": round(size_mb, 1)
                })
            else:
                print(f"    ❌ Failed: {filename}")
                konten_clips.append({
                    "filename": filename,
                    "label": label,
                    "start": seg["start"],
                    "end": seg["end"],
                    "status": "failed"
                })

            global_seg_index += 1

        render_log.append({
            "konten_id": konten_id,
            "jenis": jenis,
            "status": "done",
            "clips": konten_clips,
            "duration_est": durasi
        })

        print()

    # Simpan render log
    log_path = final_cuts_dir / "render_log.json"
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(render_log, f, ensure_ascii=False, indent=2)

    # Ringkasan
    total_clips = sum(len(r.get("clips", [])) for r in render_log)
    success_clips = sum(
        1 for r in render_log
        for c in r.get("clips", [])
        if c.get("status") != "failed"
    )

    print("=" * 60)
    print("✅ CUT COMPLETE")
    print("=" * 60)
    print(f"  📊 Total clips: {success_clips}/{total_clips}")
    print(f"  📂 Output: {final_cuts_dir}")
    print(f"  📝 Log: {log_path}")
    print()

    # List output files
    print("Output files:")
    for f in sorted(final_cuts_dir.iterdir()):
        if f.suffix in [".mp4", ".mkv", ".webm"]:
            size_mb = f.stat().st_size / (1024 * 1024)
            print(f"  📄 {f.name} ({size_mb:.1f} MB)")

    return final_cuts_dir


def run_technician_from_segments(segments: list, video_path: str = None, base_dir: Path = None):
    """Run technician dari segments list (dari topics)."""
    if not segments:
        print("❌ No segments to cut")
        return None
    
    # Find video
    video = None
    if video_path:
        video = Path(video_path)
    elif base_dir:
        # Auto-detect video di parent folder
        video_dir = base_dir.parent  # raw_footages/<video_name>/
        for ext in [".mp4", ".mkv", ".webm", ".avi", ".mov"]:
            for f in video_dir.glob(f"*{ext}"):
                if f.is_file() and f.stat().st_size > 1_000_000:
                    video = f
                    break
            if video:
                break
    
    if not video or not video.exists():
        print("❌ Video file tidak ditemukan")
        return None
    
    # Create output dir
    if base_dir:
        final_cuts_dir = base_dir.parent / "final_cuts" / "topics"
    else:
        final_cuts_dir = Path("final_cuts")
    final_cuts_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("TECHNICIAN — Video Cutter (from topics)")
    print("=" * 60)
    print(f"  📂 Video: {video}")
    print(f"  📂 Output: {final_cuts_dir}")
    print(f"  📊 Segments: {len(segments)}")
    print()
    
    # Sort by engagement score (highest first)
    segments.sort(key=lambda s: s.get("engagement_score", 5), reverse=True)
    
    # Cut per segment
    all_clips = []
    for i, seg in enumerate(segments):
        label = get_alphabet_label(i)
        start = seg["start"]
        end = seg["end"]
        seg_label = seg.get("label", "highlight")
        video_type = seg.get("video_type", "")
        score = seg.get("engagement_score", 5)
        
        start_fn = format_ts_filename(start)
        end_fn = format_ts_filename(end)
        output_name = f"{label}_{start_fn}_{end_fn}.mp4"
        output_path = final_cuts_dir / output_name
        
        dur_sec = seg["end_sec"] - seg["start_sec"]
        dur_min = dur_sec // 60
        dur_rem = dur_sec % 60
        
        print(f"  [{label}] {seg_label} ({video_type}, score:{score})")
        print(f"    ⏱️ {start} → {end} ({dur_min}m{dur_rem}s)")
        
        if cut_single_segment(video, start, end, output_path):
            size_mb = output_path.stat().st_size / (1024 * 1024)
            print(f"    ✅ {output_name} ({size_mb:.1f} MB)")
            all_clips.append({
                "label": label,
                "file": output_name,
                "size_mb": round(size_mb, 1),
                "start": start,
                "end": end,
                "duration_sec": dur_sec,
                "video_type": video_type,
                "engagement_score": score,
                "topic_label": seg_label,
            })
        else:
            print(f"    ❌ Failed")
    
    # Save log
    log_path = final_cuts_dir / "render_log.json"
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump({"clips": all_clips}, f, ensure_ascii=False, indent=2)
    
    print()
    print("=" * 60)
    print("✅ CUT COMPLETE")
    print("=" * 60)
    print(f"  📊 Total clips: {len(all_clips)}/{len(segments)}")
    print(f"  📂 Output: {final_cuts_dir}")
    
    return final_cuts_dir


def generate_segments_from_topics(topics: list) -> list:
    """Generate cut segments dari topics.json."""
    segments = []
    for t in topics:
        start = t.get("start_time", "00:00:00")
        end = t.get("end_time", "00:00:00")
        start_sec = timestamp_to_seconds(start)
        end_sec = timestamp_to_seconds(end)
        duration = t.get("duration_sec", end_sec - start_sec)
        
        # Skip if too short (< 30s) or too long (> 600s)
        if duration < 30:
            continue
        if duration > 600:
            # Split long topics into multiple segments
            mid_sec = start_sec + duration // 2
            mid_ts = seconds_to_timestamp(mid_sec)
            segments.append({
                "start": start,
                "end": mid_ts,
                "start_sec": start_sec,
                "end_sec": mid_sec,
                "label": t.get("label", "highlight"),
                "video_type": t.get("video_type", ""),
                "engagement_score": t.get("engagement_score", 5),
            })
            segments.append({
                "start": mid_ts,
                "end": end,
                "start_sec": mid_sec,
                "end_sec": end_sec,
                "label": t.get("label", "highlight") + " (part 2)",
                "video_type": t.get("video_type", ""),
                "engagement_score": t.get("engagement_score", 5),
            })
        else:
            segments.append({
                "start": start,
                "end": end,
                "start_sec": start_sec,
                "end_sec": end_sec,
                "label": t.get("label", "highlight"),
                "video_type": t.get("video_type", ""),
                "engagement_score": t.get("engagement_score", 5),
            })
    return segments


def main():
    parser = argparse.ArgumentParser(
        description="Technician: cut video menjadi potongan-potongan terpisah"
    )
    parser.add_argument("input_file", help="Path ke topics.json atau edit_plan.json")
    parser.add_argument(
        "--video", "-v",
        default=None,
        help="Path ke video file (default: auto-detect)"
    )
    parser.add_argument(
        "--mode", "-m",
        choices=["topics", "editplan"],
        default="editplan",
        help="Mode: topics (dari topic_detector) atau editplan (dari retention_architect)"
    )

    args = parser.parse_args()
    
    if args.mode == "topics":
        # Load topics.json
        with open(args.input_file, "r", encoding="utf-8") as f:
            topics = json.load(f)
        segments = generate_segments_from_topics(topics)
        print(f"  📊 Generated {len(segments)} segments from {len(topics)} topics")
        # Save segments as edit_plan for reference
        edit_plan_path = Path(args.input_file).parent / "edit_plan_from_topics.json"
        with open(edit_plan_path, "w", encoding="utf-8") as f:
            json.dump({"segments": segments}, f, ensure_ascii=False, indent=2)
        run_technician_from_segments(segments, args.video, Path(args.input_file).parent)
    else:
        run_technician(args.input_file, args.video)


if __name__ == "__main__":
    main()
