"""
STORYTELLER v4: 5C Storytelling — Strict context adherence
- Prompt sangat ketat: JANGAN mengarang, SESUAIKAN 100% dengan summary
- Include contoh benar/salah di prompt
- Judul harus unik per topik (gak boleh "GACHA" semua)
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from config_api import call_llm

PROMPT_SYSTEM = """Kamu adalah "Storyteller" profesional untuk YouTube gaming.

Tugasmu: dari TOPIK yang diberikan, susun NARASI 5C yang COMPELLING dan SESUAI 100% dengan isi topik.

=== ATURAN SANGAT KETAT ===

1. NARASI HARUS 100% SESUAI dengan summary topik
   - BACA summary dengan teliti
   - CERITAKAN hal yang ADA di summary
   - JANGAN mengarang cerita yang TIDAK ADA di summary
   - JANGAN pakai template/generic story

2. CONTOH BENAR vs SALAH:
   - Topik: "Boss Battle Chicken Jacket" → Ceritakan boss battle melawan Chicken Jacket
   - Topik: "Gacha Pull Dapat Epic" → Ceritakan momen gacha pull dan reaksi dapat epic
   - Topik: "Momen Lucu Chat" → Ceritakan interaksi lucu dengan chat
   - SALAH: Semua topik diceritakan sama (nangis, gacha, dll)

3. JUDUL harus UNIK dan SPESIFIK:
   - JANGAN pakai kata "GACHA" kecuali topik memang tentang gacha
   - JANGAN pakai template "[EMOSI] di [TEMPAT]!"
   - Buat judul yang berbeda untuk setiap topik

4. 5C Framework:
   - Character: Siapa + motivasi (sesuai konteks topik)
   - Context: Latar belakang (dari summary)
   - Conflict: Masalah/tantangan (dari summary)
   - Climax: Puncak momen (dari summary)
   - Closure: Penutup (dari summary)

5. Gaya: santai, engaging, seperti YouTuber Indonesia
6. Jangan tambahkan editing notes

=== OUTPUT FORMAT ===
{
  "topic_id": "topic_001",
  "title": "Judul UNIK yang relevan dengan isi (bukan template)",
  "hook": "Hook 1-2 kalimat yang relate dengan topik",
  "thumbnail_text": "Maks 5 kata",
  "narasi": {
    "character": "...",
    "context": "...",
    "conflict": "...",
    "climax": "...",
    "closure": "..."
  },
  "full_script": "Narasi lengkap yang mengalir natural",
  "cta": "Call to action"
}"""

PROMPT_USER = """Susun narasi 5C untuk topik berikut.

=== TOPIK ===
Label: {label}
Video Type: {video_type}
Summary: {summary}
Chunks: {chunks}

=== TREND INSIGHTS ===
{trend_insights}

INGAT: Narasi HARUS 100% SESUAI dengan summary di atas. JANGAN mengarang!

Output JSON:"""

def load_topics(topics_path: str) -> list:
    with open(topics_path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_trend_research(trend_path: str) -> dict:
    if Path(trend_path).exists():
        with open(trend_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def create_story(topic: dict, trend: dict) -> dict:
    label = topic.get("label", "")
    video_type = topic.get("video_type", "")
    summary = topic.get("summary", "")
    chunks = ", ".join(topic.get("chunks", []))
    
    trend_insights = ""
    if trend:
        recommended_title = trend.get("recommended_title", "")
        recommended_hook = trend.get("recommended_hook", "")
        key_insights = trend.get("key_insights", [])
        trend_insights = f"Recommended title: {recommended_title}\nRecommended hook: {recommended_hook}\nInsights: {', '.join(key_insights)}"
    
    user_msg = PROMPT_USER \
        .replace("{label}", label) \
        .replace("{video_type}", video_type) \
        .replace("{summary}", summary) \
        .replace("{chunks}", chunks) \
        .replace("{trend_insights}", trend_insights)
    
    messages = [
        {"role": "system", "content": PROMPT_SYSTEM},
        {"role": "user", "content": user_msg}
    ]
    
    for attempt in range(2):
        try:
            response = call_llm("secondary", messages, max_tokens=3000, temperature=0.4)
            
            if not response or not response.strip():
                continue
            
            response_clean = response.strip()
            if response_clean.startswith("```json"):
                response_clean = response_clean[7:]
            if response_clean.startswith("```"):
                response_clean = response_clean[3:]
            if response_clean.endswith("```"):
                response_clean = response_clean[:-3]
            response_clean = response_clean.strip()
            
            story = json.loads(response_clean)
            story["topic_id"] = topic.get("topic_id", "")
            story["status"] = "ok"
            return story
        except Exception as e:
            if attempt == 0:
                continue
            return {
                "topic_id": topic.get("topic_id", ""),
                "title": label,
                "hook": "",
                "thumbnail_text": "",
                "narasi": {},
                "full_script": summary,
                "cta": "",
                "status": f"error: {e}"
            }
    
    return {
        "topic_id": topic.get("topic_id", ""),
        "title": label,
        "hook": "",
        "thumbnail_text": "",
        "narasi": {},
        "full_script": summary,
        "cta": "",
        "status": "max_retries"
    }

def main():
    if len(sys.argv) < 2:
        print("Usage: python storyteller_v4.py <topics.json> [trend_research.json]")
        sys.exit(1)
    
    topics_path = sys.argv[1]
    trend_path = sys.argv[2] if len(sys.argv) > 2 else ""
    
    topics = load_topics(topics_path)
    trend = load_trend_research(trend_path) if trend_path else {}
    
    print("=" * 60)
    print("STORYTELLER v4 — Strict Context")
    print("=" * 60)
    print(f"  📊 Topics: {len(topics)}")
    
    stories = []
    for i, topic in enumerate(topics):
        print(f"\n  [{i+1}/{len(topics)}] {topic.get('label', '')} ({topic.get('video_type', '')})")
        
        vt = topic.get("video_type", "")
        type_trend = trend.get(vt, {})
        
        story = create_story(topic, type_trend)
        stories.append(story)
        
        if story.get("status") == "ok":
            print(f"    ✅ {story.get('title', '')[:50]}")
        else:
            print(f"    ❌ {story.get('status')}")
    
    output_path = Path(topics_path).parent / "stories.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(stories, f, ensure_ascii=False, indent=2)
    
    print(f"\n📝 Saved: {output_path}")
    print(f"✅ {len(stories)} stories created")

if __name__ == "__main__":
    main()
