---
title: Live2Video Pipeline v1.0→v1.2 — Full Development Session
sessions: [20260517_072358_13faf9, 20260514_151941_53c8b5, 20260517_064116_d20e7a, 20260517_045609_bd4738, 20260516_194454_0d4c87]
date: 2026-05-16 to 2026-05-17
platform: tui
model: openrouter/owl-alpha
total_messages: ~2272 (combined)
tags: [live2video, pipeline, development, v1.0, v1.1, v1.2]
---

# Live2Video Pipeline v1.0 → v1.2 — Full Development

**Date:** 2026-05-16 to 2026-05-17 | **Platform:** TUI | **Combined messages:** ~2272

> Sessions #1-5 are the same continuous development work, split across multiple TUI session restarts/clones. Combined into one summary.

## What Happened

Full-day development of Live2Video pipeline. Started from evaluating v1.0 results, went through complete architecture overhaul, and ended with v1.2_tes1 producing 22 video clips with unique 5C narrative scripts.

## Pipeline Evolution

### v1.0 (Initial)
- Chunk → Summarize → Merge → Orchestrate → Render
- Result: 5 clips, 8.7GB — too large (10min-1hr+ per clip)
- Issues: JSON parsing errors, data mining/storytelling failed, chunks too big

### v1.1 (First Rework)
- Added topic detection, trend research (YouTube Data API v3), storytelling 5C
- Result: 7-8 clips, ~1.4GB — better but topic detection only covered 20-33min of 2hr stream
- Issues: LLM rate limit, topic detection not granular, story titles generic ("GACHA")

### v1.2 (Final)
- Topic detection v5: rule-based grouping + LLM labeling (batch processing)
- Storyteller v4: strict context adherence, anti-generic titles
- Result: 22 clips, ~2.5GB, all titles unique, all 8 steps complete ✅

## Key Technical Fixes

| Issue | Fix |
|-------|-----|
| `.format()` crashes on JSON curly braces | `.replace()` + `[[placeholder]]` |
| SRT files not supported | `semanticchunker.py` auto-detects SRT/VTT |
| Timeout on 44 chunks | Increased from 120s → 600s → 900s |
| LLM rate limit | Dual API key (primary + secondary) |
| Topic detection too coarse | Rule-based Jaccard similarity + LLM labeling |
| Story titles generic ("GACHA") | Strict prompt + uniqueness requirements + examples |
| Output files scattered | Standardized `testing/v{version}_tes{N}/` structure |
| yt-dlp errors | Switched to YouTube Data API v3 |
| `work/final_cuts/` duplicate folder | Cleanup: move to `final_cuts/topics/`, delete duplicate |
| Video clips lost during cleanup | Restore from backup, re-render |

## User Preferences (Durable)

1. **Editor = human**: Agent only collects moments + labels + scripts, human edits
2. **Output = short clips + 5C narrative scripts ONLY** — no editing notes, sound effects, thumbnail text
3. **1 livestream → multiple videos** based on detected topics
4. **Video types**: storytime, reaction, shorts, tutorial, my experience, letsplay
5. **Granular topics** preferred over merged large ones
6. **Folder naming**: `testing/v{version}_tes{N}/` (e.g., `v1.2_tes1`)

## Folder Structure (Final)

```
hermes_live2video/
├── testing/
│   ├── v1.0_tes1/          ← 5 clips (old)
│   ├── v1.1_tes1/          ← 7 clips
│   ├── v1.1_tes2/          ← 22 clips
│   └── v1.2_tes1/          ← 22 clips (final)
├── raw_footages/
│   └── GTA Anime - NTE/    ← video.mp4 + .id.srt + metadata.json
└── hermes_skills/          ← all scripts
```

## Scripts (Final State)

- `semanticchunker.py` — SRT/VTT chunking
- `chunk_summarizer.py` — LLM summarization (900s timeout)
- `chunk_merger.py` — topic-based merging
- `topic_detector_v5.py` — rule-based + LLM label
- `trend_researcher_v4.py` — YouTube Data API v3
- `storyteller_v4.py` — 5C storytelling, strict prompt
- `technician.py` — ffmpeg video rendering
- `generate_report.py` — HTML progress report
- `pipeline_runner.py` — orchestrator
- `config_api.py` — API key management (dual profile)
- `brief2edit.py` — production brief → edit plan converter

## Skill Library Updates

Updated `live2video-pipeline` SKILL.md with:
1. Pipeline flow v1.2
2. Topic detection v5 approach (rule-based + LLM label)
3. Storyteller v4 strict prompt techniques
4. Known issues: API key expiration, timeout requirements
5. Version history: v1.0, v1.1, v1.2

New support files:
- `references/topic_detection_approaches.md` — evolution from v3 to v5
- `references/api_key_validation.md` — validation tests, common issues
- `scripts/retry_stories.py` — retry failed stories after rate limit

## Related

- [[live2video-pipeline]] — Full architecture
- [[live2video-detailed]] — Detailed technical knowledge
- [[live2video-troubleshooting]] — Problems & solutions evolution
- [[20260518-live2video-v1.3-final]] — Part 3: v1.3 5C long-form video (next iteration)
- [[copilot-m365-pipeline]] — Similar browser automation pattern
- [[html-context-preservation]] — HTML context strategy
- [[context-window-override]] — Gemma 4 context window override
- [[reject-cloakbrowser]] — Playwright over CloakBrowser

## Related Decisions

- [[reject-cloakbrowser]] — Playwright + cookie injection
- [[html-context-preservation]] — Save project context as HTML
- [[context-window-override]] — Gemma 4 context window override
- [[vision-model-selection]] — Nemotron Nano 12B VL

## Detail Files

Condensed conversation available in `sessions/detail/`:
- `20260517_072358_13faf9.md` — 513 messages (main session)
- `20260514_151941_53c8b5.md` — 508 messages (clone)
- `20260517_064116_d20e7a.md` — 476 messages (clone)
- `20260517_045609_bd4738.md` — 403 messages (clone)
- `20260516_194454_0d4c87.md` — 372 messages (clone)
