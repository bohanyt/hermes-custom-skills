"""
SEMANTIC CHUNKER: Split transkrip VTT menjadi chunk kecil (~2.5 menit)
Simpan di hermes_skills/semanticchunker.py

Cara pakai:
  python semanticchunker.py "path/to/video.id.vtt"
  python semanticchunker.py "path/to/video.id.vtt" --target-minutes 3
  python semanticchunker.py "path/to/video.id.vtt" --output "path/to/chunks"

Output:
  <video_folder>/chunks/
    ├── chunks.json          ← semua chunks (metadata + path ke teks)
    ├── chunk_001.txt        ← teks chunk 1
    ├── chunk_002.txt        ← teks chunk 2
    └── ...

Setiap chunk target ~2.5 menit (bisa 2-4 menit), smart cut di jeda bicara.
Max ~5000 chars per chunk — aman untuk model kecil (8K context window).
"""

import argparse
import json
import re
import sys
from pathlib import Path
from datetime import timedelta

# ── config ──────────────────────────────────────────────────────────────
TARGET_MINUTES = 2.5          # durasi target per chunk (menit)
MIN_MINUTES = 1.5             # durasi minimum per chunk
MAX_MINUTES = 4.0             # durasi maximum per chunk
MAX_CHARS = 6000              # max chars per chunk (safety net)
SILENCE_THRESHOLD = 1.5       # detik jeda bicara untuk cut point

# ── VTT parser ──────────────────────────────────────────────────────────
def parse_transcript(file_path: str) -> list:
    """
    Parse file .vtt ATAU .srt menjadi list of segments.
    Auto-detect format berdasarkan ekstensi + isi file.
    Setiap segment: {start, end, text, start_sec, end_sec}
    """
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    ext = Path(file_path).suffix.lower()

    if ext == ".srt":
        return _parse_srt(content)
    else:
        return _parse_vtt(content)


def _parse_vtt(content: str) -> list:
    """Parse VTT format."""
    # Hapus header WEBVTT
    content = re.sub(r"^WEBVTT.*?\n\n", "", content, flags=re.DOTALL)
    blocks = re.split(r"\n\n+", content.strip())
    segments = []
    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) < 2:
            continue
        timestamp_line = None
        for i, line in enumerate(lines):
            if "-->" in line:
                timestamp_line = i
                break
        if timestamp_line is None:
            continue
        ts_text = lines[timestamp_line]
        ts_match = re.match(
            r"(\d{1,2}:\d{2}:\d{2}\.\d{3})\s*-->\s*(\d{1,2}:\d{2}:\d{2}\.\d{3})",
            ts_text
        )
        if not ts_match:
            ts_match = re.match(
                r"(\d{1,2}:\d{2}\.\d{3})\s*-->\s*(\d{1,2}:\d{2}\.\d{3})",
                ts_text
            )
        if not ts_match:
            continue
        start_str = ts_match.group(1)
        end_str = ts_match.group(2)
        text_lines = lines[timestamp_line + 1:]
        text = " ".join(tl.strip() for tl in text_lines if tl.strip())
        if not text:
            continue
        segments.append({
            "start": start_str,
            "end": end_str,
            "start_sec": timestamp_to_seconds(start_str),
            "end_sec": timestamp_to_seconds(end_str),
            "text": text
        })
    return segments


def _parse_srt(content: str) -> list:
    """Parse SRT format (timestamp pakai koma, ada nomor urut)."""
    # Normalize: ganti koma di timestamp jadi titik
    # SRT: 00:00:01,040 --> 00:00:07,720
    # VTT: 00:00:01.040 --> 00:00:07.720
    content = re.sub(r"(\d{2}:\d{2}:\d{2}),(\d{3})", r"\1.\2", content)

    # Split per block (dipisahkan oleh blank line)
    blocks = re.split(r"\n\n+", content.strip())

    segments = []
    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) < 2:
            continue

        # Skip nomor urut (line pertama yang cuma angka)
        start_idx = 0
        if re.match(r"^\d+$", lines[0].strip()):
            start_idx = 1

        # Cari line yang mengandung timestamp
        timestamp_line = None
        for i in range(start_idx, len(lines)):
            if "-->" in lines[i]:
                timestamp_line = i
                break

        if timestamp_line is None:
            continue

        ts_text = lines[timestamp_line]
        ts_match = re.match(
            r"(\d{1,2}:\d{2}:\d{2}\.\d{3})\s*-->\s*(\d{1,2}:\d{2}:\d{2}\.\d{3})",
            ts_text
        )
        if not ts_match:
            continue

        start_str = ts_match.group(1)
        end_str = ts_match.group(2)

        # Gabungkan teks (semua line setelah timestamp)
        text_lines = lines[timestamp_line + 1:]
        text = " ".join(tl.strip() for tl in text_lines if tl.strip())

        if not text:
            continue

        segments.append({
            "start": start_str,
            "end": end_str,
            "start_sec": timestamp_to_seconds(start_str),
            "end_sec": timestamp_to_seconds(end_str),
            "text": text
        })

    return segments


def timestamp_to_seconds(ts: str) -> float:
    """Convert HH:MM:SS.mmm atau MM:SS.mmm ke detik."""
    parts = ts.split(":")
    if len(parts) == 3:
        h, m, s = parts
        return int(h) * 3600 + int(m) * 60 + float(s)
    elif len(parts) == 2:
        m, s = parts
        return int(m) * 60 + float(s)
    return 0.0


def seconds_to_timestamp(sec: float) -> str:
    """Convert detik ke format HH:MM:SS.mmm"""
    td = timedelta(seconds=sec)
    total = int(td.total_seconds())
    h = total // 3600
    m = (total % 3600) // 60
    s = sec - (h * 3600 + m * 60)
    return f"{h:02d}:{m:02d}:{s:06.3f}"


# ── chunker ─────────────────────────────────────────────────────────────
def find_cut_point(segments: list, target_end_sec: float, search_window: float = 30.0) -> int:
    """
    Cari index segment terbaik untuk cut di sekitar target_end_sec.
    Prioritaskan jeda bicara (gap antar segment) yang > SILENCE_THRESHOLD.
    Search window: berapa detik sebelum/setelah target yang diperiksa.
    """
    best_idx = None
    best_gap = 0.0

    for i in range(len(segments) - 1):
        seg_end = segments[i]["end_sec"]
        next_start = segments[i + 1]["start_sec"]

        # Cek apakah segment ini dalam search window
        if abs(seg_end - target_end_sec) > search_window:
            continue

        gap = next_start - seg_end

        # Prioritaskan gap terbesar yang > threshold
        if gap >= SILENCE_THRESHOLD and gap > best_gap:
            best_gap = gap
            best_idx = i

    # Kalogak ada jeda yang cukup, pakai segment terdekat dengan target
    if best_idx is None:
        closest_dist = float("inf")
        for i, seg in enumerate(segments):
            dist = abs(seg["end_sec"] - target_end_sec)
            if dist < closest_dist:
                closest_dist = dist
                best_idx = i

    return best_idx


def chunk_segments(segments: list, target_minutes: float = TARGET_MINUTES) -> list:
    """
    Potong segments menjadi chunk berdasarkan durasi target.
    Smart cut: cari jeda bicara di sekitar titik potong.
    """
    if not segments:
        return []

    chunks = []
    total_duration = segments[-1]["end_sec"] - segments[0]["start_sec"]
    target_sec = target_minutes * 60

    chunk_start_idx = 0
    chunk_start_time = segments[0]["start_sec"]
    chunk_id = 1

    while chunk_start_idx < len(segments):
        # Hitung target end time untuk chunk ini
        target_end = chunk_start_time + target_sec

        # Cari segment terakhir yang masih dalam batas
        # Prioritaskan: jeda bicara > durasi minimum > durasi maximum
        min_end = chunk_start_time + (MIN_MINUTES * 60)
        max_end = chunk_start_time + (MAX_MINUTES * 60)

        # Cari cut point terbaik
        cut_idx = None

        # Phase 1: Cari jeda bicara dalam range [min_end, max_end]
        best_gap = 0.0
        for i in range(chunk_start_idx, len(segments)):
            if segments[i]["end_sec"] > max_end:
                break
            if segments[i]["end_sec"] < min_end:
                continue

            # Cek gap setelah segment ini
            if i + 1 < len(segments):
                gap = segments[i + 1]["start_sec"] - segments[i]["end_sec"]
                if gap >= SILENCE_THRESHOLD and gap > best_gap:
                    best_gap = gap
                    cut_idx = i

        # Phase 2: Kalogak ada jeda, pakai titik terdekat dengan target
        if cut_idx is None:
            closest_dist = float("inf")
            for i in range(chunk_start_idx, len(segments)):
                if segments[i]["end_sec"] > max_end:
                    break
                if i + 1 < len(segments):
                    next_start = segments[i + 1]["start_sec"]
                    if next_start > min_end:
                        dist = abs(segments[i]["end_sec"] - target_end)
                        if dist < closest_dist:
                            closest_dist = dist
                            cut_idx = i

        # Phase 3: Fallback — pakai segment terakhir sebelum max_end
        if cut_idx is None:
            for i in range(chunk_start_idx, len(segments)):
                if segments[i]["end_sec"] > max_end:
                    cut_idx = i - 1 if i > chunk_start_idx else i
                    break
            if cut_idx is None:
                cut_idx = len(segments) - 1

        # Safety: cek char count, kalau kebanyakan potong lebih awal
        chunk_text = " ".join(s["text"] for s in segments[chunk_start_idx:cut_idx + 1])
        if len(chunk_text) > MAX_CHARS and cut_idx > chunk_start_idx:
            # Potong setengah
            cut_idx = chunk_start_idx + (cut_idx - chunk_start_idx) // 2

        # Buat chunk
        chunk_segments = segments[chunk_start_idx:cut_idx + 1]
        chunk_text = " ".join(s["text"] for s in chunk_segments)

        chunk = {
            "chunk_id": f"chunk_{chunk_id:03d}",
            "start_time": seconds_to_timestamp(chunk_segments[0]["start_sec"]),
            "end_time": seconds_to_timestamp(chunk_segments[-1]["end_sec"]),
            "start_sec": chunk_segments[0]["start_sec"],
            "end_sec": chunk_segments[-1]["end_sec"],
            "duration_sec": round(chunk_segments[-1]["end_sec"] - chunk_segments[0]["start_sec"]),
            "char_count": len(chunk_text),
            "word_count": len(chunk_text.split()),
            "segment_count": len(chunk_segments),
            "text": chunk_text
        }
        chunks.append(chunk)

        # Next chunk
        chunk_start_idx = cut_idx + 1
        if chunk_start_idx < len(segments):
            chunk_start_time = segments[chunk_start_idx]["start_sec"]
        chunk_id += 1

    return chunks


# ── main ────────────────────────────────────────────────────────────────
def process_transcript(file_path: str, target_minutes: float = TARGET_MINUTES, output_dir: str = None):
    """
    Main: parse VTT/SRT → chunk → simpan ke folder chunks/
    """
    file_path = Path(file_path)
    if not file_path.exists():
        print(f"❌ File tidak ditemukan: {file_path}")
        sys.exit(1)

    # Tentukan output directory
    if output_dir:
        chunks_dir = Path(output_dir)
    else:
        chunks_dir = file_path.parent / "chunks"

    chunks_dir.mkdir(parents=True, exist_ok=True)

    # Parse transcript (auto-detect VTT/SRT)
    print("=" * 60)
    print(f"STEP 1: Parsing {file_path.suffix}...")
    print("=" * 60)
    segments = parse_transcript(str(file_path))
    print(f"  📊 Total segments: {len(segments)}")
    if segments:
        total_dur = segments[-1]["end_sec"] - segments[0]["start_sec"]
        print(f"  ⏱️  Total duration: {seconds_to_timestamp(total_dur)}")
    print()

    # Chunk
    print("=" * 60)
    print(f"STEP 2: Chunking (~{target_minutes} menit per chunk)...")
    print("=" * 60)
    chunks = chunk_segments(segments, target_minutes)
    print(f"  📦 Total chunks: {len(chunks)}")
    print()

    # Simpan chunks.json
    chunks_json_path = chunks_dir / "chunks.json"
    chunks_summary = []
    for c in chunks:
        summary = {k: v for k, v in c.items() if k != "text"}
        summary["text_file"] = f"{c['chunk_id']}.txt"
        chunks_summary.append(summary)

    with open(chunks_json_path, "w", encoding="utf-8") as f:
        json.dump(chunks_summary, f, ensure_ascii=False, indent=2)
    print(f"  📝 Saved: {chunks_json_path}")

    # Simpan per-chunk text files
    for c in chunks:
        chunk_txt_path = chunks_dir / f"{c['chunk_id']}.txt"
        with open(chunk_txt_path, "w", encoding="utf-8") as f:
            f.write(f"# {c['chunk_id']}\n")
            f.write(f"# {c['start_time']} → {c['end_time']}\n")
            f.write(f"# Duration: {c['duration_sec']}s | Words: {c['word_count']} | Chars: {c['char_count']}\n")
            f.write("#" + "=" * 58 + "\n\n")
            f.write(c["text"])
        print(f"  📄 {c['chunk_id']}.txt ({c['word_count']} words, {c['char_count']} chars)")

    # Ringkasan
    print()
    print("=" * 60)
    print("✅ DONE!")
    print("=" * 60)
    print(f"  📂 Chunks dir: {chunks_dir}")
    print(f"  📊 Total chunks: {len(chunks)}")
    if chunks:
        avg_dur = sum(c["duration_sec"] for c in chunks) / len(chunks)
        avg_chars = sum(c["char_count"] for c in chunks) / len(chunks)
        max_chars = max(c["char_count"] for c in chunks)
        print(f"  ⏱️  Avg duration: {avg_dur:.0f}s ({avg_dur/60:.1f} min)")
        print(f"  📏 Avg chars: {avg_chars:.0f}")
        print(f"  📏 Max chars: {max_chars}")
        print(f"  📏 Min chars: {min(c['char_count'] for c in chunks)}")

    return chunks_dir


def main():
    parser = argparse.ArgumentParser(
        description="Split transkrip VTT/SRT menjadi chunk kecil (~2.5 menit)"
    )
    parser.add_argument("file", help="Path ke file .vtt atau .srt")
    parser.add_argument(
        "--target-minutes", "-t",
        type=float,
        default=TARGET_MINUTES,
        help=f"Durasi target per chunk dalam menit (default: {TARGET_MINUTES})"
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Output directory (default: <folder>/chunks/)"
    )

    args = parser.parse_args()
    process_transcript(args.file, args.target_minutes, args.output)


if __name__ == "__main__":
    main()
