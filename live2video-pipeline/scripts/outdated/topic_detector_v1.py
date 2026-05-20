"""
TOPIC DETECTOR v2: Granular topic detection per chunk
Baca semua chunk summary satu per satu, tentukan:
- Tiap chunk dapat label topik yang SPESIFIK
- Merge chunk berdekatan yang topiknya SAMA PERSIS
- Setiap topik punya video_type yang cocok dari content_types.json

Output: topics.json dengan topik granular + video_type
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from config_api import call_llm

# Load content_types for video type reference
CONTENT_TYPES_PATH = Path(__file__).parent / "content_types.json"
CONTENT_TYPES = {}
if CONTENT_TYPES_PATH.exists():
    with open(CONTENT_TYPES_PATH, "r", encoding="utf-8") as f:
        ct = json.load(f)
        CONTENT_TYPES = ct.get("content_types", {})

# Build video type reference
VIDEO_TYPES = []
for niche_key, niche in CONTENT_TYPES.items():
    for ct in niche.get("content_types", []):
        VIDEO_TYPES.append(ct["jenis"])

PROMPT_SYSTEM = """Kamu adalah "Topic Detector" untuk livestream gaming/entertainment.

Tugasmu: baca semua chunk summary satu per satu (dari awal sampai akhir livestream) dan tentukan topik per chunk.

ATURAN:
1. Baca summary tiap chunk secara BERURUTAN (dari chunk_001 sampai terakhir)
2. Untuk tiap chunk, tentukan:
   a. Apakah topiknya SAMA dengan chunk sebelumnya? → merge
   b. Apakah topiknya BEDA? → topik baru
3. Label topik harus SPESIFIK dan DESKRIPTIF (bukan generic)
   - BAGUS: "First Reaction ZZZ Grafik Bikin Kaget", "Boss Battle Chicken Jacket", "Gacha Pull Dapat Epic"
   - JANGAN: "Gameplay", "Review", "Momen Lucu"
4. Setiap topik punya video_type yang pilih dari daftar:
   [Raw Clip - Reaction, YouTube Shorts, Storytime - Gaming, Video Essay - Analysis, Tutorial - Guide, Lore & Story Retelling, Rank Up / Progress, Rage / Funny Moments, Storytime - Horror, Raw Clip - Highlight, Raw Clip - Funny, Tutorial - Build With Me, Video Essay - Opinion, Raw Clip - Reaction, Storytime - Vibecoding]
5. video_type harus COCOK dengan isi topik:
   - Ada reaksi emosional kuat → Raw Clip - Reaction
   - Ada momen lucu/fail → Raw Clip - Funny / YouTube Shorts
   - Ada penjelasan mekanik/gameplay → Tutorial - Guide
   - Ada cerita pengalaman pribadi → Storytime - Gaming
   - Ada analisis/opini → Video Essay - Analysis
   - Ada momen epik/highlight → Raw Clip - Highlight
6. JANGAN terlalu agresif merge — lebih baik banyak topik kecil daripada sedikit topik besar
7. Minimal durasi per topik: 60 detik
8. Maksimal durasi per topik: 600 detik (10 menit) — kalau lebih, split jadi 2 topik

OUTPUT FORMAT (JSON array):
[
  {
    "topic_id": "topic_001",
    "label": "Label spesifik topik",
    "chunks": ["chunk_001", "chunk_002"],
    "start_time": "00:00:01",
    "end_time": "00:05:30",
    "duration_sec": 329,
    "summary": "Ringkasan 1-2 kalimat tentang topik ini",
    "video_type": "Raw Clip - Reaction",
    "engagement_score": 1-10,
    "reasoning": "Kenapa topik ini dapat video_type ini dan score ini"
  }
]

PENTING:
- Output HARUS JSON valid, tanpa markdown
- engagement_score: 1=biasa saja, 10=sangat engaging/viral potential
- Urutkan berdasarkan start_time
- Setiap chunk harus masuk ke tepat 1 topik"""

PROMPT_USER = """Analisis livestream ini dan tentukan topik per chunk:

**Total chunks:** {total_chunks}
**Total durasi:** {total_duration}

**Chunk Summaries:**
{chunks_summary}

Buat topic groups dalam format JSON sesuai aturan."""

def load_summaries(summaries_path: str) -> list:
    with open(summaries_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    elif isinstance(data, dict):
        for key in ["summaries", "chunks", "data"]:
            if key in data:
                return data[key]
        return list(data.values())
    return []

def detect_topics(summaries_path: str) -> list:
    summaries = load_summaries(summaries_path)
    print(f"  📊 Loaded {len(summaries)} summaries")
    
    # Format chunks summary
    chunks_text = ""
    total_duration = "unknown"
    for s in summaries:
        chunk_id = s.get("chunk_id", s.get("id", "unknown"))
        start = s.get("start_time", s.get("start", "00:00:00"))
        end = s.get("end_time", s.get("end", "00:00:00"))
        duration = s.get("duration_sec", 0)
        summary = s.get("summary", s.get("text", ""))
        chunks_text += f"[{chunk_id}] {start} → {end} ({duration}s): {summary}\n\n"
    
    # Get total duration from last chunk
    if summaries:
        last = summaries[-1]
        total_duration = last.get("end_time", last.get("end", "unknown"))
    
    user_prompt = PROMPT_USER.replace("[[total_chunks]]", str(len(summaries))).replace("[[total_duration]]", total_duration).replace("[[chunks_summary]]", chunks_text)
    
    messages = [
        {"role": "system", "content": PROMPT_SYSTEM},
        {"role": "user", "content": user_prompt}
    ]
    
    print("  🧠 Calling LLM for granular topic detection...")
    response = call_llm("secondary", messages, max_tokens=6000, temperature=0.3)
    
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
        topics = json.loads(response_clean)
        return topics
    except json.JSONDecodeError:
        print("  ⚠️  JSON parse failed, extracting...")
        import re
        match = re.search(r'\[.*\]', response_clean, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except:
                pass
        # Save raw for debug
        debug_path = Path(summaries_path).parent / "topics_raw.txt"
        with open(debug_path, "w", encoding="utf-8") as f:
            f.write(response_clean)
        print(f"  ❌ Parse failed, raw saved to {debug_path}")
        return []

def main():
    if len(sys.argv) < 2:
        print("Usage: python topic_detector.py <all_summaries.json>")
        sys.exit(1)
    
    summaries_path = sys.argv[1]
    print("=" * 60)
    print("TOPIC DETECTOR v2 — Granular")
    print("=" * 60)
    
    topics = detect_topics(summaries_path)
    
    if not topics:
        print("❌ No topics detected")
        sys.exit(1)
    
    # Sort by start_time
    topics.sort(key=lambda t: t.get("start_time", "00:00:00"))
    
    # Re-number
    for i, t in enumerate(topics):
        t["topic_id"] = f"topic_{i+1:03d}"
    
    print(f"\n✅ Detected {len(topics)} topics:\n")
    total_dur = 0
    for t in topics:
        dur = t.get("duration_sec", 0)
        total_dur += dur
        mins = dur // 60
        secs = dur % 60
        score = t.get("engagement_score", "?")
        print(f"  [{t['topic_id']}] {t.get('label', 'Unknown')}")
        print(f"    ⏱️ {t.get('start_time', '?')} → {t.get('end_time', '?')} ({mins}m{secs}s) | Score: {score}/10")
        print(f"    🏷️  {t.get('video_type', 'Unknown')}")
        print(f"    📦 Chunks: {', '.join(t.get('chunks', []))}")
        print(f"    📝 {t.get('summary', '')[:80]}")
        print()
    
    total_mins = total_dur // 60
    print(f"  📊 Total: {len(topics)} topics, {total_mins} menit tercakup")
    
    # Save
    output_path = Path(summaries_path).parent / "topics.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(topics, f, ensure_ascii=False, indent=2)
    print(f"📝 Saved: {output_path}")

if __name__ == "__main__":
    main()
