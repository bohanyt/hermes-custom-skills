# Hermes Session DB — Technical Reference

## File Layout

```
~/AppData/Local/hermes/
├── sessions/
│   ├── sessions.json           # Index: maps session_key → session_id + metadata
│   ├── session_<id>.json       # Per-session metadata (display_name, tokens, origin, timestamps)
│   ├── <id>.jsonl              # Actual chat messages (JSON Lines format)
│   └── request_dump_*.json     # Debug request dumps (safe to delete)
├── state.db                    # SQLite 3.x, WAL mode, FTS5 full-text search (~50MB+)
├── state.db-shm                # WAL shared memory (rebuildable)
├── state.db-wal                # WAL write-ahead log (rebuildable)
└── response_store.db           # Response cache SQLite DB
```

## sessions.json Structure

Top-level keys are session_key strings (format: `agent:<profile>:<platform>:<chat_type>:<chat_id>:<thread_id>`). Values contain: session_id, created_at, updated_at, display_name, platform, token counts, origin metadata.

## state.db (SQLite WAL)

- WAL mode: concurrent reads OK, writes must be serialized
- FTS5: full-text search over session messages
- Corruption recovery: stop Hermes, delete .shm and .wal, restart

## MSYS/Windows Compatibility

kill -0 and ps are unreliable on MSYS. Use file mtime age for stale lock detection.
stat -c '%Y' works on MSYS. Python os.path.getmtime() as fallback.
