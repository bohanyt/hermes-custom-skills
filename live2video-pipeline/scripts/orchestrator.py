"""
ORCHESTRATOR: Analisis chunks → Production Brief
Simpan di hermes_skills/orchestrator.py

Baca all_summaries.json, detect niche/game type,
pilih content type yang cocok dari content_types.json,
tentuin potensi konten yang bisa dibuat.

Cara pakai:
  python orchestrator.py "path/to/chunks/all_summaries.json"
  python orchestrator.py "path/to/chunks/all_summaries.json" --title "Judul Video"

Output:
  <chunks_folder>/
    └── production_brief.json   ← rencana produksi video
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

# ── content types ──────────────────────────────────────────────────────
CONTENT_TYPES_FILE = Path(__file__).parent / "content_types.json"

def load_content_types() -> dict:
    """Load content_types.json."""
    if CONTENT_TYPES_FILE.exists():
        with open(CONTENT_TYPES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"content_types": {}}

def detect_niche(summaries: list, metadata: dict) -> dict:
    """
    Detect niche/game type dari summaries + metadata.
    Return: {niche_key, label, confidence, matched_keywords}
    """
    content_types = load_content_types()
    types_data = content_types.get("content_types", {})

    # Gabung semua teks untuk analysis
    all_text = " ".join([
        metadata.get("title", ""),
        metadata.get("channel", ""),
    ] + [s.get("summary", "") for s in summaries])

    all_text_lower = all_text.lower()

    # Score per niche
    scores = {}
    for niche_key, niche_data in types_data.items():
        if niche_key == "unknown":
            continue
        keywords = niche_data.get("keywords", [])
        matched = [kw for kw in keywords if kw.lower() in all_text_lower]
        if matched:
            scores[niche_key] = {
                "label": niche_data.get("label", niche_key),
                "matched_keywords": matched,
                "score": len(matched),
                "content_types": niche_data.get("content_types", [])
            }

    if not scores:
        return {
            "niche_key": "unknown",
            "label": "Unknown / General",
            "confidence": 0,
            "matched_keywords": [],
            "content_types": types_data.get("unknown", {}).get("content_types", [])
        }

    # Pick highest score
    best_niche = max(scores.items(), key=lambda x: x[1]["score"])
    return {
        "niche_key": best_niche[0],
        "label": best_niche[1]["label"],
        "confidence": min(best_niche[1]["score"] / 5, 1.0),  # Normalize 0-1
        "matched_keywords": best_niche[1]["matched_keywords"],
        "content_types": best_niche[1]["content_types"]
    }

ORCHESTRATOR_SYSTEM_PROMPT = """Kamu adalah "The Orchestrator", Executive Producer dari sebuah channel YouTube.

Tugasmu: analisis summary dari setiap chunk livestream dan tentukan RENCANA PRODUKSI.

Input yang kamu terima:
- all_summaries.json: array of {chunk_id, start_time, end_time, duration_sec, summary}
- metadata.json: info video (title, channel, duration, url)
- detected_niche: hasil detection niche/game type dari keywords
- content_types: daftar jenis video yang cocok untuk niche ini (dari content_types.json)

ATURAN ANALISIS:
1. Baca semua summary secara keseluruhan
2. Identifikasi TOPIK UTAMA dari livestream ini
3. Cari MOMEN MENARIK yang bisa dijadikan konten terpisah
4. Gunakan CONTENT_TYPES yang diberikan sebagai panduan — pilih jenis video yang PALING COCOK untuk niche ini
5. Tentukan POTENSI OUTPUT (bisa lebih dari 1 video dari 1 livestream)

CONTENT TYPES YANG TERSEDIA (sesuai niche):
[[content_types_guide]]

FORMAT OUTPUT (WAJIB JSON MURNI):
{
  "analisis_keseluruhan": {
    "topik_utama": "Deskripsi topik utama livestream",
    "vibe_energi": "Deskripsi vibe/energi (misal: chaotic, santai, try-hard)",
    "total_durasi": "HH:MM:SS",
    "jumlah_chunks": 10,
    "detected_niche": "gacha_game / fps_game / just_chatting / coding_tech / creative_art / music / unknown"
  },
  "potensi_konten": [
    {
      "id": 1,
      "jenis": "Raw Clip - Reaction / Shorts / Storytime / Video Essay / Tutorial / Lore & Story Retelling / Raw Clip - Reaction",
      "judul_saran": "Judul yang clickbait tapi relevan",
      "hook": "Hook pembuka yang menarik (1-2 kalimat)",
      "chunks_dipake": ["chunk_001", "chunk_002"],
      "start_time": "00:00:00",
      "end_time": "00:05:30",
      "durasi_estimasi": "3-5 menit",
      "vibe": "Deskripsi vibe konten ini",
      "alasan": "Kenapa chunk ini cocok untuk jenis konten ini",
      "keyword_riset": ["keyword1", "keyword2"]
    }
  ],
  "rekomendasi_tambahan": [
    "Saran tambahan untuk produksi (misal: perlu B-roll, perlu voiceover, dll)"
  ]
}

PENTING:
- Output HARUS JSON valid, tanpa markdown code block
- Pilih JENIS VIDEO dari CONTENT_TYPES yang diberikan — jangan asal milih
- Setiap jenis video punya karakteristik berbeda, sesuaikan dengan momen di livestream
- Minimal rekomendasikan 1 potensi konten
- Maksimal 5 potensi konten per livestream
- Prioritaskan kuantitas konten (satu livestream = banyak video)"""

ORCHESTRATOR_USER_TEMPLATE = """Analisis livestream ini dan buat rencana produksi:

**Metadata Video:**
[[metadata]]

**Detected Niche:** [[detected_niche]]

**Content Types yang Cocok untuk Niche Ini:**
[[content_types_guide]]

**Summary per Chunk:**
[[summaries]]

Buat production brief dalam format JSON sesuai instruksi."""


def load_metadata(chunks_dir: Path) -> dict:
    """Coba load metadata.json dari folder yang sama dengan chunks."""
    # chunks_dir = raw_footages/<video>/chunks/
    # metadata.json = raw_footages/<video>/metadata.json
    meta_path = chunks_dir.parent / "metadata.json"
    if meta_path.exists():
        with open(meta_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def run_orchestrator(chunks_dir: str, title: str = None):
    """
    Baca all_summaries.json + metadata.json -> analisis -> production_brief.json
    """
    chunks_path = Path(chunks_dir)
    if not chunks_path.is_dir():
        print(f"❌ Directory tidak ditemukan: {chunks_path}")
        sys.exit(1)

    summaries_file = chunks_path / "all_summaries.json"
    if not summaries_file.exists():
        print(f"❌ File tidak ditemukan: {summaries_file}")
        print(f"   Jalankan chunk_summarizer.py dulu.")
        sys.exit(1)

    # Load summaries
    with open(summaries_file, "r", encoding="utf-8") as f:
        summaries = json.load(f)

    # Load metadata
    metadata = load_metadata(chunks_path)

    print("=" * 60)
    print("ORCHESTRATOR — Production Brief Generator")
    print("=" * 60)
    print(f"  📂 Chunks dir: {chunks_path}")
    print(f"  📊 Total chunks: {len(summaries)}")
    if metadata:
        print(f"  📹 Title: {metadata.get('title', '?')}")
        print(f"  👤 Channel: {metadata.get('channel', '?')}")
        print(f"  ⏱️  Duration: {metadata.get('duration', '?')}")
        print(f"  🔗 URL: {metadata.get('url', '?')}")
    print()

    # Format summaries untuk prompt
    summaries_text = ""
    for s in summaries:
        summaries_text += f"- {s['chunk_id']} ({s['start_time']} → {s['end_time']}, {s.get('duration_sec', '?')}s): {s['summary']}\n"

    # Format metadata untuk prompt
    if metadata:
        metadata_text = f"""
Title: {metadata.get('title', 'N/A')}
Channel: {metadata.get('channel', 'N/A')}
Duration: {metadata.get('duration', 'N/A')}
URL: {metadata.get('url', 'N/A')}
Downloaded: {metadata.get('downloaded_at', 'N/A')}
"""
    else:
        metadata_text = "Metadata tidak tersedia."

    # Detect niche dari summaries + metadata
    print("[Orchestrator] 🔍 Detecting niche...")
    niche_result = detect_niche(summaries, metadata)
    print(f"  🎯 Detected: {niche_result['label']} (confidence: {niche_result['confidence']:.0%})")
    if niche_result.get("matched_keywords"):
        print(f"  🔑 Keywords: {', '.join(niche_result['matched_keywords'][:10])}")
    print()

    # Format content types guide
    content_types_guide = ""
    for ct in niche_result.get("content_types", []):
        content_types_guide += f"\n--- {ct['jenis']} ---\n"
        content_types_guide += f"  Cocok untuk: {', '.join(ct.get('cocok_untuk', []))}\n"
        content_types_guide += f"  Hook pattern: {ct.get('hook_pattern', '?')}\n"
        content_types_guide += f"  Durasi ideal: {ct.get('durasi_ideal', '?')}\n"
        content_types_guide += f"  Editing: {ct.get('editing_style', '?')}\n"

    if not content_types_guide:
        content_types_guide = "Tidak ada content type spesifik. Gunakan umum: Raw Clip, Video Essay, Shorts, Storytime, Tutorial."

    # Format detected niche text
    detected_niche_text = f"{niche_result['label']} (key: {niche_result['niche_key']}, confidence: {niche_result['confidence']:.0%})"

    # Call LLM
    print("[Orchestrator] 🧠 Analisis livestream...")
    print()

    messages = [
        {"role": "system", "content": ORCHESTRATOR_SYSTEM_PROMPT.replace("[[content_types_guide]]", content_types_guide)},
        {"role": "user", "content": ORCHESTRATOR_USER_TEMPLATE
            .replace("[[metadata]]", metadata_text)
            .replace("[[summaries]]", summaries_text)
            .replace("[[detected_niche]]", detected_niche_text)
            .replace("[[content_types_guide]]", content_types_guide)
        }
    ]

    try:
        response = call_llm(
            profile=PROFILE,
            messages=messages,
            max_tokens=4000,
            temperature=0.4
        )
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

    # Parse JSON response
    # Hapus markdown code block kalau ada
    response_clean = response.strip()
    if response_clean.startswith("```json"):
        response_clean = response_clean[7:]
    if response_clean.startswith("```"):
        response_clean = response_clean[3:]
    if response_clean.endswith("```"):
        response_clean = response_clean[:-3]
    response_clean = response_clean.strip()

    try:
        brief = json.loads(response_clean)
    except json.JSONDecodeError as e:
        print(f"⚠️  Warning: Response bukan JSON valid: {e}")
        print(f"   Raw response:\n{response}")
        # Simpan raw response aja
        brief = {"raw_response": response}

    # Simpan production_brief.json
    brief_path = chunks_path / "production_brief.json"
    with open(brief_path, "w", encoding="utf-8") as f:
        json.dump(brief, f, ensure_ascii=False, indent=2)

    # Ringkasan
    print()
    print("=" * 60)
    print("✅ PRODUCTION BRIEF")
    print("=" * 60)

    if "analisis_keseluruhan" in brief:
        analisis = brief["analisis_keseluruhan"]
        print(f"\n📊 Analisis:")
        print(f"  Topik: {analisis.get('topik_utama', '?')}")
        print(f"  Vibe: {analisis.get('vibe_energi', '?')}")
        print(f"  Durasi: {analisis.get('total_durasi', '?')}")
        print(f"  Chunks: {analisis.get('jumlah_chunks', '?')}")

    if "potensi_konten" in brief:
        print(f"\n🎬 Potensi Konten ({len(brief['potensi_konten'])} video):")
        for i, konten in enumerate(brief["potensi_konten"]):
            print(f"\n  [{i+1}] {konten.get('jenis', '?')}")
            print(f"      Judul: {konten.get('judul_saran', '?')}")
            print(f"      Hook: {konten.get('hook', '?')}")
            print(f"      Chunks: {', '.join(konten.get('chunks_dipake', []))}")
            print(f"      Waktu: {konten.get('start_time', '?')} → {konten.get('end_time', '?')}")
            print(f"      Durasi estimasi: {konten.get('durasi_estimasi', '?')}")
            print(f"      Alasan: {konten.get('alasan', '?')}")
            if konten.get('keyword_riset'):
                print(f"      Keyword riset: {', '.join(konten['keyword_riset'])}")

    if "rekomendasi_tambahan" in brief:
        print(f"\n💡 Rekomendasi:")
        for rec in brief["rekomendasi_tambahan"]:
            print(f"  - {rec}")

    print(f"\n📝 Saved: {brief_path}")
    print()

    return brief


def main():
    parser = argparse.ArgumentParser(
        description="Orchestrator: analisis chunks → production brief"
    )
    parser.add_argument("chunks_dir", help="Path ke folder chunks/")
    parser.add_argument(
        "--title", "-t",
        default=None,
        help="Override judul video"
    )

    args = parser.parse_args()
    run_orchestrator(args.chunks_dir, args.title)


if __name__ == "__main__":
    main()
