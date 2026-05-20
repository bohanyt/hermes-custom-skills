#!/usr/bin/env bash
# hermes-multi.sh
# Multi-terminal Hermes launcher with per-instance API keys
#
# Usage:
#   hermes-multi.sh <config_file>
#
# Config file format (bash source-able):
#   HERMES_API_KEYS=(
#     "sk-or-v1-aaaa..."   # terminal-1
#     "sk-or-v1-bbbb..."   # terminal-2
#     "sk-or-v1-cccc..."   # terminal-3
#   )
#   HERMES_INSTANCE_NAMES=(
#     "terminal-1"
#     "terminal-2"
#     "terminal-3"
#   )
#   HERMES_MODEL="openrouter/owl-alpha"
#
# Or use simple format (one key per line, # for comments):
#   # terminal-1
#   sk-or-v1-aaaa...
#   # terminal-2
#   sk-or-v1-bbbb...
#
# Examples:
#   hermes-multi.sh ~/.hermes-keys.conf
#   hermes-multi.sh ./my-keys.txt

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${1:-}"

if [ -z "$CONFIG_FILE" ]; then
    echo "Usage: hermes-multi.sh <config_file>"
    echo ""
    echo "Config file: one API key per line, # comments for instance names"
    echo "Example:"
    echo "  # terminal-1"
    echo "  sk-or-v1-aaaa..."
    echo "  # terminal-2"
    echo "  sk-or-v1-bbbb..."
    exit 1
fi

if [ ! -f "$CONFIG_FILE" ]; then
    echo "Config file not found: $CONFIG_FILE"
    exit 1
fi

# Parse config — simple format: # name, then key on next line
declare -a NAMES=()
declare -a KEYS=()
current_name="terminal-$(( ${#NAMES[@]} + 1 ))"

while IFS= read -r line; do
    # Skip empty lines
    [[ -z "$line" ]] && continue
    
    # Comment line = instance name
    if [[ "$line" == \#* ]]; then
        current_name="${line#\# }"
        current_name="${current_name#\#}"
        continue
    fi
    
    # API key line
    NAMES+=("$current_name")
    KEYS+=("$line")
    current_name="terminal-$(( ${#NAMES[@]} + 1 ))"
done < "$CONFIG_FILE"

if [ ${#KEYS[@]} -eq 0 ]; then
    echo "No API keys found in config file."
    exit 1
fi

echo "========================================="
echo "  Hermes Multi-Terminal Launcher"
echo "  Instances: ${#KEYS[@]}"
echo "  Time: $(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================="
echo ""

for i in "${!KEYS[@]}"; do
    echo "  [$((i+1))] ${NAMES[$i]} -> ${KEYS[$i]:0:12}..."
done
echo ""

# Launch each instance in a new terminal window
LAUNCH_CMD=""
for i in "${!KEYS[@]}"; do
    local_name="${NAMES[$i]}"
    local_key="${KEYS[$i]}"
    
    # Build the command for this instance
    # Uses mintty (default MSYS2 terminal) or falls back to cmd
    INSTANCE_CMD="export OPENROUTER_API_KEY='${local_key}'; cd '${SCRIPT_DIR}'; bash hermes-safe.sh '${local_name}'; exec bash"
    
    echo "[*] Launching instance $((i+1))/${#KEYS[@]}: $local_name"
    
    # Try mintty first (MSYS2 default), then fall back to cmd.exe
    if command -v mintty &>/dev/null; then
        mintty -t "Hermes: $local_name" -- bash -c "$INSTANCE_CMD" &
    elif command -v xterm &>/dev/null; then
        xterm -title "Hermes: $local_name" -e "bash -c '$INSTANCE_CMD'" &
    else
        # Windows fallback: use cmd.exe to start new window
        cmd.exe /c start "Hermes: $local_name" bash -c "$INSTANCE_CMD" &
    fi
    
    LAUNCH_PID=$!
    echo "    PID: $LAUNCH_PID"
    
    # Small delay between launches to avoid race condition on first lock
    sleep 1
done

echo ""
echo "[*] All ${#KEYS[@]} instances launched."
echo "[*] Each instance will acquire DB lock when saving."
echo "[*] Check status: hermes-session-lock.sh status"
echo ""
