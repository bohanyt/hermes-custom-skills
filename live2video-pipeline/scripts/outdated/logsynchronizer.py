"""
LOG SYNCHRONIZER: Proses & sinkronisasi data mentah
Simpan di hermes_skills/logsynchronizer.py

Baca markers.txt, live_chat.json, transkrip VTT.
Hitung chat spikes (MPM), potong transkrip per chunk.
Output: paket data rapi untuk Data Miner.

Cara pakai:
  python logsynchronizer.py --video-dir "path/to/raw_footages/Nama Video/"
  python logsynchronizer.py --video-dir "path/to/video/" --markers "markers.txt" --chat "live_chat.json"

Output:
  <video_folder>/
    └── sync_data.json        ← data tersinkronisasi per chunk
"""

import argparse
import json
import re
import sys
from pathlib import Path
from datetime import datetime

# ── config ──────────────────────────────────────────────────────────────
SPIKE_THRESHOLD = 5.0    # MPM > 5x average = spike
MIN_SPIKE_ABSOLUTE = 10  # Minimal 10 pesan/menit untuk dianggap spike


# ── helpers ─────────────────────────────────────────────────────────────
def timestamp_to_seconds(ts: str) -> float:
    """Convert HH:MM:SS or MM:SS to seconds."""
    parts = ts.strip().split(":")
    if len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    elif len(parts) == 2:
        return int(parts[0]) * 60 + float(parts[1])
    return 0.0


def seconds_to_timestamp(sec: float) -> str:
    """Convert seconds to HH:MM:SS."""
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = sec % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}"


# ── markers ─────────────────────────────────────────────────────────────
def load_markers(markers_path: str) -> list:
    """
    Load manual markers dari file.
    Format: 1 timestamp per line (HH:MM:SS atau MM:SS).
    Bisa juga format JSON: [{"time": "01:14:30", "label": "..."}, ...]
    """
    path = Path(markers_path)
    if not path.exists():
        print(f"  ⚠️  Markers file tidak ditemukan: {path}")
        return []

    with open(path, "r", encoding="utf-8") as f:
        content = f.read().strip()

    markers = []

    # Coba parse JSON
    try:
        data = json.loads(content)
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    ts = item.get("time", item.get("timestamp", ""))
                    label = item.get("label", item.get("name", "manual marker"))
                else:
                    ts = str(item)
                    label = "manual marker"
                if ts:
                    markers.append({
                        "timestamp": ts,
                        "seconds": timestamp_to_seconds(ts),
                        "label": label,
                        "type": "manual"
                    })
            return markers
    except (json.JSONDecodeError, ValueError):
        pass

    # Parse plain text (1 timestamp per line)
    for line in content.split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        # Cari timestamp di line
        ts_match = re.search(r"(\d{1,2}:\d{2}:\d{2}(?:\.\d+)?|\d{1,2}:\d{2}(?:\.\d+)?)", line)
        if ts_match:
            ts = ts_match.group(1)
            # Everything after timestamp = label
            label = line[ts_match.end():].strip(" -:")
            if not label:
                label = "manual marker"
            markers.append({
                "timestamp": ts,
                "seconds": timestamp_to_seconds(ts),
                "label": label,
                "type": "manual"
            })

    return markers


# ── chat spikes ─────────────────────────────────────────────────────────
def load_chat_data(chat_path: str) -> dict:
    """
    Load live chat JSON dan hitung messages per minute (MPM).
    Return: {minute: count, ...}
    """
    path = Path(chat_path)
    if not path.exists():
        print(f"  ⚠️  Chat file tidak ditemukan: {path}")
        return {"messages": [], "mpm": {}, "spikes": []}

    with open(path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            print(f"  ❌ Gagal parse chat JSON")
            return {"messages": [], "mpm": {}, "spikes": []}

    # Format YouTube live chat JSON
    messages = []
    if isinstance(data, list):
        messages = data
    elif isinstance(data, dict):
        messages = data.get("messages", data.get("comments", []))

    # Hitung MPM
    mpm = {}  # minute (int) -> count
    for msg in messages:
        ts = None
        if isinstance(msg, dict):
            ts = msg.get("timestamp", msg.get("time", msg.get("published_at", None)))
        if ts:
            try:
                # Handle Unix timestamp
                if isinstance(ts, (int, float)):
                    minute = int(ts // 60)
                # Handle ISO string
                elif isinstance(ts, str) and ts.replace(".", "").isdigit():
                    minute = int(float(ts) // 60)
                else:
                    # Parse "HH:MM:SS" or similar
                    parts = ts.split(":")
                    if len(parts) >= 2:
                        minute = int(parts[0]) * 60 + int(parts[1])
                    else:
                        continue
                mpm[minute] = mpm.get(minute, 0) + 1
            except (ValueError, TypeError):
                continue

    # Hitung average MPM
    if mpm:
        avg_mpm = sum(mpm.values()) / len(mpm)
    else:
        avg_mpm = 0

    # Deteksi spikes
    spikes = []
    for minute, count in mpm.items():
        if count >= MIN_SPIKE_ABSOLUTE and count > avg_mpm * SPIKE_THRESHOLD:
            spikes.append({
                "minute": minute,
                "timestamp": seconds_to_timestamp(minute * 60),
                "count": count,
                "multiplier": round(count / max(avg_mpm, 1), 1),
                "type": "chat_spike"
            })

    spikes.sort(key=lambda s: s["count"], reverse=True)

    return {
        "messages": messages,
        "mpm": mpm,
        "spikes": spikes,
        "avg_mpm": avg_mpm,
        "total_messages": len(messages),
    }


# ── transkrip cutter ────────────────────────────────────────────────────
def cut_transcript(vtt_path: str, chunks: list) -> dict:
    """
    Potong transkrip VTT berdasarkan chunks.
    Return: {chunk_id: text, ...}
    """
    path = Path(vtt_path)
    if not path.exists():
        print(f"  ⚠️  Transkrip tidak ditemukan: {path}")
        return {}

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Parse VTT
    content = re.sub(r"^WEBVTT.*?\n\n", "", content, flags=re.DOTALL)
    blocks = re.split(r"\n\n+", content.strip())

    segments = []
    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) < 2:
            continue

        ts_line = None
        for i, line in enumerate(lines):
            if "-->" in line:
                ts_line = i
                break

        if ts_line is None:
            continue

        ts_match = re.search(
            r"(\d{1,2}:\d{2}:\d{2}\.\d{3})\s*-->\s*(\d{1,2}:\d{2}:\d{2}\.\d{3})",
            lines[ts_line]
        )
        if not ts_match:
            continue

        start_sec = timestamp_to_seconds(ts_match.group(1))
        end_sec = timestamp_to_seconds(ts_match.group(2))
        text = " ".join(l.strip() for l in lines[ts_line + 1:] if l.strip())

        if text:
            segments.append({"start_sec": start_sec, "end_sec": end_sec, "text": text})

    # Potong per chunk
    chunk_texts = {}
    for chunk in chunks:
        chunk_id = chunk.get("chunk_id", "unknown")
        start = chunk.get("start_sec", 0)
        end = chunk.get("end_sec", 0)

        texts = []
        for seg in segments:
            if seg["start_sec"] >= start and seg["end_sec"] <= end:
                texts.append(seg["text"])
            elif seg["start_sec"] < end and seg["end_sec"] > start:
                # Overlap
                texts.append(seg["text"])

        chunk_texts[chunk_id] = " ".join(texts)

    return chunk_texts


# ── main ────────────────────────────────────────────────────────────────
def run_sync(video_dir: str, markers_file: str = None, chat_file: str = None):
    """
    Main: load semua data → sinkronisasi → output JSON.
    """
    video_path = Path(video_dir)
    if not video_path.is_dir():
        print(f"❌ Directory tidak ditemukan: {video_path}")
        sys.exit(1)

    print("=" * 60)
    print("LOG SYNCHRONIZER — Data Processing & Sync")
    print("=" * 60)
    print(f"  📂 Video dir: {video_path}")
    print()

    # Step 1: Load markers
    print("STEP 1: Loading markers...")
    if markers_file:
        markers = load_markers(markers_file)
    else:
        # Cari markers.txt di folder
        markers_path = video_path / "markers.txt"
        markers = load_markers(str(markers_path)) if markers_path.exists() else []

    print(f"  📌 Markers found: {len(markers)}")
    for m in markers[:5]:
        print(f"    → {m['timestamp']} — {m['label']}")
    print()

    # Step 2: Load chat data
    print("STEP 2: Loading chat data...")
    if chat_file:
        chat_data = load_chat_data(chat_file)
    else:
        # Cari live_chat.json di folder
        chat_path = video_path / "live_chat.json"
        chat_data = load_chat_data(str(chat_path)) if chat_path.exists() else {"messages": [], "mpm": {}, "spikes": [], "avg_mpm": 0, "total_messages": 0}

    print(f"  💬 Total messages: {chat_data.get('total_messages', 0)}")
    print(f"  📊 Avg MPM: {chat_data.get('avg_mpm', 0):.1f}")
    print(f"  🔥 Chat spikes: {len(chat_data.get('spikes', []))}")
    for s in chat_data.get("spikes", [])[:5]:
        print(f"    → {s['timestamp']} — {s['count']} msg/min ({s['multiplier']}x avg)")
    print()

    # Step 3: Load chunks metadata
    print("STEP 3: Loading chunks...")
    chunks_file = video_path / "chunks" / "chunks.json"
    chunks = []
    if chunks_file.exists():
        with open(chunks_file, "r", encoding="utf-8") as f:
            chunks = json.load(f)
    print(f"  📦 Chunks: {len(chunks)}")
    print()

    # Step 4: Cut transkrip per chunk
    print("STEP 4: Cutting transkrip per chunk...")
    vtt_files = list(video_path.glob("*.vtt"))
    chunk_texts = {}

    if vtt_files and chunks:
        # Pakai VTT pertama (biasanya Indonesia)
        vtt_path = str(vtt_files[0])
        print(f"  📄 Transkrip: {vtt_files[0].name}")
        chunk_texts = cut_transcript(vtt_path, chunks)
        print(f"  ✅ Cut {len(chunk_texts)} chunks")
    else:
        print(f"  ⚠️  No VTT files found")
    print()

    # Step 5: Compile sync data
    print("STEP 5: Compiling sync data...")

    sync_data = {
        "video_dir": str(video_path),
        "synced_at": datetime.now().isoformat(),
        "markers": markers,
        "chat_summary": {
            "total_messages": chat_data.get("total_messages", 0),
            "avg_mpm": chat_data.get("avg_mpm", 0),
            "spikes": chat_data.get("spikes", []),
        },
        "chunks": []
    }

    for chunk in chunks:
        chunk_id = chunk.get("chunk_id", "unknown")
        chunk_entry = {
            "chunk_id": chunk_id,
            "start_time": chunk.get("start_time", "?"),
            "end_time": chunk.get("end_time", "?"),
            "start_sec": chunk.get("start_sec", 0),
            "end_sec": chunk.get("end_sec", 0),
            "duration_sec": chunk.get("duration_sec", 0),
            "word_count": chunk.get("word_count", 0),
            "summary": chunk.get("summary", ""),
            "transcript": chunk_texts.get(chunk_id, ""),
            "markers_in_chunk": [
                m for m in markers
                if chunk.get("start_sec", 0) <= m.get("seconds", 0) <= chunk.get("end_sec", 0)
            ],
            "chat_spikes_in_chunk": [
                s for s in chat_data.get("spikes", [])
                if chunk.get("start_sec", 0) <= s.get("minute", 0) * 60 <= chunk.get("end_sec", 0)
            ],
        }
        sync_data["chunks"].append(chunk_entry)

    # Simpan sync_data.json
    sync_path = video_path / "sync_data.json"
    with open(sync_path, "w", encoding="utf-8") as f:
        json.dump(sync_data, f, ensure_ascii=False, indent=2)

    # Ringkasan
    print()
    print("=" * 60)
    print("✅ SYNC COMPLETE")
    print("=" * 60)
    print(f"  📂 Output: {sync_path}")
    print(f"  📌 Markers: {len(markers)}")
    print(f"  💬 Chat messages: {chat_data.get('total_messages', 0)}")
    print(f"  🔥 Chat spikes: {len(chat_data.get('spikes', []))}")
    print(f"  📦 Chunks: {len(chunks)}")
    print(f"  📄 Transkrip chunks: {len(chunk_texts)}")

    return sync_path


def main():
    parser = argparse.ArgumentParser(
        description="Log Synchronizer: proses & sinkronisasi data mentah"
    )
    parser.add_argument(
        "--video-dir", "-d",
        required=True,
        help="Path ke folder video (raw_footages/<video_name>)"
    )
    parser.add_argument(
        "--markers", "-m",
        default=None,
        help="Path ke markers.txt (default: <video_dir>/markers.txt)"
    )
    parser.add_argument(
        "--chat", "-c",
        default=None,
        help="Path ke live_chat.json (default: <video_dir>/live_chat.json)"
    )

    args = parser.parse_args()
    run_sync(args.video_dir, args.markers, args.chat)


if __name__ == "__main__":
    main()
