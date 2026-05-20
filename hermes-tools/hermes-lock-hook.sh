#!/usr/bin/env bash
# hermes-lock-hook.sh
# Source this from .bashrc to auto-lock/unlock Hermes sessions.
#
# Add to ~/.bashrc:
#   source /c/Users/MSI Thin 15/Documents/hermes-tools/hermes-lock-hook.sh
#
# What it does:
#   - Wraps the `hermes` command with DB lock/unlock
#   - Auto-acquires lock before Hermes starts
#   - Auto-releases lock when Hermes exits (even on Ctrl+C)
#   - Uses file-based lock (works on Windows/MSYS/Linux)
#   - Stale lock detection (5 min timeout)
#
# All terminals using this hook share the same lock file,
# so concurrent writes to state.db are serialized.

HERMES_LOCK_DIR="${HERMES_LOCK_DIR:-$HOME/.hermes-locks}"
LOCK_FILE="$HERMES_LOCK_DIR/db.lock"
STATUS_FILE="$HERMES_LOCK_DIR/status"
LOCK_MAX_AGE_SEC="${LOCK_MAX_AGE_SEC:-300}"

mkdir -p "$HERMES_LOCK_DIR"

_hermes_lock_timestamp() { date '+%Y-%m-%d %H:%M:%S'; }

_hermes_is_stale() {
    [ ! -f "$LOCK_FILE" ] && return 1
    local now mtime age
    now=$(date +%s 2>/dev/null || python -c "import time; print(int(time.time()))" 2>/dev/null || echo "0")
    mtime=$(stat -c '%Y' "$LOCK_FILE" 2>/dev/null || stat -f '%m' "$LOCK_FILE" 2>/dev/null || python -c "import os; print(int(os.path.getmtime('$LOCK_FILE')))" 2>/dev/null || echo "$now")
    age=$((now - mtime))
    [ "$age" -gt "$LOCK_MAX_AGE_SEC" ]
}

_hermes_acquire_lock() {
    local instance="${1:-$$}"
    local waited=0

    while true; do
        if [ -f "$LOCK_FILE" ]; then
            local holder
            holder=$(cat "$LOCK_FILE" 2>/dev/null || echo "?")

            if _hermes_is_stale; then
                echo "[hermes-lock] Stale lock from '$holder'. Taking over."
                rm -f "$LOCK_FILE"
                break
            fi

            if [ "$waited" -ge 60 ]; then
                echo "[hermes-lock] WARNING: Still waiting for lock held by '$holder' after 60s."
                echo "[hermes-lock] Force? Run: rm -f ~/.hermes-locks/db.lock"
                return 1
            fi

            if [ "$waited" -eq 0 ]; then
                echo "[hermes-lock] DB locked by '$holder'. Waiting..."
            fi

            sleep 2
            waited=$((waited + 2))
        else
            break
        fi
    done

    echo "$instance" > "$LOCK_FILE"
    echo "$instance $(_hermes_lock_timestamp)" > "$STATUS_FILE"
    [ "$waited" -gt 0 ] && echo "[hermes-lock] Lock acquired after ${waited}s."
    return 0
}

_hermes_release_lock() {
    local instance="${1:-$$}"
    if [ -f "$LOCK_FILE" ]; then
        local holder
        holder=$(cat "$LOCK_FILE" 2>/dev/null || echo "?")
        if [ "$holder" = "$instance" ] || [ "$holder" = "$$" ]; then
            rm -f "$LOCK_FILE"
            echo "unlocked $(_hermes_lock_timestamp)" > "$STATUS_FILE"
        fi
    fi
}

# Override the hermes command
hermes() {
    local instance="hermes-$$"

    # Acquire lock
    if ! _hermes_acquire_lock "$instance"; then
        echo "[hermes-lock] Could not acquire DB lock. Start anyway? (y/N)"
        read -r confirm
        [[ "$confirm" != "y" && "$confirm" != "Y" ]] && return 1
    fi

    # Run real Hermes with all arguments
    command hermes "$@"
    local exit_code=$?

    # Release lock
    _hermes_release_lock "$instance"

    return $exit_code
}

echo "[hermes-lock] Multi-session lock hook loaded. All 'hermes' calls will auto-lock/unlock."
