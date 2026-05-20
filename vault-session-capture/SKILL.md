---
name: vault-session-capture
description: Auto-extract knowledge from the current session to the Hermes Vault. Call this at the END of every significant session (10+ messages, new knowledge discovered).
---

# Vault Session Capture

## Purpose
Capture knowledge from the current session into the Hermes Vault before the session ends. This ensures no knowledge is lost between sessions.

## When to Call
- **End of every significant session** (10+ messages)
- **New concept/decision/person discovered**
- **Technical learning or pitfall found**
- **Before switching to a different topic**

## How to Call
At the end of a session, say: "capture this session to vault" or just invoke this skill directly.

## Steps

1. **Assess**: Does this session contain new knowledge not already in vault?
   - If NO → skip, just note "session captured, no new knowledge"
   - If YES → proceed

2. **Extract**:
   - What new concepts were discussed?
   - What decisions were made?
   - What people were mentioned?
   - What technical learnings emerged?
   - What pitfalls were discovered?

3. **Load vault-update skill** and follow its protocol

4. **Write to vault**:
   - Session summary in `sessions/YYYYMMDD-<topic>.md`
   - New concept/decision/person files if needed
   - Update `index.md`, `_meta/knowledge-map.md`, `.manifest.json`

5. **Confirm**: State what was captured and where

## Integration with Cron
- This skill is for **manual end-of-session capture**
- The cron job `vault-session-ingest` handles **automatic background capture** every 2h
- Both use the same `vault-update` protocol
- If you capture manually, the cron will skip it (already in manifest)

## Response Style

Keep responses concise. User prefers short, direct answers — one sentence when possible, no lengthy explanations unless asked.

## Important
- Don't wait for cron — capture important sessions immediately
- Cron is backup, not primary
- If session has <10 messages and no new knowledge → skip
