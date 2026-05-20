"""
TREND RESEARCHER: Riset trend YouTube berdasarkan keyword
Simpan di hermes_skills/trend_researcher.py

Baca production_brief.json, cari keyword di YouTube,
kumpulkan data video trending.

Cara pakai:
  python trend_researcher.py "path/to/chunks/production_brief.json"
  python trend_researcher.py "path/to/production_brief.json" --max-results 10

Output:
  <chunks_folder>/
    └── trend_research.json     ← data trend YouTube
"""

import argparse
import json
import re
import subprocess
import sys
import time
import urllib.parse
from pathlib import Path

# ── config ─────────────────────────────────────────────────────────────
MAX_RESULTS_DEFAULT = 20      # max video per keyword
DELAY_BETWEEN_SEARCHES = 2.0  # detik antar search

# ── YouTube search via yt-dlp ──────────────────────────────────────────
def search_youtube(keyword: str, max_results: int = MAX_RESULTS_DEFAULT) -> list:
    """
    Cari video YouTube berdasarkan keyword pakai yt-dlp.
    Return list of {title, url, views, duration, channel}.
    """
    skills_dir = Path(__file__).parent.resolve()
    yt_dlp = str(skills_dir / "yt-dlp.exe")

    search_query = f"ytsearch{max_results}:{keyword}"

    cmd = [
        yt_dlp,
        "--flat-playlist",
        "--print", "%(title)s|%(url)s|%(view_count)s|%(duration_string)s|%(channel)s",
        "--no-download",
        search_query
    ]

    print(f"  [Search] '{keyword}' → ytsearch{max_results}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    except subprocess.TimeoutExpired:
        print(f"  ⚠️  Timeout search '{keyword}'")
        return []
    except Exception as e:
        print(f"  ⚠️  Error search '{keyword}': {e}")
        return []

    if result.returncode != 0:
        print(f"  ⚠️  Search failed: {result.stderr[:200]}")
        return []

    videos = []
    for line in result.stdout.strip().split("\n"):
        line = line.strip()
        if not line:
            continue

        parts = line.split("|")
        if len(parts) >= 3:
            title = parts[0].strip()
            url = parts[1].strip()
            try:
                views = int(parts[2].strip().replace(",", ""))
            except (ValueError, IndexError):
                views = 0
            duration = parts[3].strip() if len(parts) > 3 else "?"
            channel = parts[4].strip() if len(parts) > 4 else "?"

            videos.append({
                "title": title,
                "url": f"https://youtube.com{url}" if url.startswith("/") else url,
                "views": views,
                "duration": duration,
                "channel": channel
            })

    return videos


def run_trend_research(brief_path: str, max_results: int = MAX_RESULTS_DEFAULT):
    """
    Baca production_brief.json → cari keyword → trend_research.json
    """
    brief_file = Path(brief_path)
    if not brief_file.exists():
        print(f"❌ File tidak ditemukan: {brief_file}")
        sys.exit(1)

    chunks_dir = brief_file.parent

    # Load production brief
    with open(brief_file, "r", encoding="utf-8") as f:
        brief = json.load(f)

    print("=" * 60)
    print("TREND RESEARCHER — YouTube Trend Analysis")
    print("=" * 60)
    print(f"  📂 Brief: {brief_file}")
    print()

    # Extract keywords dari brief
    all_keywords = []
    potensi = brief.get("potensi_konten", [])

    for konten in potensi:
        keywords = konten.get("keyword_riset", [])
        jenis = konten.get("jenis", "Unknown")
        for kw in keywords:
            if kw not in all_keywords:
                all_keywords.append(kw)
            # Juga tambah variasi keyword + jenis
            combined = f"{kw} {jenis.lower()}"
            if combined not in all_keywords:
                all_keywords.append(combined)

    print(f"  🔑 Keywords: {', '.join(all_keywords)}")
    print(f"  📊 Max results per keyword: {max_results}")
    print()

    # Search per keyword
    all_research = []

    for i, keyword in enumerate(all_keywords):
        print(f"[{i+1}/{len(all_keywords)}] Researching: '{keyword}'")

        videos = search_youtube(keyword, max_results)

        # Sort by views descending
        videos.sort(key=lambda v: v.get("views", 0), reverse=True)

        # Analisis: cari judul yang catchy (clickbait patterns)
        clickbait_patterns = [
            r"\d+",                    # Angka (Top 10, 5 Tips, dll)
            r"!?+",                    # Tanda seru berulang
            r"[A-Z]{3,}",             # KAPITAL semua
            r"\b(cek|review|tour|guide|tips|trick|secret|hidden|epic|crazy|insane|unbelievable|shocking|viral|trending)\b",
        ]

        scored_videos = []
        for v in videos:
            score = 0
            title = v.get("title", "")

            # Score berdasarkan views
            views = v.get("views", 0)
            if views > 1_000_000:
                score += 3
            elif views > 100_000:
                score += 2
            elif views > 10_000:
                score += 1

            # Score berdasarkan clickbait patterns
            for pattern in clickbait_patterns:
                if re.search(pattern, title, re.IGNORECASE):
                    score += 1

            scored_videos.append({**v, "clickbait_score": score})

        # Top 3 per keyword
        top_videos = scored_videos[:3]

        research_entry = {
            "keyword": keyword,
            "total_found": len(videos),
            "top_videos": top_videos,
            "avg_views": sum(v.get("views", 0) for v in videos) // max(len(videos), 1),
            "clickbait_titles": [
                v["title"] for v in sorted(scored_videos, key=lambda x: x["clickbait_score"], reverse=True)[:3]
            ]
        }
        all_research.append(research_entry)

        print(f"  ✅ Found {len(videos)} videos, top views: {top_videos[0]['views']:,}" if top_videos else f"  ⚠️  No results")

        # Delay antar search
        if i < len(all_keywords) - 1:
            time.sleep(DELAY_BETWEEN_SEARCHES)

    # Compiling insights
    # Top 5 clickbait titles across all keywords
    all_titles = []
    for r in all_research:
        all_titles.extend(r.get("clickbait_titles", []))

    # Top keywords by avg views
    keywords_by_views = sorted(all_research, key=lambda r: r.get("avg_views", 0), reverse=True)

    trend_output = {
        "research_summary": {
            "total_keywords": len(all_keywords),
            "total_videos_found": sum(r.get("total_found", 0) for r in all_research),
            "top_keyword_by_views": keywords_by_views[0]["keyword"] if keywords_by_views else "N/A",
            "avg_views_overall": sum(r.get("avg_views", 0) for r in all_research) // max(len(all_research), 1),
        },
        "per_keyword": all_research,
        "insights": {
            "clickbait_patterns": {
                "gunakan_angka": "Top 5, 10 Tips, 7 Rahasia",
                "g kata_seru": "Jangan Pakai Terlalu Banyak!!!",
                "kata_kunci": ["cek", "review", "tour", "guide", "tips", "trick", "secret", "hidden", "epic", "crazy", "insane", "viral"],
            },
            "title_formulas": [
                f"{'Top N' if i == 0 else 'X'} + [angka] + [keyword] + [power word]"
                for i in range(3)
            ],
            "recommended_keywords": [r["keyword"] for r in keywords_by_views[:3]],
        }
    }

    # Simpan trend_research.json
    trend_path = chunks_dir / "trend_research.json"
    with open(trend_path, "w", encoding="utf-8") as f:
        json.dump(trend_output, f, ensure_ascii=False, indent=2)

    # Ringkasan
    summary = trend_output["research_summary"]
    print()
    print("=" * 60)
    print("✅ TREND RESEARCH COMPLETE")
    print("=" * 60)
    print(f"  📊 Keywords researched: {summary['total_keywords']}")
    print(f"  🎬 Total videos found: {summary['total_videos_found']}")
    print(f"  🔥 Top keyword: {summary['top_keyword_by_views']}")
    print(f"  📈 Avg views: {summary['avg_views_overall']:,}")
    print(f"  📝 Saved: {trend_path}")
    print()

    # Print top titles
    if "insights" in trend_output:
        print("💡 Top Clickbait Titles (reference):")
        for r in all_research[:3]:
            print(f"\n  [{r['keyword']}]")
            for title in r.get("clickbaint_titles", [])[:2]:
                # Typo fix: clickbait_titles
                pass
            for title in r.get("clickbait_titles", [])[:2]:
                print(f"    → {title}")

    return trend_output


def main():
    parser = argparse.ArgumentParser(
        description="Trend Researcher: riset YouTube trend berdasarkan keyword dari production brief"
    )
    parser.add_argument("brief_path", help="Path ke production_brief.json")
    parser.add_argument(
        "--max-results", "-m",
        type=int,
        default=MAX_RESULTS_DEFAULT,
        help=f"Max video results per keyword (default: {MAX_RESULTS_DEFAULT})"
    )

    args = parser.parse_args()
    run_trend_research(args.brief_path, args.max_results)


if __name__ == "__main__":
    main()
