---
title: obsidian-wiki Evaluation & Hermes Update
session_id: 20260517_081135_d6d939
date: 2026-05-17
platform: tui
model: openrouter/owl-alpha
messages: 21
tags: [obsidian-wiki, hermes-update, session-management, karpathy]
---

# obsidian-wiki Evaluation & Hermes Update

**Date:** 2026-05-17 | **Platform:** TUI | **Messages:** 21

## What Happened

User asked about updating Hermes Agent and whether obsidian-wiki (Ar9av/obsidian-wiki) could be installed. Also discussed session management (clone/resume) and WhatsApp setup.

## obsidian-wiki Evaluation

**What it is:** Knowledge management system inspired by Karpathy's LLM Wiki pattern. Instead of asking LLM same questions repeatedly (or RAG every time), compile knowledge once into interconnected markdown files and keep them current. Obsidian is the viewer, LLM is the maintainer.

**Key features:**
- 23+ skills for wiki management (ingest, query, lint, rebuild, export, etc.)
- Multi-agent support (Claude Code, Cursor, Windsurf, Codex, Gemini CLI, Hermes, OpenClaw, etc.)
- Delta tracking — only processes new/changed sources
- Project-based organization
- Archive and rebuild capability
- Multi-agent ingest (Claude, Codex, Hermes, OpenClaw history)
- Cross-agent targeted search (`/wiki-claude`, `/wiki-codex`, `/wiki-hermes`)
- Audit and lint (orphaned pages, broken links, stale content)
- Automated cross-linking with `[[wikilinks]]`
- Tag taxonomy with controlled vocabulary
- Provenance tracking (extracted vs inferred vs ambiguous)
- Multimodal sources (screenshots, whiteboard photos)
- Graph export (JSON, GraphML, Neo4j, HTML)
- Tiered retrieval (index-first, then page bodies)
- QMD semantic search (optional)

**How it works (4 stages):**
1. **Ingest** — Read source material (markdown, PDFs, JSONL, text, images)
2. **Extract** — Pull out concepts, entities, claims, relationships
3. **Resolve** — Merge against existing wiki, update or create pages
4. **Schema** — Emergent schema, stays consistent as you add more

**Install:**
```bash
npx skills add Ar9av/obsidian-wiki
# or
git clone https://github.com/Ar9av/obsidian-wiki.git
cd obsidian-wiki && bash setup.sh
```

**Decision:** Not adopted — user already building custom vault system (this vault). obsidian-wiki requires Obsidian GUI which user doesn't use.

## Hermes Agent Update

**Current version:** v0.13.0 (386 commits behind)

**Update command:**
```bash
hermes update
```

## Session Management

**Clone vs Resume:**
- **Resume** → Same conversation, shared history, background processes still accessible
- **Clone** → Fresh conversation, separate context, background processes from old session don't carry over

**Best practice:** Close idle sessions to save resources and avoid API key conflicts.

## WhatsApp Setup

**How it works:**
1. Scan QR code in terminal/gateway
2. Open WhatsApp → Settings → Linked Devices → Link a Device
3. Chat to the bot number → messages go to Hermes gateway → Hermes processes → replies via WhatsApp

**Troubleshooting:**
- If messages don't get replies: check gateway connection, verify bot number
- WhatsApp is just a channel — same tools and memory as other sessions

## Related

- [[vault-pattern]] — Custom vault system (alternative to obsidian-wiki)
- [[custom-vault-over-framework]] — Decision to build custom instead of using obsidian-wiki
- [[multi-session-management]] — Session clone/resume behavior
- [[andrej-karpathy]] — LLM Wiki pattern that inspired obsidian-wiki

## Detail Files

- `sessions/detail/20260517_081135_d6d939.md` — 21 messages
