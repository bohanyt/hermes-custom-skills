"""
TREND RESEARCHER v4: YouTube Data API v3
Pakai YouTube Data API v3 untuk search + video stats.
Gratis, reliable, gak perlu yt-dlp.
"""
import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from config_api import get_api_config

def load_topics(topics_path: str) -> list:
    with open(topics_path, "r", encoding="utf-8") as f:
        return json.load(f)

def youtube_search(query: str, max_results: int = 10) -> list:
    """Search YouTube via Data API v3."""
    # Load API key from .env
    from config_api import load_env
    load_env()
    import os
    api_key = os.environ.get("YOUTUBE_API_KEY", "")
    
    if not api_key:
        print("    ⚠️  YOUTUBE_API_KEY not found")
        return []
    
    url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={urllib.parse.quote(query)}&type=video&maxResults={max_results}&key={api_key}"
    
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        
        videos = []
        for item in data.get("items", []):
            videos.append({
                "id": item["id"]["videoId"],
                "title": item["snippet"]["title"],
                "channel": item["snippet"]["channelTitle"],
                "description": item["snippet"].get("description", "")[:200],
            })
        
        return videos
    except Exception as e:
        print(f"    ⚠️  YouTube API error: {e}")
        return []

def youtube_video_stats(video_ids: list) -> dict:
    """Get video statistics via Data API v3."""
    from config_api import load_env
    load_env()
    import os
    api_key = os.environ.get("YOUTUBE_API_KEY", "")
    
    if not api_key or not video_ids:
        return {}
    
    ids = ",".join(video_ids)
    url = f"https://www.googleapis.com/youtube/v3/videos?part=statistics,snippet&id={ids}&key={api_key}"
    
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        
        stats = {}
        for item in data.get("items", []):
            vid = item["id"]
            stats[vid] = {
                "views": int(item["statistics"].get("viewCount", 0)),
                "likes": int(item["statistics"].get("likeCount", 0)),
                "comments": int(item["statistics"].get("commentCount", 0)),
            }
        
        return stats
    except Exception as e:
        print(f"    ⚠️  YouTube API error: {e}")
        return {}

def research_video_type(video_type: str, keywords: list) -> dict:
    """Research 1 video type via YouTube Data API."""
    all_videos = []
    
    for kw in keywords[:3]:
        print(f"    🔍 Searching: '{kw}'")
        videos = youtube_search(kw, max_results=10)
        all_videos.extend(videos)
    
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
    
    # Deduplicate
    seen = set()
    unique = []
    for v in all_videos:
        if v["id"] not in seen:
            seen.add(v["id"])
            unique.append(v)
    
    # Get stats for top 10
    top = unique[:10]
    stats = youtube_video_stats([v["id"] for v in top])
    
    for v in top:
        v.update(stats.get(v["id"], {}))
    
    # Sort by views
    top.sort(key=lambda v: v.get("views", 0), reverse=True)
    
    return {
        "video_type": video_type,
        "keywords": keywords,
        "top_videos": top,
        "status": "ok",
        "recommended_title": top[0]["title"] if top else video_type,
        "recommended_hook": "",
        "key_insights": [f"Found {len(top)} videos"],
    }

def main():
    if len(sys.argv) < 2:
        print("Usage: python trend_researcher_v4.py <topics.json>")
        sys.exit(1)
    
    topics_path = sys.argv[1]
    topics = load_topics(topics_path)
    
    print("=" * 60)
    print("TREND RESEARCHER v4 — YouTube Data API v3")
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
        keywords = [t.get("label", "") for t in type_topics[:3]]
        keywords = [k for k in keywords if k]
        
        if not keywords:
            keywords = [vt]
        
        print(f"\n  🔬 Researching: {vt}")
        print(f"    📝 Keywords: {keywords}")
        
        research = research_video_type(vt, keywords)
        all_research[vt] = research
        
        if research.get("status") == "ok":
            print(f"    ✅ {len(research.get('top_videos', []))} videos found")
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
