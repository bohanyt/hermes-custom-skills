"""
TREND RESEARCHER v2: Research per video type
Cari 10 video teratas berdasarkan video_type + keyword dari topik.
Analisis: views, likes, comments, hook pattern, transkrip 60 detik pertama.
"""
import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from config_api import call_llm

YT_DLP = str(Path(__file__).parent / "yt-dlp.exe")

PROMPT_SYSTEM = """Kamu adalah "Trend Analyst" untuk YouTube gaming.

Tugasmu: analisis data video YouTube dan temukan POLA yang membuat video sukses.

FOKUS ANALISIS:
1. Hook pattern — 3 detik pertama video (dari transkrip)
2. Judul pattern — apa yang bikin clickbait tapi relevan
3. Engagement pattern — views/likes ratio, komentar top
4. Struktur video — intro, rising action, climax, outro

OUTPUT FORMAT (JSON):
{
  "keyword": "keyword yang diteliti",
  "video_type": "jenis video",
  "top_videos": [
    {
      "title": "Judul video",
      "views": 123456,
      "channel": "Nama channel",
      "hook_3sec": "3 detik pertama transkrip",
      "judul_pattern": "Pattern judul (misal: [Angka] + [Power Word] + [Keyword])",
      "engagement_tips": "Tips dari video ini"
    }
  ],
  "recommended_title": "Judul yang disarankan untuk video kita",
  "recommended_hook": "Hook yang disarankan (1-2 kalimat)",
  "key_insights": ["insight 1", "insight 2", "insight 3"]
}"""

def search_youtube(keyword: str, max_results: int = 10) -> list:
    """Cari video YouTube via yt-dlp."""
    try:
        result = subprocess.run(
            [YT_DLP, f"ytsearch{max_results}:{keyword}", "--dump-json", "--no-download"],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode != 0:
            print(f"    ⚠️  yt-dlp error: {result.stderr[:100]}")
            return []
        
        videos = []
        for line in result.stdout.strip().split("\n"):
            if not line.strip():
                continue
            try:
                v = json.loads(line)
                videos.append({
                    "id": v.get("id", ""),
                    "title": v.get("title", ""),
                    "views": v.get("view_count", 0),
                    "likes": v.get("like_count", 0),
                    "channel": v.get("channel", ""),
                    "duration": v.get("duration", 0),
                    "url": v.get("webpage_url", ""),
                })
            except:
                continue
        return videos
    except subprocess.TimeoutExpired:
        print("    ⚠️  yt-dlp timeout")
        return []
    except Exception as e:
        print(f"    ⚠️  yt-dlp error: {e}")
        return []

def get_transcript(video_id: str) -> str:
    """Ambil transkrip 60 detik pertama via yt-dlp."""
    try:
        result = subprocess.run(
            [YT_DLP, f"https://youtu.be/{video_id}", "--write-auto-sub", "--sub-lang", "id", "--skip-download", "--sub-format", "vtt"],
            capture_output=True, text=True, timeout=30
        )
        # Find downloaded VTT file
        vtt_files = list(Path(".").glob("*.vtt"))
        if vtt_files:
            vtt_file = vtt_files[0]
            with open(vtt_file, "r", encoding="utf-8") as f:
                content = f.read()
            # Parse VTT, get first 60 seconds
            lines = []
            for line in content.split("\n"):
                if "-->" in line:
                    # Parse timestamp
                    parts = line.split("-->")
                    if parts:
                        ts = parts[0].strip()
                        h, m, s = 0, 0, 0
                        ts_parts = ts.split(":")
                        if len(ts_parts) == 3:
                            h, m, s = int(ts_parts[0]), int(ts_parts[1]), float(ts_parts[2].replace(",", "."))
                        total_sec = h * 3600 + m * 60 + s
                        if total_sec <= 60:
                            lines.append(line)
            # Cleanup
            for f in vtt_files:
                f.unlink(missing_ok=True)
            return "\n".join(lines[:10])
        return ""
    except:
        return ""

def research_topic(topic: dict, all_topics: list) -> dict:
    """Research 1 video type + keyword."""
    video_type = topic.get("video_type", "Unknown")
    label = topic.get("label", "")
    
    # Build search keyword
    keyword = f"{label} {video_type}"
    
    print(f"    🔍 Searching: '{keyword}'")
    videos = search_youtube(keyword, max_results=10)
    
    if not videos:
        return {
            "keyword": keyword,
            "video_type": video_type,
            "top_videos": [],
            "recommended_title": label,
            "recommended_hook": "",
            "key_insights": ["No data available"],
            "status": "no_data"
        }
    
    # Get transcripts for top 3 videos
    for v in videos[:3]:
        print(f"    📝 Transcript: {v['title'][:40]}...")
        transcript = get_transcript(v["id"])
        v["transcript_60s"] = transcript[:500] if transcript else ""
        time.sleep(1)  # Rate limit
    
    # Analyze with LLM
    videos_json = json.dumps(videos, ensure_ascii=False, indent=2)
    user_msg = f"""Analisis video berikut untuk video_type '{video_type}':

{videos_json}

Berikan analisis trend dalam format JSON."""
    
    messages = [
        {"role": "system", "content": PROMPT_SYSTEM},
        {"role": "user", "content": user_msg}
    ]
    
    try:
        response = call_llm("primary", messages, max_tokens=3000, temperature=0.3)
        response_clean = response.strip()
        if response_clean.startswith("```json"):
            response_clean = response_clean[7:]
        if response_clean.startswith("```"):
            response_clean = response_clean[3:]
        if response_clean.endswith("```"):
            response_clean = response_clean[:-3]
        response_clean = response_clean.strip()
        
        analysis = json.loads(response_clean)
        analysis["status"] = "ok"
        return analysis
    except Exception as e:
        return {
            "keyword": keyword,
            "video_type": video_type,
            "top_videos": videos[:3],
            "recommended_title": label,
            "recommended_hook": "",
            "key_insights": [f"Analysis error: {e}"],
            "status": "analysis_error"
        }

def main():
    if len(sys.argv) < 2:
        print("Usage: python trend_researcher_v2.py <topics.json>")
        sys.exit(1)
    
    topics_path = sys.argv[1]
    with open(topics_path, "r", encoding="utf-8") as f:
        topics = json.load(f)
    
    print("=" * 60)
    print("TREND RESEARCHER v2")
    print("=" * 60)
    print(f"  📊 Topics to research: {len(topics)}")
    
    # Group topics by video_type to avoid duplicate research
    video_types = {}
    for t in topics:
        vt = t.get("video_type", "Unknown")
        if vt not in video_types:
            video_types[vt] = []
        video_types[vt].append(t)
    
    print(f"  🏷️  Unique video types: {list(video_types.keys())}")
    
    # Research per video type
    all_research = {}
    for vt, type_topics in video_types.items():
        # Pick the highest engagement topic as representative
        best_topic = max(type_topics, key=lambda t: t.get("engagement_score", 0))
        print(f"\n  🔬 Researching: {vt} (via: {best_topic.get('label', '')})")
        
        research = research_topic(best_topic, topics)
        all_research[vt] = research
        
        if research.get("status") == "ok":
            print(f"    ✅ Found {len(research.get('top_videos', []))} videos")
            print(f"    💡 Recommended title: {research.get('recommended_title', '')[:50]}")
        else:
            print(f"    ⚠️  Status: {research.get('status')}")
        
        time.sleep(2)  # Rate limit between research
    
    # Save
    output_path = Path(topics_path).parent / "trend_research.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_research, f, ensure_ascii=False, indent=2)
    
    print(f"\n📝 Saved: {output_path}")
    print(f"✅ Research complete for {len(all_research)} video types")

if __name__ == "__main__":
    main()
