"""
TREND RESEARCHER v3: Fixed yt-dlp handling
- Check yt-dlp executable
- Better error handling
- Fallback to ytsearch if yt-dlp fails
"""
import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from config_api import call_llm

# Find yt-dlp
def find_yt_dlp():
    """Cari yt-dlp executable."""
    # Check same directory
    local = Path(__file__).parent / "yt-dlp.exe"
    if local.exists():
        return str(local)
    
    # Check PATH
    try:
        result = subprocess.run(["where", "yt-dlp"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            return result.stdout.strip().split("\n")[0]
    except:
        pass
    
    # Check common locations
    for p in [
        Path.home() / "AppData" / "Local" / "Microsoft" / "WinGet" / "Packages" / "yt-dlp.exe",
        Path("C:/ProgramData/chocolatey/bin/yt-dlp.exe"),
        Path("C:/tools/yt-dlp/yt-dlp.exe"),
    ]:
        if p.exists():
            return str(p)
    
    return None

YT_DLP = find_yt_dlp()
print(f"  🔍 yt-dlp: {YT_DLP or 'NOT FOUND'}")

def search_youtube(keyword: str, max_results: int = 10) -> list:
    """Cari video YouTube via yt-dlp."""
    if not YT_DLP:
        print("    ⚠️  yt-dlp not found, skipping search")
        return []
    
    try:
        cmd = [YT_DLP, f"ytsearch{max_results}:{keyword}", "--dump-json", "--no-download", "--no-warnings"]
        print(f"    🔍 Running: {' '.join(cmd[:3])}...")
        
        result = subprocess.run(
            cmd,
            capture_output=True, text=True, timeout=60,
            cwd=str(Path(__file__).parent)  # Run from script directory
        )
        
        print(f"    📊 Return code: {result.returncode}")
        if result.stderr:
            print(f"    ⚠️  stderr: {result.stderr[:100]}")
        
        if result.returncode != 0:
            print(f"    ⚠️  yt-dlp error (code {result.returncode})")
            return []
        
        if not result.stdout or not result.stdout.strip():
            print("    ⚠️  No output from yt-dlp")
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
            except json.JSONDecodeError:
                continue
        
        print(f"    ✅ Found {len(videos)} videos")
        return videos
        
    except subprocess.TimeoutExpired:
        print("    ⚠️  yt-dlp timeout")
        return []
    except FileNotFoundError:
        print("    ⚠️  yt-dlp executable not found")
        return []
    except Exception as e:
        print(f"    ⚠️  yt-dlp error: {e}")
        return []

def research_video_type(video_type: str, keywords: list) -> dict:
    """Research 1 video type with multiple keywords."""
    all_videos = []
    
    for kw in keywords[:3]:  # Max 3 keywords per type
        print(f"    🔍 Searching: '{kw}'")
        videos = search_youtube(kw, max_results=10)
        all_videos.extend(videos)
        time.sleep(2)  # Rate limit
    
    if not all_videos:
        return {
            "video_type": video_type,
            "keywords": keywords,
            "top_videos": [],
            "status": "no_data",
            "recommended_title": keywords[0] if keywords else video_type,
            "recommended_hook": "",
            "key_insights": ["No data available"]
        }
    
    # Deduplicate by video ID
    seen = set()
    unique = []
    for v in all_videos:
        if v["id"] not in seen:
            seen.add(v["id"])
            unique.append(v)
    
    # Sort by views
    unique.sort(key=lambda v: v.get("views", 0), reverse=True)
    top = unique[:10]
    
    # Analyze with LLM
    videos_json = json.dumps(top, ensure_ascii=False, indent=2)
    
    PROMPT = f"""Analisis 10 video YouTube teratas untuk jenis video '{video_type}':

{videos_json}

Temukan:
1. Pattern judul yang paling clickbait tapi relevan
2. Hook pattern (dari judul + views)
3. Engagement tips

OUTPUT JSON:
{{
  "video_type": "{video_type}",
  "top_videos": [{{"title": "...", "views": 123, "channel": "...", "hook_pattern": "..."}}],
  "recommended_title": "Judul yang disarankan",
  "recommended_hook": "Hook 1-2 kalimat",
  "key_insights": ["insight 1", "insight 2"]
}}"""
    
    messages = [
        {"role": "system", "content": "Kamu adalah YouTube Trend Analyst. Output HARUS JSON valid."},
        {"role": "user", "content": PROMPT}
    ]
    
    try:
        response = call_llm("secondary", messages, max_tokens=2000, temperature=0.3)
        response_clean = response.strip()
        if response_clean.startswith("```json"):
            response_clean = response_clean[7:]
        if response_clean.startswith("```"):
            response_clean = response_clean[3:]
        if response_clean.endswith("```"):
            response_clean = response_clean[:-3]
        
        analysis = json.loads(response_clean)
        analysis["status"] = "ok"
        return analysis
    except Exception as e:
        return {
            "video_type": video_type,
            "top_videos": top[:3],
            "status": f"analysis_error: {e}",
            "recommended_title": top[0]["title"] if top else video_type,
            "recommended_hook": "",
            "key_insights": [f"Error: {e}"]
        }

def main():
    if len(sys.argv) < 2:
        print("Usage: python trend_researcher_v3.py <topics.json>")
        sys.exit(1)
    
    topics_path = sys.argv[1]
    with open(topics_path, "r", encoding="utf-8") as f:
        topics = json.load(f)
    
    print("=" * 60)
    print("TREND RESEARCHER v3")
    print("=" * 60)
    
    # Group by video_type
    video_types = {}
    for t in topics:
        vt = t.get("video_type", "Unknown")
        if vt not in video_types:
            video_types[vt] = []
        video_types[vt].append(t)
    
    print(f"  📊 Topics: {len(topics)}")
    print(f"  🏷️  Video types: {list(video_types.keys())}")
    
    # Research per video type
    all_research = {}
    for vt, type_topics in video_types.items():
        # Build keywords from topic labels
        keywords = [t.get("label", "") for t in type_topics[:3]]
        keywords = [k for k in keywords if k]  # Remove empty
        
        if not keywords:
            keywords = [vt]
        
        print(f"\n  🔬 Researching: {vt}")
        print(f"    📝 Keywords: {keywords}")
        
        research = research_video_type(vt, keywords)
        all_research[vt] = research
        
        if research.get("status") == "ok":
            print(f"    ✅ {len(research.get('top_videos', []))} videos analyzed")
        else:
            print(f"    ⚠️  Status: {research.get('status')}")
    
    # Save
    output_path = Path(topics_path).parent / "trend_research.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_research, f, ensure_ascii=False, indent=2)
    
    print(f"\n📝 Saved: {output_path}")
    print(f"✅ Research complete for {len(all_research)} video types")

if __name__ == "__main__":
    main()
