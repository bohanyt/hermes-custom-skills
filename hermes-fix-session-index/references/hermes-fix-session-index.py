#!/usr/bin/env python3
"""
hermes-fix-session-index.py
Scan session JSON files that are missing from sessions.json index and add them.
Also rebuilds the FTS5 search index in state.db for any newly added sessions.

Usage:
  python hermes-fix-session-index.py [--dry-run] [--verbose]
"""

import json
import os
import sys
import glob
import sqlite3
import datetime

HOME = os.path.expanduser("~")
SESSIONS_DIR = os.path.join(HOME, "AppData", "Local", "hermes", "sessions")
SESSIONS_JSON = os.path.join(SESSIONS_DIR, "sessions.json")
STATE_DB = os.path.join(HOME, "AppData", "Local", "hermes", "state.db")

def load_sessions_index():
    if os.path.exists(SESSIONS_JSON):
        with open(SESSIONS_JSON) as f:
            return json.load(f)
    return {}

def save_sessions_index(sessions):
    with open(SESSIONS_JSON, "w") as f:
        json.dump(sessions, f, indent=2)

def get_session_files():
    pattern = os.path.join(SESSIONS_DIR, "session_*.json")
    files = glob.glob(pattern)
    # Exclude cron/bg sessions
    files = [f for f in files if "_cron_" not in f and "_bg_" not in f]
    files.sort(key=os.path.getmtime, reverse=True)
    return files

def extract_session_info(filepath):
    try:
        with open(filepath) as f:
            data = json.load(f)
    except (json.JSONDecodeError, IOError):
        return None

    session_id = data.get("session_id", "")
    session_start = data.get("session_start", "")
    last_updated = data.get("last_updated", "")
    platform = data.get("platform", "cli")
    model = data.get("model", "")

    # Get first user message for display name
    first_user_msg = ""
    msgs = data.get("messages", [])
    for m in msgs:
        if m.get("role") == "user":
            content = m.get("content", "")
            if isinstance(content, list):
                content = " ".join([c.get("text", "") for c in content if isinstance(c, dict)])
            first_user_msg = content[:80]
            break

    # Determine display name
    if first_user_msg:
        display_name = f"CLI / {first_user_msg}"
    else:
        display_name = f"CLI / {session_id}"

    return {
        "session_id": session_id,
        "session_start": session_start,
        "last_updated": last_updated,
        "platform": platform,
        "model": model,
        "display_name": display_name,
        "filepath": filepath,
    }

def make_session_key(session_id, platform="cli"):
    return f"agent:main:{platform}:session:{session_id}"

def add_to_index(sessions, info):
    session_id = info["session_id"]
    platform = info["platform"]
    key = make_session_key(session_id, platform)

    if key in sessions:
        return False  # Already indexed

    now = datetime.datetime.now().isoformat()
    sessions[key] = {
        "session_key": key,
        "session_id": session_id,
        "created_at": info["session_start"] or now,
        "updated_at": info["last_updated"] or now,
        "display_name": info["display_name"],
        "platform": platform,
        "chat_type": "session",
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_read_tokens": 0,
        "cache_write_tokens": 0,
        "total_tokens": 0,
        "last_prompt_tokens": 0,
        "estimated_cost_usd": 0.0,
        "cost_status": "unknown",
        "expiry_finalized": True,
        "suspended": False,
        "resume_pending": False,
        "resume_reason": None,
        "last_resume_marked_at": None,
        "is_fresh_reset": False,
        "was_auto_reset": False,
        "auto_reset_reason": None,
        "reset_had_activity": False,
        "origin": {
            "platform": platform,
            "chat_id": session_id,
            "chat_name": info["display_name"],
            "chat_type": "session",
            "user_id": "local",
            "user_name": "local",
        },
    }
    return True

def rebuild_fts_index(session_id, display_name):
    """Rebuild FTS5 index in state.db for the given session."""
    if not os.path.exists(STATE_DB):
        return False
    try:
        conn = sqlite3.connect(STATE_DB)
        # Check if fts table exists
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%fts%'"
        )
        fts_tables = [row[0] for row in cursor.fetchall()]
        if fts_tables:
            # Try to rebuild — best effort
            for table in fts_tables:
                try:
                    conn.execute(f"INSERT INTO {table}({table}) VALUES('rebuild')")
                except Exception:
                    pass
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False

def main():
    dry_run = "--dry-run" in sys.argv
    verbose = "--verbose" in sys.argv

    print("=" * 50)
    print("Hermes Session Index Fixer")
    print("=" * 50)
    print()

    # Load existing index
    sessions = load_sessions_index()
    existing_count = len(sessions)
    print(f"Sessions in index: {existing_count}")

    # Scan session files
    files = get_session_files()
    print(f"Session files found: {len(files)}")
    print()

    added = 0
    skipped = 0
    errors = 0

    for filepath in files:
        info = extract_session_info(filepath)
        if info is None:
            if verbose:
                print(f"  SKIP (unreadable): {os.path.basename(filepath)}")
            errors += 1
            continue

        session_id = info["session_id"]
        if not session_id:
            if verbose:
                print(f"  SKIP (no session_id): {os.path.basename(filepath)}")
            errors += 1
            continue

        key = make_session_key(session_id)
        if key in sessions:
            skipped += 1
            if verbose:
                print(f"  OK (already indexed): {session_id}")
            continue

        # Missing from index — add it
        print(f"  ADD: {session_id}")
        print(f"       {info['display_name'][:60]}")

        if not dry_run:
            if add_to_index(sessions, info):
                added += 1
                # Try to rebuild FTS index
                rebuild_fts_index(session_id, info["display_name"])
        else:
            added += 1  # Would be added

    print()
    print(f"Results: {added} added, {skipped} already indexed, {errors} errors")

    if not dry_run and added > 0:
        save_sessions_index(sessions)
        print(f"Index saved: {len(sessions)} total sessions")
    elif dry_run and added > 0:
        print(f"DRY RUN: Would add {added} sessions (not saved)")
    else:
        print("No changes needed.")

    print()
    print("Done.")

if __name__ == "__main__":
    main()
