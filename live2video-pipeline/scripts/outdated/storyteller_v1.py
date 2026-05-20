"""
STORYTELLER: Susun narasi & hook untuk video
Simpan di hermes_skills/storyteller.py

Baca production_brief.json + data_mining.json + trend_research.json,
susun kerangka narasi per konten:
- Hook pembuka
- Story flow / alur narasi
- Quote placement
- Call to action

Cara pakai:
  python storyteller.py "path/to/chunks/production_brief.json"

Output:
  <chunks_folder>/
    └── story_brief.json       ← narasi + hook per konten
"""

import argparse
import json
import sys
from pathlib import Path

# ── import config ──────────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent))
from config_api import call_llm

# ── config ─────────────────────────────────────────────────────────────
PROFILE = "secondary"

STORYTELLER_SYSTEM_PROMPT = """Kamu adalah "The Storyteller", penulis skrip dan narasi untuk video YouTube.

Tugasmu: buat KERANGKA NARASI & HOOK untuk setiap video yang direkomendasikan.

Input:
- Production brief (jenis video, chunks yang dipake, vibe)
- Data mining (quotes, timestamps, momen menarik)
- Trend research (clickbait patterns, top titles)

Yang harus kamu buat per konten:
1. HOOK — Kalimat pembuka yang bikin orang mau nunggu (2-3 kalimat)
2. STORY FLOW — Alur narasi (pembuka → isi → penutup)
3. QUOTE PLACEMENT — Di mana quote tertentu diletakin
4. CALL TO ACTION — Ajakan di akhir video
5. THUMBNAIL TEXT — Teks untuk thumbnail (max 5 kata)

OUTPUT FORMAT (WAJIB JSON MURNI):
{
  "konten_id": 1,
  "jenis": "Video Essay / Shorts / dll",
  "judul_final": "Judul video final (clickbait tapi relevan)",
  "hook": "Kalimat pembuka yang menggugah rasa ingin tahu (2-3 kalimat)",
  "story_flow": [
    {
      "bagian": "Pembuka",
      "timestamp": "00:00:00 - 00:00:30",
      "deskripsi": "Apa yang ditampilkan/dikatakan",
      "catatan": "Catatan untuk editor"
    },
    {
      "bagian": "Rising Action",
      "timestamp": "00:00:30 - 00:02:00",
      "deskripsi": "Apa yang ditampilkan/dikatakan",
      "catatan": "Catatan untuk editor"
    },
    {
      "bagian": "Climax / Highlight",
      "timestamp": "00:02:00 - 00:03:30",
      "deskripsi": "Apa yang ditampilkan/dikatakan",
      "catatan": "Catatan untuk editor"
    },
    {
      "bagian": "Penutup",
      "timestamp": "00:03:30 - 00:04:00",
      "deskripsi": "Apa yang ditampilkan/dikatakan",
      "catatan": "Catatan untuk editor"
    }
  ],
  "quote_placement": [
    {
      "quote": "Quote yang dipake",
      "timestamp_video": "00:01:30",
      "letak": "Di overlay / subtitle /",
      "cara": "Cara menampilkan quote (misal: big text, dengan efek zoom, dll)"
    }
  ],
  "call_to_action": "Kalimat CTA di akhir video (follow, like, comment, dll)",
  "thumbnail_text": "Teks untuk thumbnail (max 5 kata, besar & readable)",
  "thumbnail_description": "Deskripsi visual thumbnail (untuk AI image gen atau desainer)",
  "catatan_editing": [
    "Catatan tambahan untuk editor (efek suara, transisi, dll)"
  ]
}

PENTING:
- Output HARUS JSON valid, tanpa markdown code block
- Hook harus membuat penonton ingin terus nonton
- Story flow harus logis dan engaging
- Quote placement harus timing-nya pas
- Thumbnail text harus besar, readable, dan clickbait"""

STORYTELLER_USER_TEMPLATE = """Buat kerangka narasi & hook untuk video berikut:

**Production Brief:**
[[brief]]

**Data Mining (Quotes & Moments):**
[[data_mining]]

**Trend Research:**
[[trend]]

Buat story brief dalam format JSON sesuai instruksi."""


def load_json_safe(path: Path) -> dict | list:
    """Load JSON file, return empty dict kalau gak ada/error."""
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def run_storyteller(brief_path: str):
    """
    Baca brief + mining + trend → story_brief.json
    """
    brief_file = Path(brief_path)
    if not brief_file.exists():
        print(f"❌ File tidak ditemukan: {brief_file}")
        sys.exit(1)

    chunks_dir = brief_file.parent

    # Load all data
    brief = load_json_safe(brief_file)
    data_mining = load_json_safe(chunks_dir / "data_mining.json")
    trend_research = load_json_safe(chunks_dir / "trend_research.json")

    print("=" * 60)
    print("STORYTELLER — Narrative & Hook Generator")
    print("=" * 60)
    print(f"  📂 Brief: {brief_file}")
    print()

    potensi = brief.get("potensi_konten", [])
    all_stories = []

    for konten in potensi:
        konten_id = konten.get("id", 0)
        jenis = konten.get("jenis", "Unknown")
        judul = konten.get("judul_saran", "Unknown")
        hook_brief = konten.get("hook", "")
        chunks_dipake = konten.get("chunks_dipake", [])
        keyword_riset = konten.get("keyword_riset", [])

        print(f"[{konten_id}/{len(potensi)}] Story: {jenis} — {judul}")

        # Cari data mining untuk konten ini
        mining_for_konten = None
        if isinstance(data_mining, list):
            for m in data_mining:
                if m.get("konten_id") == konten_id or m.get("jenis") == jenis:
                    mining_for_konten = m
                    break

        # Cari trend untuk konten ini (keyword matching)
        trend_for_konten = None
        if isinstance(trend_research, dict):
            per_keyword = trend_research.get("per_keyword", [])
            for t in per_keyword:
                kw = t.get("keyword", "").lower()
                for k in keyword_riset:
                    if k.lower() in kw or kw in k.lower():
                        trend_for_konten = t
                        break

        # Prepare prompt data
        brief_info = json.dumps({
            "jenis": jenis,
            "judul_saran": judul,
            "hook": hook_brief,
            "chunks_dipake": chunks_dipake,
            "keyword_riset": keyword_riset
        }, ensure_ascii=False, indent=2)

        mining_info = json.dumps(mining_for_konten, ensure_ascii=False, indent=2) if mining_for_konten else "No data mining available"
        trend_info = json.dumps(trend_for_konten, ensure_ascii=False, indent=2) if trend_for_konten else "No trend data available"

        # Call LLM
        messages = [
            {"role": "system", "content": STORYTELLER_SYSTEM_PROMPT},
            {"role": "user", "content": STORYTELLER_USER_TEMPLATE
                .replace("[[brief]]", brief_info)
                .replace("[[data_mining]]", mining_info)
                .replace("[[trend]]", trend_info)
            }
        ]

        try:
            response = call_llm(
                profile=PROFILE,
                messages=messages,
                max_tokens=3000,
                temperature=0.5
            )
        except Exception as e:
            print(f"  ❌ Error: {e}")
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
            story = json.loads(response_clean)
        except json.JSONDecodeError:
            print(f"  ⚠️  JSON parse failed, saving raw")
            story = {"raw_response": response, "konten_id": konten_id}

        all_stories.append(story)
        n_flow = len(story.get("story_flow", []))
        n_quotes = len(story.get("quote_placement", []))
        print(f"  ✅ {n_flow} flow sections, {n_quotes} quote placements")

    # Simpan story_brief.json
    story_path = chunks_dir / "story_brief.json"
    with open(story_path, "w", encoding="utf-8") as f:
        json.dump(all_stories, f, ensure_ascii=False, indent=2)

    # Ringkasan
    print()
    print("=" * 60)
    print("✅ STORYTELLING COMPLETE")
    print("=" * 60)
    print(f"  📊 Stories created: {len(all_stories)}")
    print(f"  📝 Saved: {story_path}")
    print()

    for s in all_stories:
        print(f"  🎬 {s.get('judul_final', 'N/A')}")
        if s.get('hook'):
            print(f"     Hook: {s['hook'][:100]}...")
        if s.get('thumbnail_text'):
            print(f"     Thumbnail: {s['thumbnail_text']}")
        print()

    return all_stories


def main():
    parser = argparse.ArgumentParser(
        description="Storyteller: susun narasi & hook untuk video"
    )
    parser.add_argument("brief_path", help="Path ke production_brief.json")
    args = parser.parse_args()
    run_storyteller(args.brief_path)


if __name__ == "__main__":
    main()
