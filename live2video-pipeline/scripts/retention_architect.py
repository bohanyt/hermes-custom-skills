"""
RETENTION ARCHITECT: Edit pacing & cut boring parts
Simpan di hermes_skills/retention_architect.py

Baca story_brief.json + chunks, tentuin:
- Bagian yang harus dipotong (boring, pacing lambat)
- Bagian yang harus dipertahankan (hook, highlight, quote)
- Estimasi durasi final

Cara pakai:
  python retention_architect.py "path/to/chunks/story_brief.json"

Output:
  <chunks_folder>/
    └── edit_plan.json         ← rencana edit per konten
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

RETENTION_SYSTEM_PROMPT = """Kamu adalah "The Retention Architect", editor video yang fokus pada RETENTION (berapa banyak penonton yang stay sampai akhir).

Tugasmu: analisis story brief dan buat RENCANA EDITING yang memaksimalkan retention.

Prinsip editing:
1. HOOK dalam 5 detik pertama — kalau boring, orang langsung skip
2. PACING CEPAT — potong bagian yang gak ngontribusi ke cerita
3. PATTERN INTERRUPT — setiap 15-30 detik ada sesuatu yang berubah (cut, zoom, sound effect, text overlay)
4. NO DEAD AIR — hapus jeda panjang, "umm", "uhh", dll
5. END STRONG — akhir video harus memorable (punchline, twist, atau CTA)

Yang harus kamu tentuin per konten:
1. BAGIAN YANG DIPOTONG — Timestamp + alasan
2. BAGIAN YANG DIPERTAHANKAN — Timestamp + alasan
3. ESTIMASI DURASI FINAL
4. EDITING NOTES — Efek, transisi, sound yang disarankan

OUTPUT FORMAT (WAJIB JSON MURNI):
{
  "konten_id": 1,
  "jenis": "Video Essay / Shorts / dll",
  "durasi_original": "00:05:00",
  "durasi_estimasi_final": "00:03:30",
  "persentase_pemotongan": "30%",
  "bagian_dipotong": [
    {
      "timestamp": "00:01:00 - 00:01:30",
      "alasan": "Pacing lambat, gak ngontribusi ke cerita",
      "tipe": "dead air / repetitive / off-topic"
    }
  ],
  "bagian_dipertahankan": [
    {
      "timestamp": "00:00:00 - 00:00:15",
      "alasan": "Hook kuat, bikin penonton stay",
      "tipe": "hook / highlight / quote / climax"
    }
  ],
  "editing_notes": [
    "Tambah zoom-in di timestamp 00:02:30 untuk emphasis",
    "Potong 'umm' dan 'uhh' di bagian tengah",
    "Tambah sound effect di momen klimaks"
  ],
  "retention_score": 8,
  "retention_tips": [
    "Tips tambahan untuk meningkatkan retention"
  ]
}

PENTING:
- Output HARUS JSON valid, tanpa markdown code block
- Prioritaskan PACING CEPAT
- Target: setiap 15-30 detik ada perubahan visual/audio
- Retention score: 1-10 (10 = sangat engaging)"""

RETENTION_USER_TEMPLATE = """Analisis story brief berikut dan buat rencana editing:

**Story Brief:**
[[story_brief]]

**Chunks Info:**
[[chunks_info]]

Buat edit plan dalam format JSON sesuai instruksi."""


def load_json_safe(path: Path):
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def run_retention_architect(story_path: str):
    """
    Baca story_brief.json + chunks → edit_plan.json
    """
    story_file = Path(story_path)
    if not story_file.exists():
        print(f"❌ File tidak ditemukan: {story_file}")
        sys.exit(1)

    chunks_dir = story_file.parent

    # Load data
    stories = load_json_safe(story_file)
    if isinstance(stories, dict):
        stories = [stories]

    chunks_meta = load_json_safe(chunks_dir / "chunks.json")
    if isinstance(chunks_meta, dict):
        chunks_meta = [chunks_meta]

    print("=" * 60)
    print("RETENTION ARCHITECT — Pacing & Edit Plan")
    print("=" * 60)
    print(f"  📂 Story: {story_file}")
    print()

    all_edit_plans = []

    for story in stories:
        konten_id = story.get("konten_id", 0)
        jenis = story.get("jenis", "Unknown")
        judul = story.get("judul_final", "Unknown")
        story_flow = story.get("story_flow", [])

        print(f"[{konten_id}/{len(stories)}] Editing: {jenis} — {judul}")

        # Prepare chunks info
        chunks_info = json.dumps(chunks_meta[:20], ensure_ascii=False, indent=2) if chunks_meta else "No chunks info"

        # Call LLM
        messages = [
            {"role": "system", "content": RETENTION_SYSTEM_PROMPT},
            {"role": "user", "content": RETENTION_USER_TEMPLATE
                .replace("[[story_brief]]", json.dumps(story, ensure_ascii=False, indent=2))
                .replace("[[chunks_info]]", chunks_info)
            }
        ]

        try:
            response = call_llm(
                profile=PROFILE,
                messages=messages,
                max_tokens=2500,
                temperature=0.3
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
            plan = json.loads(response_clean)
        except json.JSONDecodeError:
            print(f"  ⚠️  JSON parse failed, saving raw")
            plan = {"raw_response": response, "konten_id": konten_id}

        all_edit_plans.append(plan)
        n_cut = len(plan.get("bagian_dipotong", []))
        n_keep = len(plan.get("bagian_dipertahankan", []))
        durasi = plan.get("durasi_estimasi_final", "?")
        score = plan.get("retention_score", "?")
        print(f"  ✅ Cut: {n_cut} parts, Keep: {n_keep} parts, Est: {durasi}, Score: {score}/10")

    # Simpan edit_plan.json
    edit_path = chunks_dir / "edit_plan.json"
    with open(edit_path, "w", encoding="utf-8") as f:
        json.dump(all_edit_plans, f, ensure_ascii=False, indent=2)

    # Ringkasan
    print()
    print("=" * 60)
    print("✅ EDIT PLAN COMPLETE")
    print("=" * 60)
    print(f"  📊 Edit plans: {len(all_edit_plans)}")
    print(f"  📝 Saved: {edit_path}")
    print()

    return all_edit_plans


def main():
    parser = argparse.ArgumentParser(
        description="Retention Architect: edit pacing & cut boring parts"
    )
    parser.add_argument("story_path", help="Path ke story_brief.json")
    args = parser.parse_args()
    run_retention_architect(args.story_path)


if __name__ == "__main__":
    main()
