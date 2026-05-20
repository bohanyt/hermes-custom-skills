"""
DATA MINER: Ekstrak quote & timestamp dari chunks
Simpan di hermes_skills/data_miner.py

Baca production_brief.json + chunks, ekstrak:
- Quote terbaik per konten
- Timestamp penting
- Momen menarik (reaksi, highlight)

Cara pakai:
  python data_miner.py "path/to/chunks/production_brief.json"

Output:
  <chunks_folder>/
    └── data_mining.json        ← quotes + timestamps per konten
"""

import argparse
import json
import re
import sys
from pathlib import Path

# ── import config ──────────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent))
from config_api import call_llm

# ── config ─────────────────────────────────────────────────────────────
PROFILE = "secondary"

DATA_MINER_SYSTEM_PROMPT = """Kamu adalah "The Data Miner", agen ekstraksi data dari transkrip livestream.

Tugasmu: baca transkrip chunk dan ekstrak data PENTING untuk produksi video.

Input:
- Daftar chunk dengan teks transkrip
- Production brief (jenis video yang akan dibuat)

Yang harus kamu ekstrak per konten:
1. QUOTE TERBAIK — Kalimat yang catchy, lucu, atau mengena (max 5 per konten)
2. TIMESTAMP PENTING — Momen yang harus di-include (dengan alasan)
3. MOMEN MENARIK — Reaksi, letupan emosi, atau momen viral (max 3 per konten)

OUTPUT FORMAT (WAJIB JSON MURNI):
{
  "konten_id": 1,
  "jenis": "Video Essay / Shorts / dll",
  "quotes": [
    {
      "quote": "Kalimat yang catchy/lucu/mengena",
      "timestamp": "00:05:23",
      "chunk_id": "chunk_003",
      "alasan": "Kenapa quote ini bagus (lucu, relatable, dll)"
    }
  ],
  "timestamps_penting": [
    {
      "timestamp": "00:07:15",
      "chunk_id": "chunk_004",
      "deskripsi": "Deskripsi momen",
      "alasan": "Kenapa momen ini penting"
    }
  ],
  "momen_menarik": [
    {
      "timestamp": "00:12:30",
      "chunk_id": "chunk_006",
      "deskripsi": "Deskripsi momen menarik",
      "tipe": "reaksi / lucu / epic / emotional"
    }
  ]
}

PENTING:
- Output HARUS JSON valid, tanpa markdown code block
- Semua timestamp dalam format HH:MM:SS atau MM:SS
- Prioritaskan quote yang pendek dan impactful
- Kalau gak ada quote bagus, kosongkan array"""

DATA_MINER_USER_TEMPLATE = """Ekstrak data dari transkrip berikut untuk produksi video:

**Production Brief:**
[[brief]]

**Transkrip per Chunk:**
[[chunks_text]]

Ekstrak quotes, timestamps penting, dan momen menarik dalam format JSON."""


def load_chunks(chunks_dir: Path) -> dict:
    """Load semua chunk text files."""
    chunks = {}
    chunks_json = chunks_dir / "chunks.json"

    if chunks_json.exists():
        with open(chunks_json, "r", encoding="utf-8") as f:
            meta = json.load(f)
        for item in meta:
            chunk_id = item["chunk_id"]
            txt_file = chunks_dir / item.get("text_file", f"{chunk_id}.txt")
            if txt_file.exists():
                with open(txt_file, "r", encoding="utf-8") as f:
                    text = f.read()
                # Skip header
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
                chunks[chunk_id] = "\n".join(content_lines).strip()

    return chunks


def run_data_miner(brief_path: str):
    """
    Baca production_brief.json + chunks → ekstrak data → data_mining.json
    """
    brief_file = Path(brief_path)
    if not brief_file.exists():
        print(f"❌ File tidak ditemukan: {brief_file}")
        sys.exit(1)

    chunks_dir = brief_file.parent

    # Load brief
    with open(brief_file, "r", encoding="utf-8") as f:
        brief = json.load(f)

    # Load chunks text
    chunks = load_chunks(chunks_dir)

    print("=" * 60)
    print("DATA MINER — Quote & Timestamp Extraction")
    print("=" * 60)
    print(f"  📂 Brief: {brief_file}")
    print(f"  📊 Chunks loaded: {len(chunks)}")
    print()

    potensi = brief.get("potensi_konten", [])
    all_mining = []

    for konten in potensi:
        konten_id = konten.get("id", 0)
        jenis = konten.get("jenis", "Unknown")
        chunks_dipake = konten.get("chunks_dipake", [])

        print(f"[{konten_id}/{len(potensi)}] Mining: {jenis}")
        print(f"  Chunks: {', '.join(chunks_dipake)}")

        # Kumpulkan teks dari chunks yang dipake
        konten_text = ""
        for chunk_id in chunks_dipake:
            if chunk_id in chunks:
                konten_text += f"\n--- {chunk_id} ---\n{chunks[chunk_id]}\n"

        if not konten_text.strip():
            print(f"  ⚠️  No text found for these chunks")
            all_mining.append({
                "konten_id": konten_id,
                "jenis": jenis,
                "quotes": [],
                "timestamps_penting": [],
                "momen_menarik": [],
                "error": "No chunk text found"
            })
            continue

        # Truncate kalau terlalu panjang (max ~8000 chars)
        if len(konten_text) > 15000:
            konten_text = konten_text[:15000] + "\n... (truncated)"

        # Brief info untuk prompt
        brief_info = f"Jenis: {jenis}\nChunks: {', '.join(chunks_dipake)}"

        # Call LLM
        messages = [
            {"role": "system", "content": DATA_MINER_SYSTEM_PROMPT},
            {"role": "user", "content": DATA_MINER_USER_TEMPLATE
                .replace("[[brief]]", brief_info)
                .replace("[[chunks_text]]", konten_text)
            }
        ]

        try:
            response = call_llm(
                profile=PROFILE,
                messages=messages,
                max_tokens=2000,
                temperature=0.3
            )
        except Exception as e:
            print(f"  ❌ Error: {e}")
            all_mining.append({
                "konten_id": konten_id,
                "jenis": jenis,
                "quotes": [],
                "timestamps_penting": [],
                "momen_menarik": [],
                "error": str(e)
            })
            continue

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
            mining = json.loads(response_clean)
        except json.JSONDecodeError:
            print(f"  ⚠️  JSON parse failed, saving raw")
            mining = {"raw_response": response, "konten_id": konten_id, "jenis": jenis}

        all_mining.append(mining)
        n_quotes = len(mining.get("quotes", []))
        n_moments = len(mining.get("momen_menarik", []))
        print(f"  ✅ Found {n_quotes} quotes, {n_moments} moments")

    # Simpan data_mining.json
    mining_path = chunks_dir / "data_mining.json"
    with open(mining_path, "w", encoding="utf-8") as f:
        json.dump(all_mining, f, ensure_ascii=False, indent=2)

    # Ringkasan
    print()
    print("=" * 60)
    print("✅ DATA MINING COMPLETE")
    print("=" * 60)
    total_quotes = sum(len(m.get("quotes", [])) for m in all_mining)
    total_moments = sum(len(m.get("momen_menarik", [])) for m in all_mining)
    print(f"  📊 Total quotes: {total_quotes}")
    print(f"  🎬 Total moments: {total_moments}")
    print(f"  📝 Saved: {mining_path}")
    print()

    return all_mining


def main():
    parser = argparse.ArgumentParser(
        description="Data Miner: ekstrak quote & timestamp dari chunks"
    )
    parser.add_argument("brief_path", help="Path ke production_brief.json")
    args = parser.parse_args()
    run_data_miner(args.brief_path)


if __name__ == "__main__":
    main()
