---
title: Vault Setup & Architecture Discussion
sessions: [20260517_090851_060c8d, 20260517_101529_dd8116, 20260517_102333_35c075, 20260517_110322_767eb1, 20260517_122625_013605, 20260517_132345_d863b4, 20260517_133734_5cc347, 20260517_153648_a778d7, 20260517_163025_9c2c63, 20260517_165137_810f93]
date: 2026-05-17
platform: cli
model: openrouter/owl-alpha
total_messages: ~1500 (combined)
tags: [vault, architecture, setup, memory, seo-memory]
---

# Vault Setup & Architecture Discussion

**Date:** 2026-05-17 | **Platform:** CLI | **Combined messages:** ~1500

## What Happened

Full-day discussion and implementation of the Hermes Vault system. From initial concept ("SEO memory") to full implementation with skills, batch ingest, and cron job.

## Vault Concept: "SEO Memory"

**Problem:** Hermes memory tool limited to 2200 chars. Session search is linear scan, inefficient for 100+ sessions. Multi-session (different API keys) has no shared memory.

**Solution:** Knowledge base as extended memory — indexed, queryable, concurrent-safe.

**Principles:**
- **Compile, don't retrieve** — knowledge is pre-compiled, not re-derived
- **Index first** — always scan index before opening files
- **File-per-session** — no overwrites, append-only
- **Concurrency safe** — `.lock` file mechanism

## Vault Architecture

```
Sessions (raw JSON)
    ↓ Phase 1: Extract
sessions/detail/ (condensed markdown)
    ↓ Phase 2: AI Analysis
sessions/ (session summaries)
    ↓ Phase 3: Knowledge Extraction
concepts/ | decisions/ | people/ | _meta/
```

**Query flow:**
1. Scan `index.md` (lightweight)
2. Open relevant topic files
3. Drill to `sessions/detail/` if needed
4. Last resort: raw JSON in `AppData/Local/hermes/sessions/`

## Key Decisions

1. **No Obsidian GUI** — custom markdown implementation
2. **Vault path**: `C:\Users\MSI Thin 15\Documents\hermes-vault/`
3. **Multi-session safety**: File-per-sessions, append-only index, `.lock` file
4. **Single model (owl-alpha)** with 5 API keys for fallback
5. **Scope**: Hermes-only for now (Phase 1), multi-agent later (Phase 2)

## Skills Created

- `vault-query` — Instructions for scanning index.md before answering
- `vault-update` — Instructions for extracting session content and writing to vault

## Scripts Created

- `scripts/phase1_extract.py` — Extract clean messages from JSON session files
- `scripts/phase2a_condense.py` — Generate condensed views for AI analysis
- `scripts/phase3_check_new.py` — Detect and process new sessions
- `scripts/extract_knowledge.py` — Extract key info from condensed files
- `scripts/analyze_sessions.py` — Group sessions by topic

## Cron Job

- `vault-session-ingest` — Runs every 6 hours
- Auto-detects new sessions, runs Phase 1+2a, AI summarizes

## Folder Convention

```
hermes-vault/
├── index.md              # master index + quick nav
├── concepts/             # structured knowledge (11 files)
├── decisions/            # decisions made (6 files)
├── people/               # people discussed (1 file)
├── sessions/             # session summaries (per topic)
│   └── detail/           # condensed conversations (drill-down)
├── scripts/              # automation scripts (5 files)
└── _meta/
    ├── knowledge-map.md  # knowledge graph
    ├── hermes-patterns.md # patterns & pitfalls
    ├── taxonomy.md
    └── agents.md
```

## Related

- [[vault-pattern]] — Vault architecture pattern
- [[seo-memory]] — SEO memory concept
- [[concurrency-lock]] — Multi-session safety
- [[custom-vault-over-framework]] — Why custom, not obsidian-wiki

## Detail Files

- `sessions/detail/20260517_090851_060c8d.md` — 263 messages, initial concept
- `sessions/detail/20260517_101529_dd8116.md` — 65 messages, architecture
- `sessions/detail/20260517_102333_35c075.md` — 88 messages, implementation
- `sessions/detail/20260517_110322_767eb1.md` — 119 messages, skills
- `sessions/detail/20260517_122625_013605.md` — 177 messages, batch ingest
- `sessions/detail/20260517_132345_d863b4.md` — 217 messages, testing
- `sessions/detail/20260517_133734_5cc347.md` — 230 messages, refinement
- `sessions/detail/20260517_153648_a778d7.md` — 264 messages, cron job
- `sessions/detail/20260517_163025_9c2c63.md` — 32 messages, lint
- `sessions/detail/20260517_165137_810f93.md` — 38 messages, final
