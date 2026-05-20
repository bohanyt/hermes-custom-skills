---
name: hermes-multi-session
description: Multi-terminal Hermes session manager with per-instance API keys, DB lock/queue, and shared vault. Use when running multiple Hermes terminals simultaneously with different API keys but one shared session DB and vault.
---

# Hermes Multi-Session Manager

Run multiple Hermes terminals simultaneously with different API keys, shared session DB, and automatic lock/queue to prevent DB corruption.

## Architecture

```
Terminal 1 (key A) ──┐
Terminal 2 (key B) ──┼──→ [lock/queue] → state.db (shared) → vault (shared)
Terminal 3 (key C) ──┘
```

- Each terminal uses a different API key (rate limit distribution)
- All terminals write to the same session DB and vault
- File-based lock prevents concurrent writes (DB corruption protection)
- Stale lock detection (configurable timeout, default 5 min)

## Files

| File | Purpose |
|------|---------|
| `hermes-new` | **Easiest way**: spawn new terminal, paste API key, done |
| `hermes-session-lock.sh` | Lock/unlock/status/wait/alert for DB access |
| `hermes-safe.sh` | Wrapper: auto lock/unlock around Hermes |
| `hermes-multi.sh` | Launch multiple terminals with different keys |
| `hermes-keys.conf` | API key config (one per instance) |

## Quick Start — The Easy Way

Just run `hermes-new` from any terminal:

```bash
hermes-new
```

It will:
1. Ask you to paste an API key (or use existing `$OPENROUTER_API_KEY`)
2. Open a new terminal window
3. Auto-acquire DB lock → start Hermes → auto-release lock on exit

That's it. DB and vault are shared automatically.

You can also name the instance:
```bash
hermes-new my-session-name
```

## Quick Start — The Full Way

### 1. Setup

Copy all script files to a directory (e.g., `~/Documents/hermes-tools/`):

```bash
mkdir -p ~/Documents/hermes-tools
# Copy hermes-session-lock.sh, hermes-safe.sh, hermes-multi.sh
chmod +x ~/Documents/hermes-tools/*.sh
```

### 2. Create API Key Config

Create `~/.hermes-keys.conf`:

```bash
# terminal-1
sk-or-v1-your-first-key-here

# terminal-2
sk-or-v1-your-second-key-here

# terminal-3
sk-or-v1-your-third-key-here
```

Format: `# instance_name` on one line, API key on the next line.

### 3. Launch Multi-Terminal

```bash
cd ~/Documents/hermes-tools
bash hermes-multi.sh ~/.hermes-keys.conf
```

This opens each instance in a new terminal window with its own API key.

### 4. Manual Single Instance

If you want to launch just one instance with lock protection:

```bash
export OPENROUTER_API_KEY="sk-or-v1-your-key"
bash ~/Documents/hermes-tools/hermes-safe.sh my-instance
```

## Lock Management

### Check Status

```bash
bash hermes-session-lock.sh status
```

Output:
- `UNLOCKED — DB is free` — safe to start
- `LOCKED by 'terminal-1'` — instance is saving, wait
- `STALE LOCK from 'terminal-1'` — holder died, safe to take over

### Manual Lock/Unlock

```bash
# Acquire lock
bash hermes-session-lock.sh lock my-instance

# Release lock
bash hermes-session-lock.sh unlock my-instance

# Wait for lock (then acquire)
bash hermes-session-lock.sh wait my-instance 300

# Show current alert
bash hermes-session-lock.sh alert
```

### Force Start (Skip Lock)

```bash
bash hermes-safe.sh my-instance --force
```

WARNING: Only use `--force` if you're sure no other instance is writing. Risk of DB corruption.

## How Lock Works

1. **Lock file**: `~/.hermes-locks/db.lock` contains instance name
2. **Stale detection**: Lock older than `LOCK_MAX_AGE_SEC` (default 300s = 5min) is considered stale
3. **Auto-cleanup**: Stale locks are automatically taken over
4. **Trap cleanup**: `hermes-safe.sh` releases lock on EXIT/INT/TERM (even Ctrl+C)

## Configuration

Environment variables:

| Variable | Default | Purpose |
|----------|---------|---------|
| `HERMES_LOCK_DIR` | `~/.hermes-locks` | Lock file directory |
| `LOCK_MAX_AGE_SEC` | `300` | Max lock age before stale (seconds) |
| `OPENROUTER_API_KEY` | (from env) | Per-instance API key |

## Shared Vault Setup

To use the same vault across all instances, ensure all Hermes configs point to the same vault path. In each instance's `config.yaml`:

```yaml
vault:
  path: C:\Users\MSI Thin 15\Documents\hermes-vault
```

Or set via Hermes config command:
```bash
hermes config set vault.path "C:\Users\MSI Thin 15\Documents\hermes-vault"
```

## Troubleshooting

### "LOCK HELD by 'terminal-1'"
Another instance is saving. Wait for it to finish, or:
```bash
bash hermes-session-lock.sh wait my-instance
```

### "STALE LOCK from 'terminal-1'"
The holder process died. Safe to take over:
```bash
bash hermes-session-lock.sh lock my-instance
```

### DB Corruption
If state.db is corrupted:
1. Stop all Hermes instances
2. Delete `state.db-shm` and `state.db-wal` (NOT `state.db`)
3. Restart Hermes — it will rebuild WAL files

### Lock file not releasing
Manual cleanup:
```bash
rm -f ~/.hermes-locks/db.lock ~/.hermes-locks/pid
```

## Migration to Another Device

1. Copy all files to the new device:
   - `hermes-new` (the easy way)
   - `hermes-session-lock.sh` (lock management)
   - `hermes-safe.sh` (wrapper)
   - `hermes-multi.sh` (multi-launch)
2. Ensure Hermes is installed and `hermes` command is in PATH
3. Update vault path in config if different
4. Run `hermes-new` — paste API key — done

## Limitations (Phase 1)

- Lock is advisory: instances must use `hermes-safe.sh` wrapper (raw `hermes` bypasses lock)
- No automatic queue: instances must wait manually or use `hermes-session-lock.sh wait`
- Stale detection is time-based (not process-based) — works on Windows/MSYS/Linux
- Alert is file-based (check `hermes-session-lock.sh alert`) — no push notification

## Roadmap

- Phase 2: Automatic queue with FIFO ordering
- Phase 3: Hermes config integration (auto-detect multi-instance)
- Phase 4: Web UI for lock status monitoring
