# YouTube Data API v3 Integration

## Setup

1. Go to https://console.cloud.google.com
2. Create a new project (or use existing)
3. Enable "YouTube Data API v3" (APIs & Services → Library → search → enable)
4. Create API key (APIs & Services → Credentials → Create → API key)
5. Copy key (format: `AIzaSyXXXXXXXXXXXXXXXX`)

## Add to .env

```env
YOUTUBE_API_KEY=AIzaSyXXXXXXXXXXXXXXXX
```

## Free Tier Limits

- **10,000 units/day** (free)
- Search: 100 units per call
- Video stats: 1 unit per call (batch up to 50)
- Channel stats: 1 unit per call (batch up to 50)
- Comment threads: 1 unit per call

## What the API Enables

| Feature | yt-dlp | YouTube API |
|---------|--------|-------------|
| Accurate view count | ❌ Cached/delayed | ✅ Real-time |
| Date filter (publishedAfter) | ⚠️ Limited | ✅ Full support |
| Min views filter | ❌ Not available | ✅ Post-filter |
| Subscriber count | ❌ Unreliable | ✅ Accurate |
| Comments sorted by likes | ⚠️ Basic | ✅ Top by likes |
| Batch requests | ❌ One-by-one | ✅ Up to 50 IDs per call |

## Fallback Behavior

Scripts use this priority:
1. If `YOUTUBE_API_KEY` exists in `.env` → YouTube API (accurate, fast)
2. Otherwise → yt-dlp fallback (slower, less accurate)

## Quota Management

For `market_scraper.py` with 3 keywords × 50 results:
- Search: 3 × 100 = 300 units
- Video stats: ~150 videos × 1 = 150 units (batched)
- Channel stats: ~50 channels × 1 = 50 units (batched)
- Comments: 10 videos × 1 = 10 units
- **Total: ~511 units** per full run (well within 10K free tier)
