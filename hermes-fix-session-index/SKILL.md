---
name: hermes-fix-session-index
description: Fix missing session index entries. Use when sessions created via hermes.exe (CLI/PowerShell) don't appear in session_search. Scans session JSON files and adds missing entries to sessions.json index.
---

# Hermes Fix Session Index

Fix the bug where sessions created via `hermes.exe` (CLI/PowerShell) are saved as JSON files but NOT indexed in `sessions.json`, making them invisible to `session_search`.

## When to Use

- After running Hermes via PowerShell / `hermes.exe` directly
- When a session doesn't appear in `session_search` but the JSON file exists
- Periodically as maintenance (or use the cron job for automatic fixing)

## How to Use

### From Hermes Chat

Tell Hermes:
> "fix session index" or "index my sessions" or "sessions not showing up"

Hermes will run the fix script and report results.

### From Terminal

```bash
python ~/Documents/hermes-tools/hermes-fix-session-index.py
```

Dry run (preview only):
```bash
python ~/Documents/hermes-tools/hermes-fix-session-index.py --dry-run
```

Verbose:
```bash
python ~/Documents/hermes-tools/hermes-fix-session-index.py --verbose
```

## What It Does

1. Scans `~/.hermes/sessions/session_*.json` files
2. Compares against `sessions.json` index
3. Adds missing entries with proper metadata
4. Rebuilds FTS5 search index in `state.db`
5. Reports: added, already indexed, errors

## Automatic Fix (Cron Job)

For hands-free fixing, set up a cron job:

```
hermes cron create --schedule "0 * * * *" --prompt "Run: python ~/Documents/hermes-tools/hermes-fix-session-index.py"
```

This runs every hour and auto-fixes any new unindexed sessions.

## Known Bug

This is a workaround for a Hermes v0.14.0 bug where CLI sessions (via `hermes.exe`) are not automatically indexed. See GitHub issue: [link to be added after submission]

## Files

- Script: `~/Documents/hermes-tools/hermes-fix-session-index.py`
- Sessions index: `~/AppData/Local/hermes/sessions/sessions.json`
- State DB: `~/AppData/Local/hermes/state.db`
