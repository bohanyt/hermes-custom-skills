#!/usr/bin/env python3
"""
vault_update.py — Auto-extract knowledge dari Hermes sessions ke Vault

Flow:
  1. Scan session JSON files di AppData/Local/hermes/sessions/
  2. Bandingkan dengan .manifest.json (yang udah di-process)
  3. Extract topics dari session baru
  4. Write ke vault: sessions/
  5. Update index.md dan .manifest.json

Usage:
  python vault_update.py [--vault-path <path>] [--dry-run] [--verbose]
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# ─── Config ───────────────────────────────────────────────────────────────────

VAULT_PATH = Path.home() / "Documents" / "hermes-vault"
SESSIONS_PATH = Path.home() / "AppData" / "Local" / "hermes" / "sessions"
MANIFEST_PATH = VAULT_PATH / ".manifest.json"
INDEX_PATH = VAULT_PATH / "index.md"

MIN_SESSION_MESSAGES = 10
MAX_SUMMARY_LENGTH = 500

# ─── Helpers ──────────────────────────────────────────────────────────────────

def load_manifest():
    if MANIFEST_PATH.exists():
        with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "version": "2.0",
        "last_updated": "",
        "counts": {"sessions": 0, "concepts": 0, "decisions": 0, "people": 0},
        "processed_sessions": [],
        "skipped_sessions": [],
        "sessions": []
    }

def save_manifest(manifest):
    manifest["last_updated"] = datetime.now(timezone.utc).isoformat()
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

def is_session_processed(session_file, manifest):
    """Check if session already in manifest (by filename or session_id)."""
    session_id = session_file.stem
    
    # Check new format: processed_sessions list
    if session_id in manifest.get("processed_sessions", []):
        return True
    
    # Check old format: sessions array of objects
    for s in manifest.get("sessions", []):
        if isinstance(s, dict):
            s_file = s.get("file", "")
            s_id = s.get("session_id", "")
            if s_id == session_id or s_file.endswith(session_id):
                return True
        elif isinstance(s, str) and s == session_id:
            return True
    
    return False

def is_duplicate_title(title, vault_path):
    """Check if a session with similar title already exists in vault."""
    sessions_dir = vault_path / "sessions"
    if not sessions_dir.exists():
        return False
    
    normalized = re.sub(r'[^\w]', '', title.lower())
    
    for f in sessions_dir.glob("*.md"):
        content = f.read_text(encoding="utf-8", errors="ignore")
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                for line in parts[1].strip().split("\n"):
                    if line.startswith("title:"):
                        existing_title = line.split(":", 1)[1].strip().strip('"').strip()
                        existing_normalized = re.sub(r'[^\w]', '', existing_title.lower())
                        if normalized == existing_normalized or \
                           (len(normalized) > 10 and len(existing_normalized) > 10 and \
                            (normalized in existing_normalized or existing_normalized in normalized)):
                            return True
    return False

def load_session(session_file):
    """Load session JSON/JSONL file, return list of messages."""
    messages = []
    try:
        with open(session_file, "r", encoding="utf-8") as f:
            content = f.read().strip()
        
        if content.startswith("{"):
            data = json.loads(content)
            if isinstance(data, dict):
                if "messages" in data:
                    messages = data["messages"]
                elif "history" in data:
                    messages = data["history"]
                elif "role" in data:
                    messages = [data]
        elif content.startswith("["):
            data = json.loads(content)
            if isinstance(data, list):
                messages = data
        else:
            for line in content.split("\n"):
                line = line.strip()
                if line:
                    try:
                        obj = json.loads(line)
                        if isinstance(obj, dict):
                            messages.append(obj)
                    except json.JSONDecodeError:
                        pass
    except Exception as e:
        print(f"  ERROR loading {session_file.name}: {e}")
    
    return messages

def extract_session_metadata(session_file, messages):
    session_id = session_file.stem
    
    for msg in messages[:5]:
        if isinstance(msg, dict) and "session_id" in msg:
            session_id = msg["session_id"]
            break
    
    ts_match = re.match(r"(\d{8}_\d{6})", session_file.name)
    if ts_match:
        try:
            dt = datetime.strptime(ts_match.group(1), "%Y%m%d_%H%M%S")
            timestamp = dt.strftime("%Y-%m-%d")
        except ValueError:
            timestamp = datetime.fromtimestamp(session_file.stat().st_mtime).strftime("%Y-%m-%d")
    else:
        timestamp = datetime.fromtimestamp(session_file.stat().st_mtime).strftime("%Y-%m-%d")
    
    msg_count = sum(1 for m in messages if isinstance(m, dict) and m.get("role") in ("user", "assistant"))
    
    title = ""
    for msg in messages:
        if isinstance(msg, dict) and msg.get("role") == "user":
            content = msg.get("content", "")
            if isinstance(content, str) and content.strip():
                title = content.strip()[:80]
                break
            elif isinstance(content, list):
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        title = part.get("text", "").strip()[:80]
                        break
                if title:
                    break
    
    if not title:
        title = session_id
    
    return {
        "session_id": session_id,
        "timestamp": timestamp,
        "message_count": msg_count,
        "title": title,
        "filename": session_file.name
    }

def extract_topics(messages):
    topics = []
    full_text = ""
    
    for msg in messages:
        if isinstance(msg, dict):
            content = msg.get("content", "")
            if isinstance(content, str):
                full_text += " " + content
            elif isinstance(content, list):
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        full_text += " " + part.get("text", "")
    
    words = re.findall(r'\b[a-zA-Z]{4,}\b', full_text.lower())
    word_freq = {}
    stopwords = {"yang", "dengan", "untuk", "dari", "pada", "adalah", "ini", "itu",
                 "akan", "bisa", "sudah", "belum", "saja", "juga", "tidak",
                 "have", "this", "that", "with", "from", "will", "been", "were", "they",
                 "their", "what", "when", "where", "which", "there", "about", "would",
                 "could", "should", "does", "make", "like", "just", "more", "some",
                 "than", "them", "then", "into", "only", "also", "very", "much",
                 "even", "back", "well", "know", "take", "come", "good", "give",
                 "most", "over", "such", "think", "help", "through", "before",
                 "between", "after", "still", "find", "here", "thing", "many",
                 "long", "part", "great", "right", "look", "want", "tell",
                 "work", "first", "need", "keep", "call", "made", "down",
                 "being", "each", "done", "open", "show", "seems", "ask",
                 "used", "try", "start", "might", "must", "mean", "hand",
                 "high", "last", "move", "next", "once", "other", "same",
                 "seem", "turn", "went", "while", "end", "set", "put",
                 "read", "run", "said", "way", "get", "got", "let", "say",
                 "too", "any", "may", "new", "now", "old", "see", "two",
                 "who", "how", "its", "our", "out", "day", "has", "his",
                 "her", "him", "not", "all", "and", "are", "but", "for",
                 "had", "may", "one", "own", "she", "the", "use", "you"}
    
    for word in words:
        if word not in stopwords and len(word) > 4:
            word_freq[word] = word_freq.get(word, 0) + 1
    
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    topics = [word for word, count in sorted_words[:10] if count >= 3]
    
    return topics

def write_session_summary(session_dir, metadata, topics, messages):
    session_dir.mkdir(parents=True, exist_ok=True)
    
    summary_parts = []
    for msg in messages[:10]:
        if isinstance(msg, dict) and msg.get("role") == "user":
            content = msg.get("content", "")
            if isinstance(content, str):
                summary_parts.append(content.strip()[:200])
            elif isinstance(content, list):
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        summary_parts.append(part.get("text", "").strip()[:200])
    
    summary = " ".join(summary_parts)[:MAX_SUMMARY_LENGTH]
    if not summary:
        summary = f"Session with {metadata['message_count']} messages."
    
    slug = re.sub(r'[^\w\-]', '-', metadata['title'].lower())[:50]
    date_str = metadata['timestamp'].replace("-", "")
    filename = f"{date_str}-{slug}.md"
    filepath = session_dir / filename
    
    tags = ", ".join(topics[:5]) if topics else "session"
    
    md = f"""---
title: {metadata['title']}
date: {metadata['timestamp']}
session_id: {metadata['session_id']}
messages: {metadata['message_count']}
tags: [{tags}]
---

## Summary

{summary}

## Topics
"""
    for topic in topics[:10]:
        md += f"- {topic}\n"
    
    md += f"""
## Source
- File: `{metadata['filename']}`
- Messages: {metadata['message_count']}
"""
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(md)
    
    return filename

def update_index(index_path, session_filename, metadata, topics):
    entry = f"| [{metadata['title']}](sessions/{session_filename}) | {metadata['timestamp']} | {', '.join(topics[:3])} | {metadata['message_count']} |\n"
    
    if index_path.exists():
        content = index_path.read_text(encoding="utf-8")
    else:
        content = "# Vault Index\n\n| Session | Date | Topics | Messages |\n|---------|------|--------|----------|\n"
    
    lines = content.split("\n")
    insert_idx = None
    for i, line in enumerate(lines):
        if line.startswith("|---"):
            insert_idx = i + 1
            break
    
    if insert_idx is not None:
        lines.insert(insert_idx, entry.rstrip())
    else:
        lines.append(entry.rstrip())
    
    index_path.write_text("\n".join(lines), encoding="utf-8")

def process_session(session_file, manifest, vault_path, dry_run=False, verbose=False):
    session_id = session_file.stem
    
    if is_session_processed(session_file, manifest):
        if verbose:
            print(f"  SKIP (processed): {session_file.name}")
        return None
    
    if "skipped_sessions" not in manifest:
        manifest["skipped_sessions"] = []
    if "processed_sessions" not in manifest:
        manifest["processed_sessions"] = []
    
    messages = load_session(session_file)
    
    if not messages:
        print(f"  SKIP (no messages): {session_file.name}")
        manifest["skipped_sessions"].append({"id": session_id, "reason": "no_messages"})
        return None
    
    metadata = extract_session_metadata(session_file, messages)
    
    if metadata["message_count"] < MIN_SESSION_MESSAGES:
        print(f"  SKIP (trivial, {metadata['message_count']} msgs): {session_file.name}")
        manifest["skipped_sessions"].append({"id": session_id, "reason": "trivial"})
        return None
    
    print(f"  PROCESSING: {metadata['title'][:60]} ({metadata['message_count']} msgs)")
    
    # Check for duplicate title (revisit session)
    if is_duplicate_title(metadata["title"], vault_path):
        # Check if this revisit has more content
        sessions_dir = vault_path / "sessions"
        normalized = re.sub(r'[^\w]', '', metadata["title"].lower())
        
        for f in sessions_dir.glob("*.md"):
            content = f.read_text(encoding="utf-8", errors="ignore")
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    for line in parts[1].strip().split("\n"):
                        if line.startswith("title:"):
                            existing_title = line.split(":", 1)[1].strip().strip('"').strip()
                            existing_normalized = re.sub(r'[^\w]', '', existing_title.lower())
                            if normalized == existing_normalized or \
                               (len(normalized) > 10 and existing_normalized in normalized):
                                # Found duplicate — check message count
                                existing_msgs = 0
                                for l in parts[2].split("\n"):
                                    if l.startswith("messages:"):
                                        try:
                                            existing_msgs = int(l.split(":")[1].strip())
                                        except:
                                            pass
                                        break
                                
                                if metadata["message_count"] > existing_msgs:
                                    print(f"    REPLACE (revisit, {existing_msgs} -> {metadata['message_count']} msgs)")
                                    # Remove old file
                                    f.unlink()
                                    # Continue to write new one
                                    break
                                else:
                                    print(f"    SKIP (duplicate, not better): {metadata['title'][:60]}")
                                    manifest["skipped_sessions"].append({"id": session_id, "reason": "duplicate_not_better"})
                                    return None
                    break
    
    if dry_run:
        print(f"    DRY RUN — would write to sessions/")
        return metadata
    
    topics = extract_topics(messages)
    
    session_dir = vault_path / "sessions"
    filename = write_session_summary(session_dir, metadata, topics, messages)
    
    update_index(vault_path / "index.md", filename, metadata, topics)
    
    manifest["processed_sessions"].append(session_id)
    
    # Ensure counts key exists
    if "counts" not in manifest:
        manifest["counts"] = {"sessions": 0, "concepts": 0, "decisions": 0, "people": 0}
    manifest["counts"]["sessions"] = manifest["counts"].get("sessions", 0) + 1
    
    # Also add to sessions array (old format, for compatibility)
    manifest["sessions"].append({
        "file": f"sessions/{filename}",
        "date": metadata["timestamp"],
        "session_id": session_id,
        "topics": topics[:5]
    })
    
    print(f"    -> sessions/{filename}")
    
    return metadata

# ─── Lock ─────────────────────────────────────────────────────────────────────

LOCK_PATH = VAULT_PATH / ".vault_update.lock"
LOCK_TIMEOUT = 300  # 5 minutes

def acquire_lock():
    """Acquire file lock. Returns True if lock acquired, False if another process holds it."""
    if LOCK_PATH.exists():
        # Check if lock is stale
        try:
            lock_time = datetime.fromtimestamp(LOCK_PATH.stat().st_mtime, tz=timezone.utc)
            age = (datetime.now(timezone.utc) - lock_time).total_seconds()
            if age > LOCK_TIMEOUT:
                # Stale lock, take over
                LOCK_PATH.touch()
                return True
            else:
                # Another process is running
                return False
        except:
            return False
    else:
        LOCK_PATH.touch()
        return True

def release_lock():
    """Release file lock."""
    try:
        if LOCK_PATH.exists():
            LOCK_PATH.unlink()
    except:
        pass

# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Vault Update — Auto-extract sessions to vault")
    parser.add_argument("--vault-path", default=str(VAULT_PATH), help="Path to vault")
    parser.add_argument("--sessions-path", default=str(SESSIONS_PATH), help="Path to sessions")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()
    
    vault_path = Path(args.vault_path)
    sessions_path = Path(args.sessions_path)
    
    # Acquire lock (prevent concurrent runs in multi-session)
    if not args.dry_run:
        if not acquire_lock():
            print("Another vault update is running. Skipping.")
            sys.exit(0)
    
    try:
        print("=" * 60)
        print("Vault Update — Auto-extract sessions to vault")
        print("=" * 60)
        print(f"Vault:    {vault_path}")
        print(f"Sessions: {sessions_path}")
        print(f"Mode:     {'DRY RUN' if args.dry_run else 'LIVE'}")
        print("")
        
        if not vault_path.exists():
            print(f"ERROR: Vault path not found: {vault_path}")
            sys.exit(1)
        if not sessions_path.exists():
            print(f"ERROR: Sessions path not found: {sessions_path}")
            sys.exit(1)
        
        manifest = load_manifest()
        
        processed_ids = set(manifest.get("processed_sessions", []))
        for s in manifest.get("sessions", []):
            if isinstance(s, dict):
                processed_ids.add(s.get("session_id", ""))
                s_file = s.get("file", "")
                if s_file:
                    processed_ids.add(Path(s_file).stem)
        
        print(f"Previously processed: {len(processed_ids)} sessions")
        print("")
        
        session_files = sorted(sessions_path.glob("session_*.json*"), key=lambda f: f.stat().st_mtime)
        
        if not session_files:
            print("No session files found.")
            sys.exit(0)
        
        print(f"Found {len(session_files)} session files")
        print("")
        
        new_count = 0
        skip_count = 0
        
        for session_file in session_files:
            result = process_session(
                session_file, manifest, vault_path,
                dry_run=args.dry_run, verbose=args.verbose
            )
            if result:
                new_count += 1
            else:
                skip_count += 1
        
        if not args.dry_run:
            save_manifest(manifest)
        
        print("")
        print("=" * 60)
        print(f"Summary: {new_count} new, {skip_count} skipped")
        print(f"Total in vault: {len(processed_ids) + new_count}")
        print("=" * 60)
    
    finally:
        release_lock()

if __name__ == "__main__":
    main()
