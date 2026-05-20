"""
MARKET SCRAPER: Scrape YouTube competitor data
Simpan di hermes_skills/market_scraper.py

Priority:
1. YouTube Data API v3 (kalau ada YOUTUBE_API_KEY di .env) — views akurat + filter tanggal
2. Fallback ke yt-dlp (kalau gak ada API key)

Cara pakai:
  python market_scraper.py "keyword1" "keyword2" --max-results 50
  python market_scraper.py "NTE hidden lore" --filter "this month" --min-views 100000

Output:
  market_research_<timestamp>.json
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
from pathlib import Path

# ── config ──────────────────────────────────────────────────────────────
SKILLS_DIR = Path(__file__).parent.resolve()
YT_DLP = str(SKILLS_DIR / "yt-dlp.exe")
DEFAULT_MAX_RESULTS = 50
MIN_VIEWS_DEFAULT = 100_000
TOP_N = 10

# ── load env ────────────────────────────────────────────────────────────
def load_env():
    """Load .env file."""
    env_file = SKILLS_DIR / ".env"
    if env_file.exists():
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key not in os.environ:
                    os.environ[key] = value

load_env()
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY", "")
USE_API = bool(YOUTUBE_API_KEY)

# ── YouTube Data API v3 ─────────────────────────────────────────────────
def yt_api_search(keyword: str, max_results: int = DEFAULT_MAX_RESULTS,
                  published_after: str = None, published_before: str = None) -> list:
    """
    Search YouTube pakai Data API v3.
    Return list of {id, title, channel, channelId, publishedAt, thumbnail}.
    """
    params = {
        "part": "snippet",
        "q": keyword,
        "type": "video",
        "maxResults": min(max_results, 50),
        "order": "relevance",
        "key": YOUTUBE_API_KEY,
    }

    if published_after:
        params["publishedAfter"] = published_after
    if published_before:
        params["publishedBefore"] = published_before

    url = f"https://www.googleapis.com/youtube/v3/search?{urllib.parse.urlencode(params)}"

    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"  ⚠️  YouTube API search error: {e}")
        return []

    videos = []
    for item in data.get("items", []):
        vid = item.get("id", {}).get("videoId", "")
        snippet = item.get("snippet", {})
        videos.append({
            "id": vid,
            "title": snippet.get("title", ""),
            "url": f"https://youtube.com/watch?v={vid}",
            "channel": snippet.get("channelTitle", "?"),
            "channel_id": snippet.get("channelId", ""),
            "published_at": snippet.get("publishedAt", ""),
            "thumbnail": snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
        })

    return videos


def yt_api_video_stats(video_ids: list) -> dict:
    """
    Ambil stats (views, likes, comments) untuk list video IDs.
    Return: {video_id: {views, likes, comments, ...}}
    """
    if not video_ids:
        return {}

    # API max 50 IDs per request
    all_stats = {}
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i:i+50]
        ids_str = ",".join(batch)

        params = {
            "part": "statistics,snippet",
            "id": ids_str,
            "key": YOUTUBE_API_KEY,
        }

        url = f"https://www.googleapis.com/youtube/v3/videos?{urllib.parse.urlencode(params)}"

        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            print(f"  ⚠️  YouTube API stats error: {e}")
            continue

        for item in data.get("items", []):
            vid = item.get("id", "")
            stats = item.get("statistics", {})
            snippet = item.get("snippet", {})
            all_stats[vid] = {
                "views": int(stats.get("viewCount", 0)),
                "likes": int(stats.get("likeCount", 0)),
                "comments": int(stats.get("commentCount", 0)),
                "channel": snippet.get("channelTitle", "?"),
                "channel_id": snippet.get("channelId", ""),
            }

    return all_stats


def yt_api_channel_stats(channel_ids: list) -> dict:
    """
    Ambil subscriber count untuk list channel IDs.
    Return: {channel_id: subscriber_count}
    """
    if not channel_ids:
        return {}

    all_stats = {}
    for i in range(0, len(channel_ids), 50):
        batch = channel_ids[i:i+50]
        ids_str = ",".join(batch)

        params = {
            "part": "statistics",
            "id": ids_str,
            "key": YOUTUBE_API_KEY,
        }

        url = f"https://www.googleapis.com/youtube/v3/channels?{urllib.parse.urlencode(params)}"

        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            print(f"  ⚠️  YouTube API channel error: {e}")
            continue

        for item in data.get("items", []):
            cid = item.get("id", "")
            stats = item.get("statistics", {})
            # Subscriber count might be hidden
            subs = stats.get("subscriberCount", "0")
            all_stats[cid] = int(subs) if subs.isdigit() else 0

    return all_stats


def yt_api_comments(video_id: str, max_comments: int = 10) -> list:
    """
    Ambil top comments dari video pakai YouTube API.
    Sort by likes (top likes first).
    Default: 10 comments.
    """
    params = {
        "part": "snippet",
        "videoId": video_id,
        "maxResults": min(max_comments, 100),
        "order": "relevance",
        "key": YOUTUBE_API_KEY,
    }

    url = f"https://www.googleapis.com/youtube/v3/commentThreads?{urllib.parse.urlencode(params)}"

    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"  ⚠️  YouTube API comments error: {e}")
        return []

    comments = []
    for item in data.get("items", []):
        top = item.get("snippet", {}).get("topLevelComment", {}).get("snippet", {})
        comments.append({
            "author": top.get("authorDisplayName", "?"),
            "text": top.get("textDisplay", ""),
            "likes": top.get("likeCount", 0),
        })

    # Sort by likes descending, take top N
    comments.sort(key=lambda c: c.get("likes", 0), reverse=True)
    return comments[:max_comments]


# ── yt-dlp fallback ─────────────────────────────────────────────────────
def yt_dlp_search(keyword: str, max_results: int = DEFAULT_MAX_RESULTS) -> list:
    """Search YouTube pakai yt-dlp (fallback)."""
    query = f"ytsearch{max_results}:{keyword}"

    cmd = [
        YT_DLP,
        "--flat-playlist",
        "--dump-single-json",
        "--no-download",
        query
    ]

    print(f"  [yt-dlp] Searching: '{keyword}'")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    except Exception as e:
        print(f"  ⚠️  yt-dlp error: {e}")
        return []

    if result.returncode != 0:
        return []

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return []

    videos = []
    entries = data.get("entries", []) if isinstance(data, dict) else []
    for entry in entries:
        if not entry:
            continue
        videos.append({
            "id": entry.get("id", ""),
            "title": entry.get("title", ""),
            "url": entry.get("webpage_url", f"https://youtube.com/watch?v={entry.get('id', '')}"),
            "views": entry.get("view_count", 0) or 0,
            "channel": entry.get("channel", entry.get("uploader", "?")),
            "channel_id": entry.get("channel_id", ""),
            "duration": entry.get("duration_string", "?"),
            "thumbnail": entry.get("thumbnail", ""),
        })

    return videos


def yt_dlp_comments(video_id: str, max_comments: int = 10) -> list:
    """Ambil comments pakai yt-dlp (fallback). Sort by likes, max 10."""
    url = f"https://youtube.com/watch?v={video_id}"
    cmd = [YT_DLP, "--write-comments", "--no-download", "--skip-download", url]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    except Exception:
        return []

    if result.returncode != 0:
        return []

    comments = []
    try:
        data = json.loads(result.stdout)
        for comment in data.get("comments", []):
            if isinstance(comment, dict):
                comments.append({
                    "author": comment.get("author", "?"),
                    "text": comment.get("text", ""),
                    "likes": comment.get("like_count", 0),
                })
    except Exception:
        pass

    # Sort by likes descending, take top N
    comments.sort(key=lambda c: c.get("likes", 0), reverse=True)
    return comments[:max_comments]


def yt_dlp_hook_transcript(video_id: str, max_seconds: int = 60) -> str:
    """Ambil 60 detik pertama transkrip pakai yt-dlp (fallback)."""
    url = f"https://youtube.com/watch?v={video_id}"
    cmd = [YT_DLP, "--write-auto-subs", "--sub-lang", "all", "--sub-format", "vtt",
           "--skip-download", "--no-download", url]

    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    except Exception:
        return ""

    vtt_files = sorted(Path(".").glob("*.vtt"), key=lambda f: f.stat().st_mtime, reverse=True)
    if not vtt_files:
        return ""

    try:
        with open(vtt_files[0], "r", encoding="utf-8") as f:
            content = f.read()

        lines = content.split("\n")
        hook_text = []
        for line in lines:
            ts_match = re.search(r"(\d{2}:\d{2}:\d{2}\.\d{3})", line)
            if ts_match:
                parts = ts_match.group(1).split(":")
                total_sec = int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
                if total_sec > max_seconds:
                    break
            elif line.strip() and not line.startswith("WEBVTT") and not line.startswith("NOTE"):
                hook_text.append(line.strip())

        # Cleanup
        for vf in vtt_files[:5]:
            try:
                vf.unlink()
            except Exception:
                pass

        return " ".join(hook_text[:20])
    except Exception:
        return ""


# ── helpers ─────────────────────────────────────────────────────────────
def parse_time_filter(filter_str: str) -> tuple:
    """
    Convert time filter string to ISO 8601 timestamps.
    Return: (published_after, published_before)
    """
    now = datetime.utcnow()
    filter_lower = filter_str.lower().strip()

    periods = {
        "today": timedelta(days=1),
        "this week": timedelta(weeks=1),
        "this month": timedelta(days=30),
        "this year": timedelta(days=365),
        "last week": timedelta(weeks=1),
        "last month": timedelta(days=30),
        "last year": timedelta(days=365),
    }

    delta = periods.get(filter_lower)
    if delta:
        after = (now - delta).strftime("%Y-%m-%dT%H:%M:%SZ")
        before = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        return after, before

    return None, None


def calculate_vs_ratio(views: int, subscribers: int) -> float:
    """Calculate Views/Subscribers ratio."""
    if subscribers <= 0:
        return 0.0
    return round(views / subscribers, 2)


def filter_by_views(videos: list, min_views: int = MIN_VIEWS_DEFAULT) -> list:
    """Filter video berdasarkan minimum views."""
    return [v for v in videos if v.get("views", 0) >= min_views]


# ── main ────────────────────────────────────────────────────────────────
def run_scraper(keywords: list, max_results: int = DEFAULT_MAX_RESULTS,
                time_filter: str = None, min_views: int = MIN_VIEWS_DEFAULT):
    """
    Main: search → stats → filter → deep dive → output JSON.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = SKILLS_DIR / f"market_research_{timestamp}.json"

    print("=" * 60)
    print("MARKET SCRAPER — YouTube Competitor Analysis")
    print("=" * 60)
    print(f"  🔑 Keywords: {', '.join(keywords)}")
    print(f"  📊 Max results: {max_results}")
    print(f"  📅 Time filter: {time_filter or 'None'}")
    print(f"  📉 Min views: {min_views:,}")
    print(f"  🔌 Backend: {'YouTube API v3' if USE_API else 'yt-dlp (fallback)'}")
    print()

    # Parse time filter
    published_after, published_before = None, None
    if time_filter:
        published_after, published_before = parse_time_filter(time_filter)

    # Step 1: Search
    print("STEP 1: Searching YouTube...")
    all_videos = {}

    for keyword in keywords:
        if USE_API:
            videos = yt_api_search(keyword, max_results, published_after, published_before)
        else:
            videos = yt_dlp_search(keyword, max_results)

        for v in videos:
            vid = v.get("id", "")
            if vid and vid not in all_videos:
                all_videos[vid] = v
        time.sleep(0.5)

    print(f"  📊 Total unique videos found: {len(all_videos)}")
    print()

    # Step 2: Get stats
    print("STEP 2: Fetching video stats...")
    videos_list = list(all_videos.values())
    video_ids = [v["id"] for v in videos_list if v.get("id")]

    if USE_API:
        # YouTube API: batch stats + channel stats
        stats = yt_api_video_stats(video_ids)
        for v in videos_list:
            vid = v.get("id", "")
            if vid in stats:
                v.update(stats[vid])

        # Get channel subscriber counts
        channel_ids = list(set(v.get("channel_id", "") for v in videos_list if v.get("channel_id")))
        channel_stats = yt_api_channel_stats(channel_ids)
        for v in videos_list:
            cid = v.get("channel_id", "")
            if cid in channel_stats:
                v["channel_followers"] = channel_stats[cid]
    else:
        # yt-dlp: fetch per video (slower)
        for i, v in enumerate(videos_list):
            vid = v.get("id", "")
            if vid:
                url = f"https://youtube.com/watch?v={vid}"
                cmd = [YT_DLP, "--dump-single-json", "--no-download", url]
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                    if result.returncode == 0:
                        data = json.loads(result.stdout)
                        v["views"] = data.get("view_count", 0) or 0
                        v["likes"] = data.get("like_count", 0) or 0
                        v["channel_followers"] = data.get("channel_follower_count", 0) or 0
                except Exception:
                    pass
                if (i + 1) % 10 == 0:
                    print(f"    [{i+1}/{len(videos_list)}] Stats fetched")
                time.sleep(0.5)

    print()

    # Step 3: Filter by views
    print(f"STEP 3: Filtering (min views: {min_views:,})...")
    filtered = filter_by_views(videos_list, min_views)
    print(f"  📊 After filtering: {len(filtered)} videos")

    # Calculate V/S ratio
    for v in filtered:
        subs = v.get("channel_followers", 0)
        v["vs_ratio"] = calculate_vs_ratio(v.get("views", 0), subs)

    # Sort by V/S ratio
    filtered.sort(key=lambda v: v.get("vs_ratio", 0), reverse=True)
    print()

    # Step 4: Deep dive TOP 10
    top_videos = filtered[:TOP_N]
    print(f"STEP 4: Deep diving top {TOP_N} videos...")

    for i, v in enumerate(top_videos):
        vid = v.get("id", "")
        print(f"\n  [{i+1}/{TOP_N}] {v.get('title', '?')[:60]}...")
        print(f"    Views: {v.get('views', 0):,} | V/S: {v.get('vs_ratio', 0)}")

        # Comments — top 10 by likes
        if USE_API:
            comments = yt_api_comments(vid, 10)
        else:
            comments = yt_dlp_comments(vid, 10)
        v["comments"] = comments
        v["comment_count"] = len(comments)
        print(f"    Comments: {len(comments)} (top likes)")

        # Hook transcript
        hook = yt_dlp_hook_transcript(vid, 60)
        v["hook_transcript"] = hook
        if hook:
            print(f"    Hook: {hook[:80]}...")

        time.sleep(1)

    # Compile output
    output = {
        "timestamp": timestamp,
        "backend": "youtube_api_v3" if USE_API else "yt-dlp",
        "keywords": keywords,
        "time_filter": time_filter,
        "total_found": len(all_videos),
        "total_filtered": len(filtered),
        "top_videos": [
            {
                "id": v.get("id"),
                "title": v.get("title"),
                "url": v.get("url"),
                "views": v.get("views", 0),
                "likes": v.get("likes", 0),
                "channel": v.get("channel", "?"),
                "channel_followers": v.get("channel_followers", 0),
                "vs_ratio": v.get("vs_ratio", 0),
                "duration": v.get("duration", "?"),
                "thumbnail": v.get("thumbnail", ""),
                "comments_preview": v.get("comments", [])[:5],
                "hook_transcript": v.get("hook_transcript", ""),
                "outlier_score": v.get("vs_ratio", 0) * 10,
            }
            for v in top_videos
        ]
    }

    # Save
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    # Ringkasan
    print()
    print("=" * 60)
    print("✅ MARKET RESEARCH COMPLETE")
    print("=" * 60)
    print(f"  📁 Output: {output_file.name}")
    print(f"  🔌 Backend: {output['backend']}")
    print(f"  📊 Top {TOP_N} videos analyzed")
    if top_videos:
        avg_vs = sum(v.get("vs_ratio", 0) for v in top_videos) / len(top_videos)
        print(f"  📈 Avg V/S ratio: {avg_vs:.1f}")
        print(f"  🏆 Top performer: {top_videos[0].get('title', '?')[:50]}")
        print(f"     Views: {top_videos[0].get('views', 0):,} | V/S: {top_videos[0].get('vs_ratio', 0)}")

    return output_file


def main():
    parser = argparse.ArgumentParser(
        description="Market Scraper: YouTube competitor analysis"
    )
    parser.add_argument("keywords", nargs="+", help="Keywords untuk search")
    parser.add_argument(
        "--max-results", "-m",
        type=int,
        default=DEFAULT_MAX_RESULTS,
        help=f"Max YouTube results per keyword (default: {DEFAULT_MAX_RESULTS})"
    )
    parser.add_argument(
        "--filter",
        default=None,
        help="Time filter: 'today', 'this week', 'this month', 'this year'"
    )
    parser.add_argument(
        "--min-views",
        type=int,
        default=MIN_VIEWS_DEFAULT,
        help=f"Minimum views filter (default: {MIN_VIEWS_DEFAULT})"
    )

    args = parser.parse_args()
    run_scraper(args.keywords, args.max_results, args.filter, args.min_views)


if __name__ == "__main__":
    main()
