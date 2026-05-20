#!/usr/bin/env bash
# hermes-session-lock.sh
# Phase 1: File-based lock + alert for multi-terminal Hermes sessions
#
# Uses file mtime for stale detection (no PID checks — works on Windows/MSYS).
# A lock older than LOCK_MAX_AGE_SEC is considered stale and will be taken over.
#
# Usage:
#   hermes-session-lock.sh lock   <instance_name>  — acquire lock
#   hermes-session-lock.sh unlock <instance_name>  — release lock
#   hermes-session-lock.sh status                  — check lock status
#   hermes-session-lock.sh wait   <instance_name>  — wait until lock is free, then acquire
#   hermes-session-lock.sh alert                   — show alert to all terminals

set -euo pipefail

LOCK_DIR="${HERMES_LOCK_DIR:-$HOME/.hermes-locks}"
LOCK_FILE="$LOCK_DIR/db.lock"
STATUS_FILE="$LOCK_DIR/status"
ALERT_FILE="$LOCK_DIR/alert"
LOCK_MAX_AGE_SEC="${LOCK_MAX_AGE_SEC:-300}"  # 5 min default

mkdir -p "$LOCK_DIR"

_timestamp() { date '+%Y-%m-%d %H:%M:%S'; }

# Check if lock file is stale (older than LOCK_MAX_AGE_SEC)
_is_stale() {
    if [ ! -f "$LOCK_FILE" ]; then
        return 1  # no lock = not stale
    fi
    local now lock_age
    now=$(date +%s 2>/dev/null || python -c "import time; print(int(time.time()))")
    local mtime
    mtime=$(stat -c '%Y' "$LOCK_FILE" 2>/dev/null || stat -f '%m' "$LOCK_FILE" 2>/dev/null || python -c "import os,time; print(int(os.path.getmtime('$LOCK_FILE')))" 2>/dev/null || echo "$now")
    lock_age=$((now - mtime))
    if [ "$lock_age" -gt "$LOCK_MAX_AGE_SEC" ]; then
        return 0  # stale
    fi
    return 1  # not stale
}

cmd_lock() {
    local instance="${1:-unknown}"
    
    if [ -f "$LOCK_FILE" ]; then
        local holder
        holder=$(cat "$LOCK_FILE" 2>/dev/null || echo "unknown")
        
        if _is_stale; then
            echo "[$(_timestamp)] Stale lock from '$holder' (age > ${LOCK_MAX_AGE_SEC}s). Taking over."
            rm -f "$LOCK_FILE"
        else
            echo "[$(_timestamp)] LOCK HELD by '$holder'"
            echo "  -> Wait: hermes-session-lock.sh wait $instance"
            echo "  -> Or force: hermes-session-lock.sh unlock $holder (then retry)"
            echo "WARNING: DB lock held by '$holder'" > "$ALERT_FILE"
            return 1
        fi
    fi
    
    echo "$instance" > "$LOCK_FILE"
    echo "$instance $(_timestamp)" > "$STATUS_FILE"
    echo "[$(_timestamp)] LOCK ACQUIRED by '$instance'"
    echo "Hermes DB: '$instance' is now saving to DB. Please wait..." > "$ALERT_FILE"
    return 0
}

cmd_unlock() {
    local instance="${1:-unknown}"
    
    if [ ! -f "$LOCK_FILE" ]; then
        echo "[$(_timestamp)] No lock to release."
        return 0
    fi
    
    local holder
    holder=$(cat "$LOCK_FILE" 2>/dev/null || echo "unknown")
    
    if [ "$holder" != "$instance" ]; then
        echo "[$(_timestamp)] WARNING: Lock held by '$holder', not '$instance'. Force unlock? (y/N)"
        read -r confirm
        if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
            echo "  -> Unlock cancelled."
            return 1
        fi
    fi
    
    rm -f "$LOCK_FILE"
    echo "unlocked $(_timestamp)" > "$STATUS_FILE"
    echo "[$(_timestamp)] LOCK RELEASED by '$instance'"
    echo "Hermes DB: Ready. Lock released by '$instance'." > "$ALERT_FILE"
    return 0
}

cmd_status() {
    if [ -f "$LOCK_FILE" ]; then
        local holder
        holder=$(cat "$LOCK_FILE" 2>/dev/null || echo "unknown")
        
        if _is_stale; then
            echo "STALE LOCK from '$holder' (age > ${LOCK_MAX_AGE_SEC}s)"
            echo "  -> Safe to take over: hermes-session-lock.sh lock <your_instance>"
        else
            echo "LOCKED by '$holder'"
            echo "  Since: $(stat -c '%y' "$LOCK_FILE" 2>/dev/null || stat -f '%Sm' "$LOCK_FILE" 2>/dev/null || echo 'unknown')"
        fi
    else
        echo "UNLOCKED — DB is free"
    fi
    
    if [ -f "$STATUS_FILE" ]; then
        echo "Last status: $(cat "$STATUS_FILE")"
    fi
}

cmd_wait() {
    local instance="${1:-unknown}"
    local max_wait="${2:-300}"
    local waited=0
    
    echo "[$(_timestamp)] '$instance' waiting for DB lock..."
    
    while [ -f "$LOCK_FILE" ]; do
        local holder
        holder=$(cat "$LOCK_FILE" 2>/dev/null || echo "unknown")
        
        if _is_stale; then
            echo "[$(_timestamp)] Holder '$holder' is stale. Taking lock."
            rm -f "$LOCK_FILE"
            break
        fi
        
        if [ "$waited" -ge "$max_wait" ]; then
            echo "[$(_timestamp)] TIMEOUT after ${max_wait}s. Lock still held by '$holder'."
            return 1
        fi
        
        echo "  ... waiting (${waited}s / ${max_wait}s) — held by '$holder'"
        sleep 5
        waited=$((waited + 5))
    done
    
    cmd_lock "$instance"
}

cmd_alert() {
    if [ -f "$ALERT_FILE" ]; then
        echo "=== HERMES DB ALERT ==="
        cat "$ALERT_FILE"
        echo "======================="
    else
        echo "No active alerts."
    fi
}

# --- Main ---
case "${1:-help}" in
    lock)   cmd_lock "${2:-}" ;;
    unlock) cmd_unlock "${2:-}" ;;
    status) cmd_status ;;
    wait)   cmd_wait "${2:-}" "${3:-300}" ;;
    alert)  cmd_alert ;;
    help|*)
        echo "Usage: hermes-session-lock.sh {lock|unlock|status|wait|alert} [instance_name] [max_wait_seconds]"
        echo ""
        echo "Commands:"
        echo "  lock <name>     — Acquire DB lock (fails if already locked)"
        echo "  unlock <name>   — Release DB lock"
        echo "  status          — Check current lock status"
        echo "  wait <name> [s] — Wait for lock, then acquire (default 300s timeout)"
        echo "  alert           — Show current alert message"
        echo ""
        echo "Env:"
        echo "  HERMES_LOCK_DIR    — Lock directory (default: ~/.hermes-locks)"
        echo "  LOCK_MAX_AGE_SEC   — Max lock age before stale (default: 300s = 5min)"
        ;;
esac
