#!/usr/bin/env bash
# hermes-safe.sh
# Wrapper: jalanin Hermes dengan session lock otomatis
#
# Usage:
#   hermes-safe.sh <instance_name> [--force] [hermes_args...]
#
# Examples:
#   hermes-safe.sh terminal-1
#   hermes-safe.sh terminal-2 --model openrouter/owl-alpha
#   hermes-safe.sh terminal-1 --force   # skip lock check (risky)
#
# What it does:
#   1. Checks DB lock status
#   2. Acquires lock (or waits if locked)
#   3. Runs Hermes
#   4. Releases lock when Hermes exits (even on Ctrl+C)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTANCE="${1:-default}"
shift

FORCE=false
if [[ "${1:-}" == "--force" ]]; then
    FORCE=true
    shift
fi

echo "========================================="
echo "  Hermes Safe Launcher"
echo "  Instance: $INSTANCE"
echo "  Time: $(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================="
echo ""

# Step 1: Check status
echo "[*] Checking DB lock..."
"$SCRIPT_DIR/hermes-session-lock.sh" status
echo ""

# Step 2: Acquire lock
echo "[*] Acquiring lock..."
if ! "$SCRIPT_DIR/hermes-session-lock.sh" lock "$INSTANCE"; then
    if [ "$FORCE" = true ]; then
        echo "[!] --force: Starting anyway. DB corruption risk!"
    else
        echo ""
        echo "[!] Could not acquire lock."
        echo "[!] Options:"
        echo "    1. Wait:  hermes-session-lock.sh wait $INSTANCE"
        echo "    2. Force:  hermes-safe.sh $INSTANCE --force"
        echo "    3. Check:  hermes-session-lock.sh status"
        echo ""
        exit 1
    fi
fi

echo ""
echo "[*] Lock acquired. Starting Hermes..."
echo "[*] Instance '$INSTANCE' will hold the lock until Hermes exits."
echo "[*] Press Ctrl+C to stop. Lock will be released automatically."
echo ""

# Step 3: Cleanup on exit
cleanup() {
    echo ""
    echo "[*] Hermes exited. Releasing lock for '$INSTANCE'..."
    "$SCRIPT_DIR/hermes-session-lock.sh" unlock "$INSTANCE" 2>/dev/null || true
    echo "[*] Lock released. DB is free."
}
trap cleanup EXIT INT TERM

# Step 4: Run Hermes
hermes "$@"
