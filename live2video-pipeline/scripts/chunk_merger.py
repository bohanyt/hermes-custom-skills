"""
CHUNK MERGER: Merge chunk yang topiknya sama
Simpan di hermes_skills/chunk_merger.py

Baca chunks.json + chunk text files, kirim ke LLM untuk deteksi
pergantian topik. Merge chunk yang topiknya sama.

Cara pakai:
  python chunk_merger.py "path/to/chunks/chunks.json"
  python chunk_merger.py "path/to/chunks/chunks.json" --max-duration 300

Output:
  <chunks_folder>/merged/
    ├── chunks.json              ← chunks yang sudah di-merge
    ├── chunk_001.txt            ← teks chunk 1 (merged)
    ├── chunk_002.txt            ← teks chunk 2 (merged)
    └── merge_log.json           ← log merge
"""

import argparse
import json
import sys
import time
from pathlib import Path

# ── import config ──────────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent))
from config_api import call_llm

# ── config ─────────────────────────────────────────────────────────────
PROFILE = "secondary"  # pakai model yang lebih murah
MAX_DURATION_DEFAULT = 300  # max 5 menit per merged chunk
MIN_DURATION_DEFAULT = 60   # min 1 menit per merged chunk

MERGE_SYSTEM_PROMPT = """Kamu adalah "Chunk Merger", alat untuk menggabungkan potongan transkrip livestream yang topiknya sama.

Tugasmu: baca daftar chunk summary dan tentukan mana yang harus di-merge.

ATURAN:
1. Baca summary tiap chunk secara berurutan
2. Jika chunk A dan chunk B membahas TOPIK YANG SAMA → MERGE
3. Jika chunk A dan chunk B membahas TOPIK BERBEDA → PISAH
4. Jangan merge kalau durasi totalnya akan melebihi {max_duration} detik
5. Jangan merge kalau ada jeda topik yang jelas (misal: dari "gacha" ke "baca chat santai")

OUTPUT FORMAT (WAJIB JSON MURNI):
[
  {
    "merged_chunk_id": "chunk_001",
    "source_chunks": ["chunk_001", "chunk_002"],
    "start_time": "00:00:00",
    "end_time": "00:05:30",
    "duration_sec": 330,
    "topik_utama": "Deskripsi topik utama chunk ini",
    "alasan_merge": "Kenapa chunk ini di-merge"
  },
  {
    "merged_chunk_id": "chunk_002",
    "source_chunks": ["chunk_003"],
    "start_time": "00:05:30",
    "end_time": "00:08:00",
    "duration_sec": 150,
    "topik_utama": "Deskripsi topik utama chunk ini",
    "alasan_merge": "Chunk ini topiknya berbeda dari sebelumnya, jadi tidak di-merge"
  }
]

PENTING:
- Output HARUS JSON valid, tanpa markdown code block
- Setiap chunk harus masuk ke tepat 1 merged chunk
- Prioritaskan merge yang masuk akal (topik sama, durasi wajar)
- Jangan terlalu agresif merge — lebih baik sedikit chunk tapi topiknya jelas"""

MERGE_USER_TEMPLATE = """Tentukan mana chunk yang harus di-merge berdasarkan summary berikut:

**Max durasi per merged chunk:** {max_duration} detik

**Chunks:**
{chunks_summary}

Buat merge plan dalam format JSON."""


def load_chunks(chunks_json_path: str) -> list:
    """Load chunks.json."""
    path = Path(chunks_json_path)
    if not path.exists():
        print(f"❌ File tidak ditemukan: {path}")
        sys.exit(1)

    with open(path, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    return chunks


def load_chunk_text(chunks_dir: Path, chunk_id: str) -> str:
    """Load teks chunk."""
    txt_file = chunks_dir / f"{chunk_id}.txt"
    if not txt_file.exists():
        # Cari dari chunks.json
        return ""

    with open(txt_file, "r", encoding="utf-8") as f:
        text = f.read()

    # Skip header lines
    lines = text.split("\n")
    content_lines = []
    skip = True
    for line in lines:
        if skip:
            if line.startswith("#"):
                continue
            elif line.strip() == "":
                continue
            else:
                skip = False
                content_lines.append(line)
        else:
            content_lines.append(line)

    return "\n".join(content_lines).strip()


def run_merge(chunks_json_path: str, max_duration: int = MAX_DURATION_DEFAULT):
    """
    Baca chunks → kirim ke LLM → merge → simpan ke merged/
    """
    chunks_file = Path(chunks_json_path)
    chunks_dir = chunks_file.parent

    # Load chunks
    chunks = load_chunks(chunks_json_path)

    print("=" * 60)
    print("CHUNK MERGER — Merge chunks dengan topik sama")
    print("=" * 60)
    print(f"  📂 Chunks: {chunks_file}")
    print(f"  📊 Total chunks: {len(chunks)}")
    print(f"  ⏱️  Max duration per merged chunk: {max_duration}s ({max_duration/60:.0f} min)")
    print(f"  🔌 Model: {PROFILE}")
    print()

    # Prepare chunks summary untuk prompt
    chunks_summary = ""
    for c in chunks:
        chunk_id = c.get("chunk_id", "?")
        start = c.get("start_time", "?")
        end = c.get("end_time", "?")
        duration = c.get("duration_sec", 0)
        summary = c.get("summary", "No summary")

        chunks_summary += f"\n--- {chunk_id} ({start} → {end}, {duration}s) ---\n"
        chunks_summary += f"{summary}\n"

    # Truncate kalau terlalu panjang (max ~15000 chars)
    if len(chunks_summary) > 15000:
        chunks_summary = chunks_summary[:15000] + "\n... (truncated, terlalu banyak chunks)"
        print(f"  ⚠️  Summary truncated (terlalu panjang)")

    # Call LLM
    print("[Merger] 🧠 Analisis topik dan merge plan...")
    print()

    messages = [
        {"role": "system", "content": MERGE_SYSTEM_PROMPT.replace("{max_duration}", str(max_duration))},
        {"role": "user", "content": MERGE_USER_TEMPLATE.replace("{max_duration}", str(max_duration)).replace("{chunks_summary}", chunks_summary)}
    ]

    try:
        response = call_llm(
            profile=PROFILE,
            messages=messages,
            max_tokens=4000,
            temperature=0.3
        )
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

    # Parse JSON
    response_clean = response.strip()
    if response_clean.startswith("```json"):
        response_clean = response_clean[7:]
    if response_clean.startswith("```"):
        response_clean = response_clean[3:]
    if response_clean.endswith("```"):
        response_clean = response_clean[:-3]
    response_clean = response_clean.strip()

    try:
        merge_plan = json.loads(response_clean)
    except jsonDecodeError as e:
        print(f"⚠️  JSON parse failed: {e}")
        print(f"   Raw response:\n{response[:500]}")
        sys.exit(1)

    print(f"  📊 Merge plan: {len(merge_plan)} merged chunks dari {len(chunks)} original chunks")
    print()

    # Create merged chunks
    merged_dir = chunks_dir / "merged"
    merged_dir.mkdir(parents=True, exist_ok=True)

    merged_chunks = []
    merge_log = []

    for merged in merge_plan:
        merged_id = merged.get("merged_chunk_id", f"chunk_{len(merged_chunks)+1:03d}")
        source_chunks = merged.get("source_chunks", [])
        start_time = merged.get("start_time", "?")
        end_time = merged.get("end_time", "?")
        duration = merged.get("duration_sec", 0)
        topik = merged.get("topik_utama", "?")
        alasan = merged.get("alasan_merge", "?")

        # Gabung teks dari source chunks
        merged_text = ""
        for src_id in source_chunks:
            text = load_chunk_text(chunks_dir, src_id)
            if text:
                merged_text += f"\n{text}\n"

        # Simpan merged text
        merged_txt_path = merged_dir / f"{merged_id}.txt"
        with open(merged_txt_path, "w", encoding="utf-8") as f:
            f.write(f"# {merged_id} (merged)\n")
            f.write(f"# {start_time} → {end_time} ({duration}s)\n")
            f.write(f"# Topik: {topik}\n")
            f.write(f"# Source: {', '.join(source_chunks)}\n")
            f.write("#" + "=" * 58 + "\n\n")
            f.write(merged_text.strip())

        merged_entry = {
            "chunk_id": merged_id,
            "start_time": start_time,
            "end_time": end_time,
            "start_sec": 0,  # Will be calculated
            "end_sec": duration,
            "duration_sec": duration,
            "char_count": len(merged_text),
            "word_count": len(merged_text.split()),
            "segment_count": len(source_chunks),
            "text_file": f"{merged_id}.txt",
            "summary": topik,
            "source_chunks": source_chunks,
        }
        merged_chunks.append(merged_entry)

        merge_log.append({
            "merged_id": merged_id,
            "source_chunks": source_chunks,
            "duration_sec": duration,
            "topik": topik,
            "alasan": alasan,
        })

        n_merged = len(source_chunks)
        print(f"  ✅ {merged_id}: {n_merged} chunks → {duration}s — {topik[:60]}")

    # Simpan merged chunks.json
    merged_json_path = merged_dir / "chunks.json"
    with open(merged_json_path, "w", encoding="utf-8") as f:
        json.dump(merged_chunks, f, ensure_ascii=False, indent=2)

    # Simpan merge log
    log_path = merged_dir / "merge_log.json"
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(merge_log, f, ensure_ascii=False, indent=2)

    # Ringkasan
    print()
    print("=" * 60)
    print("✅ MERGE COMPLETE")
    print("=" * 60)
    print(f"  📊 Original: {len(chunks)} chunks")
    print(f"  📊 Merged: {len(merged_chunks)} chunks")
    print(f"  📉 Reduction: {len(chunks) - len(merged_chunks)} chunks di-merge")
    if merged_chunks:
        avg_dur = sum(c["duration_sec"] for c in merged_chunks) / len(merged_chunks)
        print(f"  ⏱️  Avg duration: {avg_dur:.0f}s ({avg_dur/60:.1f} min)")
    print(f"  📂 Output: {merged_dir}")
    print(f"  📝 Log: {log_path}")

    return merged_dir


def main():
    parser = argparse.ArgumentParser(
        description="Chunk Merger: merge chunk yang topiknya sama"
    )
    parser.add_argument("chunks_json", help="Path ke chunks.json")
    parser.add_argument(
        "--max-duration", "-d",
        type=int,
        default=MAX_DURATION_DEFAULT,
        help=f"Max durasi per merged chunk dalam detik (default: {MAX_DURATION_DEFAULT})"
    )

    args = parser.parse_args()
    run_merge(args.chunks_json, args.max_duration)


if __name__ == "__main__":
    main()
