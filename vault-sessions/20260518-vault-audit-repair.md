---
title: Vault Audit & Repair — Complete System Overhaul
sessions: [20260518_205144_df9b4c, 20260518_204128_4d1236]
date: 2026-05-18
platform: cli
model: openrouter/owl-alpha
total_messages: ~100 (combined)
tags: [vault, audit, repair, skills, cron, backfill]
---

# Vault Audit & Repair — Complete System Overhaul

**Date:** 2026-05-18 20:55 | **Platform:** CLI | **Messages:** ~100

## What Happened

Full audit of the Hermes Vault system. User felt the vault wasn't capturing all knowledge — concepts/decisions/people felt thin, especially for May 18 sessions. Audit revealed systemic issues and all 4 were fixed.

## Problems Found

1. **Manifest mismatch**: 45 entries in manifest but only 14 had actual summary files. 31 stale entries with no matching files.
2. **Cron job broken**: Skills `vault-query` and `vault-update` referenced by cron didn't exist in `~/AppData/Local/hermes/skills/`.
3. **No end-of-session capture**: No mechanism to auto-extract knowledge when a session ends.
4. **Thin concept files**: 4 concepts were 800-1000 bytes — too shallow to be useful knowledge.
5. **May 18 sessions not in manifest**: 14 sessions from May 18 weren't tracked.

## Fixes Applied

### B — Cron Job Repair
- Created `vault-query` skill: query protocol for the vault (index → concepts → decisions → sessions → detail → raw)
- Created `vault-update` skill: write protocol for extracting and storing knowledge
- Updated cron job: schedule 6h → 2h, attached skills, improved prompt

### A — Session Capture Skill
- Created `vault-session-capture` skill: manual trigger at end of significant sessions
- Cron job serves as automatic backup (every 2h)
- Both use the same `vault-update` protocol

### C — Backfill
- Extracted all 130 sessions to `sessions-raw/`
- Analyzed May 18 sessions: 2 already had summaries, 4 trivial (<10 msgs), rest were auto-resumes
- Rebuilt manifest from scratch: 14 summaries, 13 concepts, 6 decisions, 1 person
- Removed 31 stale manifest entries

### D — Concept Expansion
- `vault-pattern.md`: 1247B → 2741B (full architecture explanation)
- `seo-memory.md`: 839B → 2005B (SEO analogy + query flow)
- `concurrency-lock.md`: 810B → 1426B (file-based locking implementation)
- Fixed broken wikilink in knowledge-map.md

## Key Learnings

- **Manifest should track summary files, not individual session IDs** — many sessions get combined into one summary
- **Session JSON files can have different session_id than filename** — auto-resume sessions reuse the original session_id
- **request_dump_*.json files are NOT sessions** — they're request dumps, actual sessions are session_*.json
- **Cron deliver: "local" means no delivery** — output is saved only, not sent anywhere

## Related

- [[vault-pattern]] — Vault architecture
- [[seo-memory]] — SEO memory concept
- [[concurrency-lock]] — Multi-session safety

## Detail Files

- `sessions/detail/20260518_205144_df9b4c.md` — this session (condensed)
