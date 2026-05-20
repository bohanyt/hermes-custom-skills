#!/usr/bin/env python3
"""
vault_concepts.py — Extract concepts dan decisions dari vault sessions

Flow:
  1. Scan semua session summaries di vault/sessions/
  2. Extract concepts (topics yang muncul di multiple sessions)
  3. Extract decisions (pola "decided", "memilih", "finally")
  4. Write/update concepts/ dan decisions/ files
  5. Update .manifest.json

Usage:
  python vault_concepts.py [--vault-path <path>] [--dry-run]
"""

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

VAULT_PATH = Path.home() / "Documents" / "hermes-vault"
MIN_CONCEPT_SESSIONS = 2  # Minimal 2 sessions mention concept
MIN_CONCEPT_LENGTH = 1500  # Minimal 1500 bytes untuk concept file

# ─── Helpers ──────────────────────────────────────────────────────────────────

def load_manifest():
    manifest_path = VAULT_PATH / ".manifest.json"
    if manifest_path.exists():
        with open(manifest_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"version": "2.0", "counts": {}, "concepts": [], "decisions": []}

def save_manifest(manifest):
    manifest["last_updated"] = datetime.now(timezone.utc).isoformat()
    manifest_path = VAULT_PATH / ".manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

def scan_sessions():
    """Scan semua session summaries, return list of dicts."""
    sessions_dir = VAULT_PATH / "sessions"
    sessions = []
    
    if not sessions_dir.exists():
        return sessions
    
    for f in sessions_dir.glob("*.md"):
        content = f.read_text(encoding="utf-8")
        
        # Parse frontmatter
        title = ""
        date = ""
        tags = []
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                fm = parts[1]
                for line in fm.strip().split("\n"):
                    if line.startswith("title:"):
                        title = line.split(":", 1)[1].strip().strip('"')
                    elif line.startswith("date:"):
                        date = line.split(":", 1)[1].strip()
                    elif line.startswith("tags:"):
                        tags_str = line.split(":", 1)[1].strip()
                        tags = [t.strip().strip('"') for t in tags_str.strip("[]").split(",")]
        
        sessions.append({
            "file": f.name,
            "title": title,
            "date": date,
            "tags": tags,
            "content": content
        })
    
    return sessions

def extract_concepts(sessions):
    """Extract concepts dari sessions (topics yang muncul di multiple sessions)."""
    concept_sessions = defaultdict(list)
    
    for session in sessions:
        for tag in session.get("tags", []):
            if tag and tag != "session":
                concept_sessions[tag].append(session["file"])
    
    # Filter concepts yang muncul di >= MIN_CONCEPT_SESSIONS sessions
    concepts = {}
    for concept, files in concept_sessions.items():
        if len(files) >= MIN_CONCEPT_SESSIONS:
            concepts[concept] = files
    
    return concepts

def extract_decisions(sessions):
    """Extract decisions dari session content."""
    decision_patterns = [
        r'(?:decided|memilih|finally|akhirnya|tentu saja|memutuskan)\s*[:\-]?\s*(.+)',
        r'(?:decision|keputusan)\s*[:\-]?\s*(.+)',
        r'(?:will|akan)\s+(?:use|gunakan|pakai|implement|implementasikan)\s+(.+)',
    ]
    
    decisions = []
    
    for session in sessions:
        content = session.get("content", "")
        for pattern in decision_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if len(match.strip()) > 10:
                    decisions.append({
                        "text": match.strip()[:200],
                        "session": session["file"],
                        "date": session.get("date", "")
                    })
    
    return decisions

def write_concept_file(concept, sessions_list):
    """Write concept markdown file."""
    concepts_dir = VAULT_PATH / "concepts"
    concepts_dir.mkdir(exist_ok=True)
    
    filename = f"{concept}.md"
    filepath = concepts_dir / filename
    
    # Check if file exists (preserve existing content)
    existing_content = ""
    if filepath.exists():
        existing_content = filepath.read_text(encoding="utf-8")
    
    # Build content
    md = f"""# {concept.title()}

## Related Sessions
"""
    for s in sessions_list:
        md += f"- [[{s}]]\n"
    
    md += f"""
## Notes
{existing_content if existing_content else f'(Add notes about {concept} here)'}

## Last Updated
{datetime.now(timezone.utc).strftime("%Y-%m-%d")}
"""
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(md)
    
    return filename

def write_decision_file(decision):
    """Write decision markdown file."""
    decisions_dir = VAULT_PATH / "decisions"
    decisions_dir.mkdir(exist_ok=True)
    
    # Generate filename from decision text
    slug = re.sub(r'[^\w\-]', '-', decision["text"].lower())[:40]
    date_str = decision.get("date", datetime.now().strftime("%Y-%m-%d")).replace("-", "")
    filename = f"{date_str}-{slug}.md"
    filepath = decisions_dir / filename
    
    md = f"""---
title: {decision["text"][:80]}
date: {decision.get("date", "")}
session: {decision["session"]}
---

## Decision

{decision["text"]}

## Context

From session: [[{decision["session"]}]]
"""
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(md)
    
    return filename

# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Vault Concepts — Extract concepts/decisions")
    parser.add_argument("--vault-path", default=str(VAULT_PATH), help="Path to vault")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    args = parser.parse_args()
    
    vault_path = Path(args.vault_path)
    
    print("=" * 60)
    print("Vault Concepts — Extract concepts & decisions")
    print("=" * 60)
    print(f"Vault: {vault_path}")
    print(f"Mode:  {'DRY RUN' if args.dry_run else 'LIVE'}")
    print("")
    
    # Load manifest
    manifest = load_manifest()
    
    # Scan sessions
    sessions = scan_sessions()
    print(f"Found {len(sessions)} session summaries")
    print("")
    
    # Extract concepts
    concepts = extract_concepts(sessions)
    print(f"Concepts found: {len(concepts)}")
    
    concept_files = []
    for concept, files in sorted(concepts.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"  {concept}: {len(files)} sessions")
        if not args.dry_run:
            filename = write_concept_file(concept, files)
            concept_files.append(filename)
    
    # Extract decisions
    decisions = extract_decisions(sessions)
    print(f"\nDecisions found: {len(decisions)}")
    
    decision_files = []
    for decision in decisions[:20]:  # Limit to 20 most recent
        print(f"  - {decision['text'][:60]}")
        if not args.dry_run:
            filename = write_decision_file(decision)
            decision_files.append(filename)
    
    # Update manifest
    if not args.dry_run:
        manifest["concepts"] = list(concepts.keys())
        manifest["decisions"] = [d["text"][:50] for d in decisions[:20]]
        manifest["counts"]["concepts"] = len(concepts)
        manifest["counts"]["decisions"] = len(decisions[:20])
        save_manifest(manifest)
    
    print("")
    print("=" * 60)
    print(f"Concepts: {len(concepts)}, Decisions: {len(decisions)}")
    print("=" * 60)

if __name__ == "__main__":
    main()
