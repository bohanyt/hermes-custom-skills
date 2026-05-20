# Skills Maturity Report — FINAL
# Generated: 2026-05-20

## Maturity Levels

- **PRODUCTION**: Tested, complete scripts, real output produced, daily driver
- **FUNCTIONAL**: Works but not fully tested, or partial implementation
- **REFERENCE**: Documentation/SOP only, no runnable code
- **STUB**: Placeholder, incomplete, or broken

---

## PRODUCTION (9 skills)

| Skill | Evidence |
|-------|----------|
| **storytime-pipeline** | topic_chunker.py (714 lines, syntax OK). Tested: 1444 SRT → 528 cleaned → 40 chunks → 1 storytime. Full SOP + working script. |
| **hermes-fix-session-index** | hermes-fix-session-index.py (syntax OK). Fixes real Hermes v0.14.0 bug. |
| **hermes-multi-session** | 3 shell scripts (all syntax OK). Daily driver. Scripts: lock, safe, multi-launch. |
| **hermes-save-session** | hermes-save-db.sh (syntax OK). WAL flush script. |
| **vault-query** | Functional query protocol. |
| **vault-update** | Complete write protocol with concurrency safety. |
| **vault-session-capture** | Clear trigger conditions and steps. |
| **vault-management** | Umbrella + audit workflow. |
| **context-delegation** | Complete delegation patterns + model fallback chain. |

## FUNCTIONAL (5 skills)

| Skill | Evidence | Notes |
|-------|----------|-------|
| **live2video-pipeline** | 22 active Python scripts (all syntax OK) + 17 outdated versions. SKILL.md 382 lines with version history to v1.3. | Scripts now included in export (scripts/). Self-contained and portable. |
| **hermes-python-pipeline** | References pipeline-scripts.md. | Coding pattern reference. Scripts are in live2video-pipeline/scripts/. |
| **content-pipeline-builder** | References 9 scripts + 2 reference docs. | Architecture reference. Scripts are in live2video-pipeline/scripts/. |
| **browser-automation-enterprise** | 639 lines SKILL.md, 5 references, 1 template (copilot_m365_bot.py). | Comprehensive but no evidence of real-world testing. |
| **hermes-tools/** | 5 shell scripts (all syntax OK), 1 Python script. | Functional. Some are "example" files. |

## REFERENCE (4 skills)

Documentation-only SOPs. No code needed. Complete as-is.

- **caveman** — Communication protocol
- **handoff** — Document format specification
- **grill-me** — Interview framework
- **improve-codebase-architecture** — Analysis framework with glossary

## STUB (1 skill)

- **zoom-out** — Only 29 lines. Minimal. Needs expansion (examples, pitfalls, detailed process).

---

## Key Findings

### 1. live2video-pipeline is NOW self-contained
Previously referenced external scripts in Documents/hermes_live2video/hermes_skills/. Now all 22 active scripts + 17 outdated versions are included in export/scripts/.

### 2. content-pipeline-builder + hermes-python-pipeline are reference-only
They describe architecture and coding patterns but don't include scripts. The actual scripts live in live2video-pipeline/scripts/.

### 3. Truly portable (self-contained) skills:
- storytime-pipeline (has topic_chunker.py)
- hermes-multi-session (has all scripts)
- hermes-save-session (has script)
- hermes-fix-session-index (has script)
- live2video-pipeline (has all 22 scripts)
- vault-* (pure SOP)
- context-delegation (pure SOP)
- caveman, handoff, grill-me, improve-codebase-architecture (pure SOP)
- browser-automation-enterprise (has template)
- zoom-out (minimal but complete as prompt)

### 4. Scripts inventory (live2video-pipeline/scripts/):

| Script | Purpose | Lines |
|--------|---------|-------|
| pipeline_runner.py | Orchestrator (entry point) | ~200 |
| srt_cleaner.py | Clean auto-generated SRT | ~100 |
| topic_chunker.py | Chunk + label transcript | 714 |
| pipeline_cutter.py | Cut video per label | ~150 |
| storytime_scanner.py | Scan storytime (standalone) | ~100 |
| storytime_keywords.json | Keyword config | JSON |
| semanticchunker.py | Semantic chunking (legacy) | ~200 |
| topic_detector_v5.py | Topic detection (legacy, needs API) | ~300 |
| storyteller_v4.py | Storyteller (legacy, needs API) | ~400 |
| technician.py | Video processing (legacy) | ~200 |
| fetch_livestream.py | Download video + SRT | ~150 |
| chunk_summarizer.py | Summarize chunks (needs API) | ~200 |
| chunk_merger.py | Merge same-topic chunks | ~150 |
| trend_researcher_v4.py | YouTube trend research | ~200 |
| data_miner.py | Extract quotes/timestamps | ~150 |
| orchestrator.py | Production brief (legacy) | ~300 |
| retention_architect.py | Edit pacing (legacy) | ~200 |
| generate_report.py | HTML report generator | ~100 |
| retry_stories.py | Retry failed stories | 62 |
| config_api.py | API config helper | ~150 |
| yt-dlp.exe | YouTube downloader | binary |

Plus 17 files in outdated/ (old versions for reference).
