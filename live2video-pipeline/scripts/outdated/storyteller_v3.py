"""
STORYTELLER v3: 5C Storytelling dengan konteks topik yang akurat
Prompt include isi summary topik, bukan cuma video_type.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from config_api import call_llm

PROMPT_SYSTEM = """Kamu adalah "Storyteller" profesional untuk YouTube gaming.

Tugasmu: dari TOPIK yang diberikan (dengan summary dan konteks), susun NARASI yang COMPELLING menggunakan 5C:

1. **Character** — Siapa protagonisnya? Apa yang mereka rasakan?
2. **Context** — Latar belakang situasi, apa yang sedang terjadi?
3. **Conflict** — Masalah/tantangan yang dihadapi
4. **Climax** — Puncak momen paling exciting
5. **Closure** — Penutup/kesimpulan

ATURAN KETAT:
- Narasi HARUS SESUAI dengan isi topik yang diberikan
- JANGAN mengarang cerita yang tidak ada di summary
- Jika topik tentang "Boss Battle", ceritakan boss battle-nya
- Jika topik tentang "Gacha Pull", ceritakan gacha-nya
- Jika topik tentang "Momen Lucu", ceritakan momen lucunya
- Gaya bahasa: santai, engaging, seperti YouTuber Indonesia
- Fokus ke EMOSI dan MOMEN, bukan deskripsi teknis
- Jangan tambahkan editing notes (sound effect, zoom, dll)

OUTPUT FORMAT (JSON):
{
  "topic_id": "topic_001",
  "title": "Judul video yang clickbait tapi relevan dengan isi",
  "hook": "Hook pembuka 1-2 kalimat",
  "thumbnail_text": "Text untuk thumbnail (maks 5 kata)",
  "narasi": {
    "character": "Siapa + motivasi",
    "context": "Latar belakang",
    "conflict": "Masalah/tantangan",
    "climax": "Puncak momen",
    "closure": "Penutup"
  },
  "full_script": "Narasi lengkap yang mengalir natural (bisa langsung dibacakan)",
  "cta": "Call to action di akhir"
}

PENTING: Output HARUS JSON valid, tanpa markdown."""

PROMPT_USER = """Susun narasi 5C untuk topik berikut. PASTIKAN narasi SESUAI dengan isi topik!

**Topik:** {label}
**Video Type:** {video_type}
**Summary Topik:** {summary}
**Chunks yang termasuk:** {chunks}
**Trend Insights:** {trend_insights}

INGAT: Narasi harus SESUAI dengan summary di atas. Jangan mengarang cerita yang tidak ada di summary.

Buat narasi dalam format JSON."""

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
    
    # Get trend insights
    trend_insights = ""
    if trend:
        recommended_title = trend.get("recommended_title", "")
        recommended_hook = trend.get("recommended_hook", "")
        key_insights = trend.get("key_insights", [])
        trend_insights = f"Recommended title: {recommended_title}\nRecommended hook: {recommended_hook}\nInsights: {', '.join(key_insights)}"
    
    user_msg = PROMPT_USER \
        .replace("[[label]]", label) \
        .replace("[[video_type]]", video_type) \
        .replace("[[summary]]", summary) \
        .replace("[[chunks]]", chunks) \
        .replace("[[trend_insights]]", trend_insights)
    
    messages = [
        {"role": "system", "content": PROMPT_SYSTEM},
        {"role": "user", "content": user_msg}
    ]
    
    # Retry 2x
    for attempt in range(2):
        try:
            response = call_llm("secondary", messages, max_tokens=3000, temperature=0.5)
            
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
        print("Usage: python storyteller_v3.py <topics.json> [trend_research.json]")
        sys.exit(1)
    
    topics_path = sys.argv[1]
    trend_path = sys.argv[2] if len(sys.argv) > 2 else ""
    
    topics = load_topics(topics_path)
    trend = load_trend_research(trend_path) if trend_path else {}
    
    print("=" * 60)
    print("STORYTELLER v3 — 5C dengan Konteks Topik")
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
    
    # Save
    output_path = Path(topics_path).parent / "stories.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(stories, f, ensure_ascii=False, indent=2)
    
    print(f"\n📝 Saved: {output_path}")
    print(f"✅ {len(stories)} stories created")

if __name__ == "__main__":
    main()
