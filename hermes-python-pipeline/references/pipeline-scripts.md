# Pipeline Scripts Reference

Complete script inventory for the hermes_live2video pipeline. All scripts live in `hermes_skills/`.

## Script Catalog

| # | Script | Input | Output | API? | Model |
|---|--------|-------|--------|------|-------|
| 1 | `fetch_livestream.py` | YouTube URL | `video.mp4` + `.vtt` + `metadata.json` | No | — |
| 2 | `semanticchunker.py` | `.vtt` file | `chunks/*.txt` + `chunks.json` | No | — |
| 3 | `chunk_merger.py` | `chunks.json` | `merged/chunks.json` + merged txt | Yes (1x) | Summarizer profile |
| 4 | `chunk_summarizer.py` | `chunks.json` (or `merged/chunks.json`) | `chunk_XXX.summary.txt` + `all_summaries.json` | Yes | Summarizer profile (free tier) |
| 5 | `orchestrator.py` | `all_summaries.json` + `metadata.json` | `production_brief.json` | Yes | Primary profile |
| 6 | `trend_researcher.py` | `production_brief.json` | `trend_research.json` | No | yt-dlp search (20 video/keyword) |
| 7 | `data_miner.py` | `production_brief.json` + chunks | `data_mining.json` | Yes | Primary profile |
| 8 | `storyteller.py` | brief + mining + trend | `story_brief.json` | Yes | Primary profile |
| 9 | `retention_architect.py` | `story_brief.json` | `edit_plan.json` | Yes | Primary profile |
| 10 | `technician.py` | `edit_plan.json` + video | `final_cuts/*.mp4` (separate clips) | No | ffmpeg |
| 11 | `market_scraper.py` | Keywords (+ filters) | `market_research_<timestamp>.json` | Optional | YouTube Data API v3 or yt-dlp fallback |
| 12 | `logsynchronizer.py` | Video dir + markers + chat | `sync_data.json` | No | — |
| 13 | `content_types.json` | (config) | Niche-to-content-type mapping | No | — |

## Execution Order

Scripts must run in sequence — each depends on the previous step's output:

```bash
# Step 1: Download
python fetch_livestream.py "https://youtube.com/watch?v=XXXXX"

# Step 2: Chunk transcript (per ~2.5 min, fixed duration)
python semanticchunker.py "raw_footages/<video>/<video>.id.vtt"

# Step 3: Merge chunks by topic (hybrid: fixed duration + LLM merge)
python chunk_merger.py "raw_footages/<video>/chunks/chunks.json"

# Step 4: Summarize merged chunks (rate-limited, ~3s delay per chunk)
python chunk_summarizer.py "raw_footages/<video>/chunks/merged/chunks.json"

# Step 5: Orchestrator analysis (detect niche + choose video types)
python orchestrator.py "raw_footages/<video>/chunks/merged/all_summaries.json"

# Step 6: Trend research (20 videos per keyword)
python trend_researcher.py "raw_footages/<video>/chunks/merged/production_brief.json"

# Step 7: Data mining (quotes, timestamps, moments)
python data_miner.py "raw_footages/<video>/chunks/merged/production_brief.json"

# Step 8: Storytelling (narrative + hooks)
python storyteller.py "raw_footages/<video>/chunks/merged/production_brief.json"

# Step 9: Retention/ pacing edit plan
python retention_architect.py "raw_footages/<video>/chunks/merged/story_brief.json"

# Step 10: Render final cuts (separate clips, NOT merged)
python technician.py "raw_footages/<video>/chunks/merged/edit_plan.json"
```

## Data Flow

```
Livestream URL
    ↓
fetch_livestream.py ──→ raw_footages/<video>/
    ↓                        ├─ video.mp4
semanticchunker.py           ├─ video.id.vtt
    ↓                        ├─ video.en.vtt
chunk_summarizer.py          └─ metadata.json
    ↓
orchestrator.py ──────────→ production_brief.json
    ↓
trend_researcher.py ──────→ trend_research.json
    ↓
data_miner.py ────────────→ data_mining.json
    ↓
storyteller.py ───────────→ story_brief.json
    ↓
retention_architect.py ───→ edit_plan.json
    ↓
technician.py ────────────→ final_cuts/<video>/
                               ├─ konten_1.mp4
                               ├─ konten_2.mp4
                               └─ render_log.json
```

## API Config

Scripts use two API profiles via `config_api.py` + `.env`:

| Profile | Purpose | Example Model |
|---------|---------|---------------|
| `primary` | Orchestrator, Data Miner, Storyteller, Retention | `openrouter/owl-alpha` |
| `summarizer` | Chunk summaries (rate-limited free tier) | `nvidia/nemotron-nano-12b-v2-vl:free` |

Both profiles can share the same OpenRouter API key. Only the model differs.

## Chunk Sizing Math

- Speech rate: ~150-200 words/minute
- Target chunk: ~2.5 minutes
- Words per chunk: ~375-500 words
- Chars per chunk: ~2,500-3,500 chars
- Max chars (safety): 6,000 (for 8K context window models)
- Smart cut: finds silence gap >1.5s near boundary

## Key Output Files

### production_brief.json
```json
{
  "analisis_keseluruhan": { "topik_utama": "...", "vibe_energi": "..." },
  "potensi_konten": [
    {
      "id": 1,
      "jenis": "Video Essay / Shorts / Storytime / Raw Clip",
      "judul_saran": "...",
      "hook": "...",
      "chunks_dipake": ["chunk_001", "chunk_002"],
      "keyword_riset": ["keyword1", "keyword2"]
    }
  ]
}
```

### data_mining.json
Per konten: `quotes[]`, `timestamps_penting[]`, `momen_menarik[]`

### story_brief.json
Per konten: `hook`, `story_flow[]`, `quote_placement[]`, `thumbnail_text`, `call_to_action`

### edit_plan.json
Per konten: `bagian_dipotong[]`, `bagian_dipertahankan[]`, `durasi_estimasi_final`, `retention_score`
