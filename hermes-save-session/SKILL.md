---
name: hermes-save-session
description: Force-save Hermes session DB. Use when you want to manually flush/save the session database to disk, especially before closing a terminal or after important conversations. Prevents data loss.
---

# Hermes Save Session

Force-save the Hermes session database to disk. Flushes WAL (Write-Ahead Log) and verifies DB integrity.

## When to Use

- Before closing a terminal window
- After an important conversation you don't want to lose
- When switching between terminals (multi-session setup)
- When you suspect the DB hasn't been saved recently

## How to Use

### From Hermes Chat

Tell Hermes:
> "save the session DB" or "flush the DB" or "save my session"

Hermes will run the save script and report the result.

### From Terminal

```bash
bash ~/Documents/hermes-tools/hermes-save-db.sh
```

With integrity check:
```bash
bash ~/Documents/hermes-tools/hermes-save-db.sh --verify
```

## What It Does

1. Checks `state.db` exists and reports size
2. Checks WAL file for uncommitted writes
3. Runs `PRAGMA wal_checkpoint(TRUNCATE)` to flush WAL → main DB
4. Optionally verifies DB integrity
5. Reports session count

## Requirements

- `sqlite3` command (install via `pacman -S sqlite3` on MSYS2, or `choco install sqlite` on Windows)
- Without sqlite3, the script still works but can only report status (WAL flush happens automatically on Hermes exit)

## Multi-Session Note

When running multiple Hermes terminals:
1. **Close Hermes gracefully** (type `exit` or Ctrl+D) — this auto-saves
2. **Then run save script** on any terminal to verify
3. The lock hook (`hermes-lock-hook.sh`) prevents concurrent writes

## Files

- Script: `~/Documents/hermes-tools/hermes-save-db.sh`
- Lock hook: `~/Documents/hermes-tools/hermes-lock-hook.sh`
- DB: `~/AppData/Local/hermes/state.db`
