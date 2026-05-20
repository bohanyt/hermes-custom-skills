"""
STORYTELLER v2: 5C Storytelling per topik
Character, Context, Conflict, Climax, Closure
Narasi yang compelling + engaging, bukan editing notes.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from config_api import call_llm

PROMPT_SYSTEM = """Kamu adalah "Storyteller" profesional untuk YouTube gaming.

Tugasmu: dari topik yang diberikan, susun NARASI yang COMPELLING menggunakan framework 5C:

1. **Character** — Siapa protagonisnya? (streamer, karakter game, dll)
   - Apa yang mereka rasakan?
   - Apa motivasi mereka?

2. **Context** — Latar belakang situasi
   - Apa yang sedang terjadi?
   - Kenapa ini menarik?

3. **Conflict** — Masalah/tantangan yang dihadapi
   - Apa yang bikin tegang?
   - Apa yang dipertaruhkan?

4. **Climax** — Puncak momen paling exciting
   - Apa momen paling memorable?
   - Apa yang bikin penonton "WOW"?

5. **Closure** — Penutup/kesimpulan
   - Apa yang dipelajari?
   - Apa next step?

ATURAN:
- Narasi harus NATURAL dan CONVERSATIONAL (bukan formal)
- Gaya bahasa: santai, engaging, seperti YouTuber Indonesia
- Fokus ke EMOSI dan MOMEN, bukan deskripsi teknis
- Setiap section 2-4 kalimat
- Total narasi: 150-300 kata

OUTPUT FORMAT (JSON):
{
  "topic_id": "topic_001",
  "title": "Judul video yang clickbait tapi relevan",
  "hook": "Hook pembuka 1-2 kalimat (untuk 3 detik pertama)",
  "thumbnail_text": "Text untuk thumbnail (maks 5 kata)",
  "narasi": {
    "character": "Siapa + motivasi",
    "context": "Latar belakang",
    "conflict": "Masalah/tantangan",
    "climax": "Puncak momen",
    "closure": "Penutup"
  },
  "full_script": "Narasi lengkap yang sudah disusun mengalir (bisa langsung dibacakan)",
  "cta": "Call to action di akhir video"
}

PENTING:
- Output HARUS JSON valid
- full_script harus mengalir natural, bukan list
- Jangan tambahkan editing notes (sound effect, zoom, dll)
- Fokus ke STORY saja"""

PROMPT_USER = """Susun narasi 5C untuk topik berikut:

**Topik:** {label}
**Video Type:** {video_type}
**Summary:** {summary}
**Trend Research:** {trend_insights}

Buat narasi yang compelling dalam format JSON."""

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
    
    # Get trend insights
    trend_insights = ""
    if trend:
        recommended_title = trend.get("recommended_title", "")
        recommended_hook = trend.get("recommended_hook", "")
        key_insights = trend.get("key_insights", [])
        trend_insights = f"Recommended title: {recommended_title}\nRecommended hook: {recommended_hook}\nInsights: {', '.join(key_insights)}"
    
    user_msg = PROMPT_USER.replace("[[label]]", label).replace("[[video_type]]", video_type).replace("[[summary]]", summary).replace("[[trend_insights]]", trend_insights)
    
    messages = [
        {"role": "system", "content": PROMPT_SYSTEM},
        {"role": "user", "content": user_msg}
    ]
    
    try:
        response = call_llm("secondary", messages, max_tokens=3000, temperature=0.5)
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

def main():
    if len(sys.argv) < 2:
        print("Usage: python storyteller_v2.py <topics.json> [trend_research.json]")
        sys.exit(1)
    
    topics_path = sys.argv[1]
    trend_path = sys.argv[2] if len(sys.argv) > 2 else ""
    
    topics = load_topics(topics_path)
    trend = load_trend_research(trend_path) if trend_path else {}
    
    print("=" * 60)
    print("STORYTELLER v2 — 5C Storytelling")
    print("=" * 60)
    print(f"  📊 Topics: {len(topics)}")
    
    stories = []
    for i, topic in enumerate(topics):
        print(f"\n  [{i+1}/{len(topics)}] {topic.get('label', '')} ({topic.get('video_type', '')})")
        
        # Get trend for this video type
        vt = topic.get("video_type", "")
        type_trend = trend.get(vt, {})
        
        story = create_story(topic, type_trend)
        stories.append(story)
        
        if story.get("status") == "ok":
            print(f"    ✅ {story.get('title', '')[:50]}")
        else:
            print(f"    ❌ {story.get('status')}")
    
    # Save
    output_path = Path(topics_path).parent / "stories.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(stories, f, ensure_ascii=False, indent=2)
    
    print(f"\n📝 Saved: {output_path}")
    print(f"✅ {len(stories)} stories created")

if __name__ == "__main__":
    main()
