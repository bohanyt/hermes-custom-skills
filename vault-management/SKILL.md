---
name: vault-management
description: Umbrella skill for the Hermes Vault system. Covers vault query, update, capture, and audit workflows. Load this first for any vault-related work.
---

# Vault Management

The Hermes Vault is an indexed knowledge base at `C:\Users\MSI Thin 15\Documents\hermes-vault/`. It compiles knowledge from raw sessions into queryable markdown files.

## Sub-Skills

| Skill | When to Load |
|-------|-------------|
| `vault-query` | Before answering any question that might relate to past sessions, decisions, or known concepts |
| `vault-update` | End of significant session, new knowledge discovered, or cron job ingest |
| `vault-session-capture` | Manual end-of-session capture for important sessions |

## Quick Reference

**Vault path**: `C:\Users\MSI Thin 15\Documents\hermes-vault/`
**Raw sessions**: `~/AppData/Local/hermes/sessions/session_*.json`
**Extracted sessions**: `hermes-vault/sessions-raw/`
**Cron job**: `vault-session-ingest` — runs every 2h

## Audit Workflow

When the vault feels incomplete or broken, follow the audit procedure in `references/audit-procedure.md`.

Key steps: compare manifest vs actual files, find unprocessed sessions, filter trivial (<10 msgs), extract, summarize, rebuild manifest, expand thin concepts.

## Key Pitfalls

- **Don't create stub files**: Concepts must be >1500 bytes. If you can't fill it, it's not a concept yet
- **Don't trust manifest blindly**: Manifest can have stale entries. Always verify against actual files
- **Session JSONs can have different IDs**: `session_20260518_022514_020a94.json` may contain `session_id: 20260518_001332_0a5f19` (auto-resume). Check the `session_id` field, not just filename
- **Cron is backup, not primary**: Capture important sessions immediately via `vault-session-capture`. Cron fills gaps every 2h
- **Trivial sessions**: <10 messages → skip entirely. 10-30 messages with no new knowledge → 1-line in `_skipped.md`

## Response Style

Keep vault-related responses concise. User prefers short, direct answers — one sentence when possible, no lengthy explanations unless asked.
