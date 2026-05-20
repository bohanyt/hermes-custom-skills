#!/usr/bin/env bash
# hermes-save-db.sh
# Force-save Hermes session DB (flush WAL, verify integrity)
#
# Usage: hermes-save-db.sh [--verify]

set -euo pipefail

DB="$HOME/AppData/Local/hermes/state.db"
WAL="$DB-wal"
SHM="$DB-shm"

echo "=== Hermes DB Save ==="
echo "DB: $DB"
echo ""

# Check DB exists
if [ ! -f "$DB" ]; then
    echo "ERROR: DB not found: $DB"
    exit 1
fi

# Check size
DB_SIZE=$(du -h "$DB" 2>/dev/null | cut -f1)
echo "DB size: $DB_SIZE"

# Check WAL
if [ -f "$WAL" ]; then
    WAL_SIZE=$(du -h "$WAL" 2>/dev/null | cut -f1)
    echo "WAL size: $WAL_SIZE"
    echo "  -> WAL has uncommitted data. Flushing..."
else
    echo "WAL: clean (no pending writes)"
fi

# Flush WAL to main DB using SQLite
echo ""
echo "[*] Flushing WAL to main DB..."
if command -v sqlite3 &>/dev/null; then
    sqlite3 "$DB" "PRAGMA wal_checkpoint(TRUNCATE);" 2>/dev/null && echo "  -> WAL checkpoint OK" || echo "  -> WAL checkpoint failed (DB may be locked by another process)"
else
    echo "  -> sqlite3 not found. Install: pacman -S sqlite3 (MSYS2) or choco install sqlite"
    echo "  -> WAL will be flushed automatically when Hermes exits cleanly."
fi

# Verify integrity
if [[ "${1:-}" == "--verify" ]] && command -v sqlite3 &>/dev/null; then
    echo ""
    echo "[*] Verifying DB integrity..."
    if sqlite3 "$DB" "PRAGMA integrity_check;" 2>/dev/null | grep -q "ok"; then
        echo "  -> DB integrity: OK"
    else
        echo "  -> DB integrity: FAILED! Consider restoring from backup."
    fi
fi

# Count sessions
if command -v sqlite3 &>/dev/null; then
    echo ""
    SESSION_COUNT=$(sqlite3 "$DB" "SELECT COUNT(*) FROM sessions;" 2>/dev/null || echo "?")
    echo "Sessions in DB: $SESSION_COUNT"
fi

echo ""
echo "=== Done ==="
