# Vault Audit Procedure

## When to Audit
- Vault feels incomplete ("kok dikit ya")
- Manifest count doesn't match actual files
- Cron job hasn't run successfully in a while
- After major sessions that produced new knowledge

## Step-by-Step

### 1. Compare Manifest vs Actual Files
Any manifest entry without a matching sessions/*.md file = stale entry, remove from manifest.

### 2. Find Unprocessed Sessions
Diff raw session IDs (session_*.json) against manifest. Note: session JSON filename != session_id inside the JSON (auto-resume). Always check the session_id field.

### 3. Filter Trivial Sessions
- <10 messages or <5KB: skip entirely
- 10-30 messages, no new knowledge: 1-line in _skipped.md
- 10-30 messages, has new knowledge: full summary

### 4. Extract Sessions
Run: python scripts/phase1_extract.py (outputs to sessions-raw/)

### 5. Summarize
Read extracted markdown, write session summary following vault-update protocol. Create concept/decision/person files if needed. Update index.md, knowledge-map.md, manifest.json.

### 6. Rebuild Manifest
Remove stale entries, add new entries, update last_updated timestamp and counts.

### 7. Expand Thin Concepts
Any concept file <1500 bytes needs expansion with: definition, why it matters, how it works, examples, cross-references.

## Common Pitfalls
- Session JSON filename != session_id (auto-resume)
- request_dump_*.json are NOT sessions
- cron_* files are NOT user sessions
- Don't create stub concepts (<1500 bytes = not a concept yet)
