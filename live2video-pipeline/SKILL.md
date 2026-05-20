---
name: live2video-pipeline
description: "End-to-end pipeline for converting YouTube livestreams into short video clips. Topic-first approach: chunk, summarize, detect topics, label video types, research trends, 5C storytelling, cut per topic. Produces granular 1-10min clips with narrative scripts."
---

# Live2Video Pipeline Skill

## Overview
Convert 1 YouTube livestream → multiple short video clips ready for upload.

**Location:** `scripts/` (this folder — portable, standalone)
**Config:** `.env` file in scripts/ (OPENROUTER_API_KEY, SECONDARY_API_KEY, YOUTUBE_API_KEY, SUMMARIZER_MODEL)

## Pipeline Flow

### v1.2+ (Topic-First Approach — RECOMMENDED)

```
URL/SRT → semanticchunker → chunk_summarizer → chunk_merger
  → topic_detector_v5 → trend_researcher_v4 → storyteller_v4 → technician --mode topics → final_cuts/topics/
```

Key difference: Instead of orchestrator → data_miner → storyteller → retention_architect → technician (which produced coarse 10min–1h45min clips), the topic-first approach:

1. Detects granular topics per chunk (each topic = 1–10 min)
2. Labels each topic with a video type (Raw Clip - Reaction, Storytime, Tutorial, etc.)
3. Researches trends per video type (10 top videos via YouTube Data API v3)
4. Creates 5C stories per topic (Character, Context, Conflict, Climax, Closure)
5. Cuts video per topic (short, labeled clips)

### Legacy Flow (v0.1 — coarse clips, NOT recommended)

```
URL → fetch_livestream → semanticchunker → chunk_summarizer → chunk_merger
  → orchestrator → brief2edit → technician → final_cuts/
```

### Step Reference (v1.2+)

| # | Script | Purpose | API | Input | Output |
|---|--------|---------|-----|-------|--------|
| 1 | fetch_livestream.py | Download video+SRT | None | URL | raw_footages/ |
| 2 | semanticchunker.py | Chunk SRT/VTT per 2.5min | None | .srt/.vtt | chunks/ |
| 3 | chunk_summarizer.py | Summarize each chunk | secondary | chunks.json | all_summaries.json |
| 4 | chunk_merger.py | Merge same-topic chunks | secondary | chunks.json | merged/ |
| 5 | topic_detector_v5.py | Rule-based grouping + LLM labeling | secondary | all_summaries.json | topics.json |
| 6 | trend_researcher_v4.py | Research top videos per video type via YouTube Data API v3 | YT API | topics.json | trend_research.json |
| 7 | storyteller_v4.py | 5C storytelling per topic (strict context adherence) | secondary | topics.json + trend | stories.json |
| 8 | technician.py --mode topics | Cut video per topic (max 300s, auto-split) | None | topics.json + video | final_cuts/topics/ |
| 9 | generate_report.py | Generate HTML report | None | all JSON | report.html |
| 10 | pipeline_runner.py | Run all steps, output to testing/v{version}_tes{N}/ | All | video_dir | testing/v{version}_tes{N}/ |

**Note:** Steps 3 and 4 order matters — summarize FIRST, then merge (merge needs summaries).

### Legacy Scripts (v0.1 — still available but produce coarse output)

| Script | Purpose | Issue |
|--------|---------|-------|
| orchestrator.py | Detect niche + plan content | Produces 1-5 coarse content ideas (10min–1h45min each) |
| data_miner.py | Extract quotes + timestamps | Works but output not used in v0.1.2+ |
| storyteller.py | Narrative + hook | Uses old format, not 5C |
| retention_architect.py | Edit pacing | Intermittent timeout on large briefs |
| brief2edit.py | Convert brief→edit_plan | Utility, still useful for regex extraction |

## Running the Pipeline

### Full pipeline (from URL):
```bash
cd hermes_skills
python fetch_livestream.py "URL"
python semanticchunker.py "path/to/video.id.srt"
python chunk_summarizer.py "path/to/chunks/chunks.json"
python chunk_merger.py "path/to/chunks/chunks.json"
python topic_detector_v5.py "path/to/chunks/all_summaries.json"
python trend_researcher_v4.py "path/to/chunks/topics.json"
python storyteller_v3.py "path/to/chunks/topics.json" "path/to/chunks/trend_research.json"
python technician.py "path/to/chunks/topics.json" --video "path/to/video.mp4" --mode topics
python generate_report.py "path/to/chunks"
```

### Skip download (existing files):
Start from semanticchunker.py with the .srt file path.

### Run full pipeline with auto-organization:
```bash
python pipeline_runner.py "path/to/video_dir"
```
This automatically creates `testing/v{version}_tes{N}/` and runs all steps. Output goes to `testing/v{version}_tes{N}/work/` and `testing/v{version}_tes{N}/work/final_cuts/topics/`.

**Folder naming:** `v1.1_tes1`, `v1.1_tes2`, etc. Version comes from `pipeline_runner.py` version variable. Test number auto-increments.

### Test outputs:
Move test outputs to `testing/tes<N>/` to keep `raw_footages/` clean:
```bash
mkdir -p testing/tes<N>
mv "raw_footages/<video>/final_cuts" "testing/tes<N>/final_cuts"
mv "raw_footages/<video>/chunks" "testing/tes<N>/chunks"
```

## Critical Pitfalls

### 1. Python .format() Curly Brace Conflict
**Problem:** Prompt strings containing JSON examples with `{` and `}` break `.format()` calls — Python tries to interpolate JSON braces as placeholders, causing `KeyError`.
**Fix:** Use `str.replace("[[placeholder]]", value)` instead of `.format()`. Use `[[double_braces]]` for placeholders in prompt strings to avoid ambiguity.
**Affected files (all fixed as of 2026-05-14):** orchestrator.py, chunk_merger.py, data_miner.py, storyteller.py, retention_architect.py, chunk_summarizer.py
**Pattern:**
```python
# BAD — breaks on JSON examples in prompt
ORCHESTRATOR_SYSTEM_PROMPT.format(content_types_guide=guide)  # KeyError on JSON braces

# GOOD — safe, use [[placeholder]] in prompt strings
ORCHESTRATOR_SYSTEM_PROMPT.replace("[[content_types_guide]]", guide)
```
**Also update prompt strings themselves:** Replace `{placeholder}` with `[[placeholder]]` in the prompt template strings so there's no ambiguity.

### 2. LLM Response JSON Parsing
**Problem:** LLM responses may not be valid JSON (truncated, markdown-wrapped, or with unescaped quotes inside string values). The Orchestrator saves raw response as a string in `raw_response` field, which may fail `json.loads()`.
**Fix:** Always save raw response + parsed result. Use regex fallback extraction when JSON parse fails. Add retry logic (3 attempts) for transient failures.
**Pattern in brief2edit.py:**
```python
import re
starts = re.findall(r'"start_time":\s*"([^"]+)"', raw)
ends = re.findall(r'"end_time":\s*"([^"]+)"', raw)
juduls = re.findall(r'"judul_saran":\s*"([^"]+)"', raw)
```
This extracts data even from malformed JSON strings. Keep `brief2edit.py` in hermes_skills/ as a utility.

### 3. SRT vs VTT Format
**Problem:** SRT uses commas in timestamps (`00:00:01,040`), VTT uses dots (`00:00:01.040`). SRT also has sequence numbers (e.g., `1`, `2`) as the first line of each block.
**Fix:** `semanticchunker.py` auto-detects by file extension (`.srt` vs `.vtt`). For SRT: normalizes commas→dots, skips sequence number lines.
**Status:** Fixed as of 2026-05-14 — both formats supported.

### 3b. Topic Detection — Rule-Based + LLM Labeling (v5)
**Problem:** Pure LLM topic detection (v3/v4) produces too few topics (5-8 from 44 chunks) because LLM context window limits how many chunks it can read at once. Batch processing helps but many batches fail silently.
**Fix:** `topic_detector_v5.py` uses rule-based keyword similarity grouping FIRST, then LLM only for labeling (not detection). This produces 20+ topics reliably.
**Pattern:**
1. Compute keyword overlap (Jaccard similarity) between adjacent chunks
2. Group chunks with similarity >= 0.15 OR time gap < 30s
3. Split groups > 300s into sub-groups
4. Call LLM per group for: label, video_type, engagement_score
**Result:** 22 topics from 44 chunks, 116 min covered (v1.1_tes2).

### 3c. 5C Storytelling — Strict Context Adherence (v4)
**Problem:** LLM generates generic/off-topic stories (e.g., all stories about "GACHA" regardless of topic). Story script doesn't match topic summary.
**Fix:** `storyteller_v4.py` uses extremely strict prompt:
- "Narasi HARUS 100% SESUAI dengan summary topik"
- "JANGAN mengarang cerita yang TIDAK ADA di summary"
- Include contoh benar/salah in prompt
- Judul must be UNIQUE per topic (no template like "[EMOSI] di [TEMPAT]!")
- Temperature 0.4 (lower = more focused)
**Result:** Stories are topic-specific but some still generic. May need even stricter prompt or few-shot examples.

### 3d. User's Core Output Requirements
**The user needs ONLY:**
1. Short video clips per topic (1-10 min, labeled with video type)
2. Compelling narrative script per topic (5C storytelling, conversational)
3. Clear labels per topic (video type, engagement score)

**The user does NOT need:**
- Editing notes (sound effects, zoom, transitions)
- Thumbnail design notes
- Multiple content types per topic
- Coarse 10min–1h45min clips

### 4. LLM Timeout on Long Context
**Problem:** `storyteller.py` and `retention_architect.py` timeout when processing large inputs. Default timeout was 120s.
**Fix:** Increased timeout to 600s in `config_api.py` (`urllib.request.urlopen(req, timeout=600)`).
**Additional mitigation:** For very long inputs (>10 min processing), split into per-content calls.
**Status:** Storyteller works with 600s timeout. Retention architect still intermittent on large briefs.

### 5. MSYS Path Conversion
**Problem:** MSYS bash converts `C:\Users\...` paths incorrectly.
**Fix:** Use Windows-style paths directly in Python, or use raw strings `r"..."`.

### 6. ffmpeg Not Found
**Problem:** ffmpeg must be in PATH or specified.
**Fix:** Install ffmpeg, add to PATH, or place ffmpeg.exe in hermes_skills/.

### 7. Rate Limiting (429) & API Key Separation
**Problem:** OpenRouter free tier has rate limits. Primary API key may hit limit quickly when running full pipeline.
**Fix:** Use TWO separate API keys:
- `OPENROUTER_API_KEY` (primary) — for orchestrator only (niche detection, production brief)
- `SECONDARY_API_KEY` — for ALL other calls (summarizer, topic detection, storytelling, data mining, trend research)

**All scripts use `secondary` profile by default** (updated 2026-05-14). Scripts have built-in retry (3x) and delay (3s between requests). Don't run multiple sessions on same API key.

**Config in .env:**
```
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxx        # Primary — orchestrator only
SECONDARY_API_KEY=sk-or-v1-yyyyyyyy         # Secondary — everything else
```

**In config_api.py:** Three profiles available: `primary`, `summarizer`, `secondary`. All map to `secondary` API key by default for safety.

### 8. Context Window / Token Management
**Problem:** Long conversations fill context window.
**Fix:** Save docs to files (pipeline_reference.txt + pipeline_guide.html). Start new session with `hermes chat --yolo`, read docs file.

### 9. Production Brief Format Variation
**Problem:** Orchestrator output format varies between runs — sometimes `raw_response` contains JSON string, sometimes already parsed with direct keys.
**Fix:** `brief2edit.py` handles both formats — check for `potensi_konten` key first, then try parsing `raw_response`.

### 10. yt-dlp Availability
**Problem:** `trend_researcher_v3.py` requires yt-dlp.exe in hermes_skills/ folder or PATH.
**Fix:** `trend_researcher_v3.py` has `find_yt_dlp()` that checks multiple locations. Download yt-dlp.exe and place in hermes_skills/ folder.
**Note:** Some YouTube searches return code 1 (video not available) — this is normal, the script handles it gracefully.

### 11. File Organization & raw_footages/ Hygiene
**Rule:** `raw_footages/` contains ONLY source files: `video.mp4`, `.srt`, `metadata.json`. NEVER leave intermediate outputs (chunks/, final_cuts/) in raw_footages/.

**Folder naming convention:** `testing/v{version}_tes{N}/` — e.g., `v1.1_tes1`, `v1.1_tes2`, `v1.2_tes1`.
- Version = pipeline version (update in `pipeline_runner.py` version variable)
- Test number = auto-increments per version

**Full structure:**
```
testing/v1.1_tes1/
├── work/
│   ├── chunks/              ← chunk .txt + .summary.txt + chunks.json + all_summaries.json
│   ├── chunks/merged/       ← merged chunks + merge_log.json
│   ├── final_cuts/topics/   ← video clips (.mp4) + render_log.json + report.html
│   ├── topics.json
│   ├── trend_research.json
│   ├── stories.json
│   └── metadata.json
└── final_cuts/              ← (optional copy of final output)
```

**Cleanup command (PowerShell):**
```powershell
Remove-Item -Recurse -Force "raw_footages/<video>/chunks","raw_footages/<video>/final_cuts"
```

## Output Format

### Video Clips
```
final_cuts/topics/
├── a_00h00m01s_00h05m30s.mp4   ← alphabet label, HHhMMmSSs format
├── b_00h05m31s_00h10m00s.mp4
├── c_00h10m01s_00h15m00s.mp4
├── ...
└── render_log.json
```

### JSON Files
- `metadata.json` — video info
- `chunks.json` — chunk metadata
- `all_summaries.json` — per-chunk summaries
- `topics.json` — detected topics with video types + engagement scores
- `trend_research.json` — trend analysis per video type
- `stories.json` — 5C narrative scripts per topic
- `render_log.json` — render log

## 5C Application: ENTIRE Video, Not Per-Clip

**CRITICAL RULE:** The 5C framework applies to the **full video** (10-15 min), NOT to individual topic clips. This is the single most important architectural decision in the pipeline.

**Wrong (v1.2):** 22 topics → 22 separate 5C scripts → repetitive, shallow, each clip is a mini-arc
**Right (v1.3+):** 1 video → 1 five-act narrative arc → topics are scenes within the arc

The 5C full-video arc:
1. **Context** (0-2 min): Opening, first reactions, setup — pulls from early stream clips
2. **Character** (2-4.5 min): World-building, lore, discoveries — pulls from middle stream clips
3. **Conflict** (4.5-7 min): Boss battles, struggles — pulls from action clips
4. **Choice** (7-10 min): Exploration, decisions — pulls from exploration clips
5. **Consequence** (10-12 min): Rewards, resolution, closing — pulls from end stream clips

Each act pulls 3-8 clips from different parts of the livestream. Total: 20-40 clips → 10-15 min final video. Write ONE continuous `full_script` (500-800 words, conversational Indonesian).

See `references/5c_storytelling.md` for detailed framework.

## Content Types (Video Type Labeling)

Each topic gets ONE video type label. The label determines how the clip should be edited:

| Video Type | Description | Typical Duration |
|------------|-------------|-----------------|
| Raw Clip - Reaction | Emotional reaction moments | 30s–3min |
| Raw Clip - Highlight | Epic gameplay moments | 30s–3min |
| Raw Clip - Funny | Funny/fail moments | 30s–2min |
| YouTube Shorts | Short, punchy content | 30s–60s |
| Storytime - Gaming | Personal experience narrative | 3–10min |
| Tutorial - Build With Me | Character/build guide | 3–10min |
| Video Essay - Opinion | Analysis/opinion | 3–10min |
| Rage / Funny Moments | Frustration + humor | 1–5min |

## .env Configuration

```
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxx
SECONDARY_API_KEY=sk-or-v1-yyyyyyyy
YOUTUBE_API_KEY=AIzaSyxxxxxxxx
SUMMARIZER_MODEL=openrouter/owl-alpha
```

## References

- `references/5c_storytelling.md` — 5C storytelling framework. **UPDATED v1.3:** Now covers full-video arc approach (5C for entire video, not per-clip), clip selection strategy, and video type → 5C role mapping
- `references/ffmpeg_extraction_guide.md` — **NEW:** ffmpeg clip extraction pitfalls: stream copy duration inaccuracy, disk space impact on seek performance, NVENC vs software encoding tradeoffs, timeout mitigation strategies
- `references/prompt_engineering.md` — `[[placeholder]]` + `.replace()` pattern for avoiding curly brace conflicts in prompt strings
- `references/brief2edit_pattern.md` — Regex fallback pattern for extracting data from malformed JSON in production brief
- `references/topic_detection_approaches.md` — Evolution of topic detection: v3 (LLM batch) → v4 (retry) → v5 (rule-based + LLM label). Includes algorithm and thresholds.
- `references/api_key_management.md` — Dual API key setup, rate limit handling, and expiration monitoring
- `references/api_key_validation.md` — **NEW**: Validation tests for YouTube Data API v3 and OpenRouter keys, common issues (`\\_` escape, 401, 429), dual key strategy
- `scripts/retry_stories.py` — **NEW**: Retry script for failed stories (429 rate limit). Run after storyteller timeout to retry only failed entries.

## Vault Integration

The Live2Video pipeline knowledge is stored in the Hermes Vault at `C:\Users\MSI Thin 15\Documents\hermes-vault/`. When working on pipeline tasks:

1. **Before starting**: Check `concepts/live2video-pipeline.md` and `sessions/` for recent changes
2. **After significant changes**: Update the vault with new learnings, pitfalls, and version updates
3. **Cross-reference**: Link to related concepts like `[[copilot-m365-pipeline]]` and `[[html-context-preservation]]`

## Known Issues (as of 2026-05-18, v1.3-dev)

### CRITICAL: 5C Applies to ENTIRE Video, Not Per-Clip
**Problem:** v1.2 approach applied 5C storytelling per topic/clip (22 topics → 22 separate 5C scripts). This produced repetitive, shallow scripts where each clip had its own mini-arc. Conflict/closure sections were nearly identical across clips.

**Correct approach (v1.3+):** 5C is the framework for the **entire video** (10-15 min), not individual clips:
- **Context** = Opening/setup (first 2 min of video, not per-clip)
- **Character** = World-building & discovery (next 2-3 min)
- **Conflict** = Main struggle/boss fight (next 2-3 min)
- **Choice** = Exploration & decisions (next 2-3 min)
- **Consequence** = Resolution & rewards (final 2-3 min)

Each "act" pulls clips from **different topics** across the livestream. Topics are scenes within the 5C arc, NOT standalone videos. One livestream → ONE satisfying 10-15 min video with a complete narrative arc.

**Script structure:** Write ONE `full_script` for the entire video that flows naturally across all acts. The script should feel like one continuous YouTuber narration, not 22 separate mini-scripts.

### ffmpeg Stream Copy Duration Inaccuracy
**Problem:** Using `-c:v copy -c:a copy` to extract clips from large source files (5.7GB+) produces clips with wildly inaccurate durations. A 60s clip can become 20-40 minutes long because stream copy snaps to the nearest keyframe, which may be far from the requested start time.

**Fix:** Always re-encode clips (`-c:v libx264` or `-c:v h264_nvenc`) for accurate duration. Stream copy is only safe for small files (< 1GB) or when exact duration doesn't matter.

### Disk Space & ffmpeg Seek Performance
**Problem:** When disk is >95% full, ffmpeg seek on large files (5GB+) becomes extremely slow. `-ss` before `-i` keyframe seek can take 10+ minutes per clip, causing timeouts.

**Fix:** 
1. Check disk space before starting extraction: `df -h` or check free space
2. Keep at least 10-15% disk free for temp files and smooth I/O
3. If disk is full, clean up old test outputs first: `rm -rf testing/v{N}_tes{M}/work/`
4. As last resort, pre-process source to smaller file: re-encode to 720p with lower bitrate before extracting

### NVENC Encoding Speed
**Problem:** NVENC on RTX 3050 laptop encodes at ~3 fps for 1080p→1080p, making pre-processing of 2h source video impractical (would take 2+ hours).

**Workaround:** For clip extraction, use `-c:v h264_nvenc -preset p1 -rc cbr -b:v 8M` which is faster than software encoding. But for full video pre-processing, consider doing it overnight or using a machine with a stronger GPU.
- ~~config_api.py timeout too short~~ → Fixed: timeout 120s → 600s
- ~~Coarse clips (10min–1h45min)~~ → Fixed: topic-first pipeline produces granular 1-10min clips
- ~~Files scattered everywhere~~ → Fixed: pipeline_runner.py auto-organizes into testing/v{version}_tes{N}/
- ~~Single API key rate limit~~ → Fixed: dual key setup (primary + secondary)
- ~~yt-dlp unreliable for trend research~~ → Fixed: trend_researcher_v4.py uses YouTube Data API v3
- ~~Story titles not unique~~ → Fixed: storyteller_v4 strict prompt enforces unique, topic-specific titles. v1.2_tes1: all 22/22 titles unique.
- **API key expiration**: Both PRIMARY and SECONDARY API keys can expire (401 User not found). Always verify keys work before running full pipeline. User has 5 API keys configured — test all of them and use working ones.
- **API key `\\\\_` escape in .env**: When pasting API keys into .env, ensure backslash escapes (`\\\\_`) are NOT included. Backslash escapes cause 401 errors.
- **ffmpeg extraction from AV1 sources**: Source videos downloaded from YouTube may use AV1 codec. ffmpeg software decode of AV1 is extremely slow and will timeout on large files. **Fix:** Use `-hwaccel cuda -hwaccel_output_format cuda` flags for hardware-accelerated AV1 decode. This reduces extraction time from 10+ min to ~15-40s per clip. Without hardware decode, ffmpeg will consistently timeout on clips from AV1 sources. Check codec with `ffprobe -show_entries stream=codec_name`. See `references/ffmpeg_extraction_guide.md` for full command reference.
- **Use `-t` instead of `-to` for clip extraction**: Using `-t DURATION` (duration in seconds) is more reliable than `-to END_TIME` for accurate clip boundaries. `-to` can produce clips with incorrect durations due to keyframe alignment. Example: `-t 50` for a 50-second clip instead of `-to 00:03:30`.
- **Windows file locking after ffmpeg crashes**: When ffmpeg is killed or crashes, output files may remain locked by the process, causing `PermissionError: [WinError 32]`. Fix: run `taskkill /F /IM ffmpeg.exe` before retrying. If files are still locked, rename them and extract with new filenames.
- **MKV remux doesn't help AV1 decode**: Remuxing MP4→MKV (`-c:v copy -c:a copy`) is fast (~130x speed) but does NOT improve AV1 decode performance. The bottleneck is the codec, not the container. Hardware decode (`-hwaccel cuda`) is the only fix.
- **Concatenation of many clips**: 41 clips via concat demuxer works but takes ~5-10 minutes. Output file grows gradually — don't assume it's stuck if size is increasing. Use `-preset p3` for final concat (better quality than `p1`).
- **Stream copy duration inaccuracy**: `-c:v copy` produces clips with wildly inaccurate durations on large files. Always re-encode for accurate clip boundaries.
- **Disk space affects ffmpeg seek**: Disk >95% full causes severe I/O degradation. Keep 10-15% free before large video operations.
- **Story script quality**: v1.2_tes1 showed some stories still have repetitive conflict/closure sections. Consider few-shot examples or even stricter prompt for next version.
- **Rate limit bottleneck**: 22 topics × ~45s = ~16min. Rate limits still cause intermittent failures. Add 2-3s delay between storyteller requests to reduce 429 errors. With 5 API keys available, distribute load across keys.
- **Render time**: 22 clips from 5.7GB video takes ~10 minutes.
- **Duplicate `work/final_cuts/` folder**: After render, MOVE contents to `final_cuts/topics/` and DELETE `work/final_cuts/` to avoid duplicates.
- **Folder structure standardization**: All versions use `final_cuts/topics/`. When renaming: `mv final_cuts/chunks final_cuts/topics`.
- **retention_architect.py**: Intermittent timeout on large briefs. Not used in v1.2+ pipeline.
- **5 API keys available**: User has 5 OpenRouter API keys configured. Use them for fallback/rate-limit handling. Test all keys before running pipeline — some may be expired.

## Version History

| Version | Date | Changes |
|---------|------|---------|
| v0.1 | 2026-05-14 | Initial pipeline: 13 scripts, basic flow |
| v0.1.1 | 2026-05-14 | Fixed all `.format()` → `.replace()`, timeout 120→600s, SRT parser, brief2edit.py |
| v0.1.2 | 2026-05-15 | Topic-first pipeline: topic_detector_v3, storyteller_v2 (5C), trend_researcher_v3, technician --mode topics, generate_report.py, pipeline_runner.py |
| v1.0 | 2026-05-15 | topic_detector_v5 (rule-based+LLM), trend_researcher_v4 (YouTube API v3), storyteller_v3. Tested: 44→22 topics→20 stories→22 clips (~944MB) |
| v1.1 | 2026-05-15 | storyteller_v4 strict context. v1.1_tes2: 22 topics, 116min covered. Issues: title overlap, story off-topic |
| v1.3 | 2026-05-18 | **5C applies to ENTIRE video, not per-clip.** One 10-15 min video with full narrative arc. ffmpeg extraction guide added. Stream copy pitfall documented. Known issues: disk space affects seek, NVENC slow on RTX 3050. |
