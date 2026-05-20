---
name: vault-update
description: Update the Hermes Vault with knowledge from the current session. Extract topics, decisions, concepts, and write to vault. Run at end of session or when user says "simpen" or "save to vault".
---

# Vault Update

## When to Use

- End of session (auto-trigger when session is wrapping up)
- User says "simpen", "save to vault", "update vault"
- Significant new knowledge was created (decisions, concepts, discoveries)

## Config

- Vault path: `C:\Users\MSI Thin 15\Documents\hermes-vault\`

## Update Flow

1. **Extract** from current session:
   - Main topics discussed
   - Decisions made
   - New concepts/ideas introduced
   - People mentioned
   - Action items

2. **Write session summary** to `sessions/YYYY-MM-DD-session-slug.md`:
   ```markdown
   ---
   title: Session Title
   date: YYYY-MM-DD
   model: model-name
   tags: [session, topic1, topic2]
   ---
   
   ## Summary
   2-3 sentence summary of the session.
   
   ## Topics
   - Topic 1: brief description
   - Topic 2: brief description
   
   ## Decisions
   - Decision 1: context + outcome
   
   ## Concepts
   - [[concept-name]]: brief definition
   
   ## Action Items
   - [ ] Item 1
   - [ ] Item 2
   ```

3. **Update/create concept files** in `concepts/` if new concepts emerged

4. **Update/create decision files** in `decisions/` if decisions were made

5. **Update/create people files** in `people/` if new people were discussed

6. **Update index.md** — add entries for new files

7. **Update .manifest.json** — increment counts, add session entry, update timestamp

## Concurrency Safety

- Each session writes its own file (no overwrites)
- Use append for index.md updates
- Check for `.lock` file before writing; if exists, wait 2s and retry
- Create `.lock` → write → remove `.lock`

## File Naming

- Sessions: `YYYY-MM-DD-session-slug.md` (e.g., `2026-05-17-vault-setup.md`)
- Concepts: `concept-name.md` (e.g., `rag-pattern.md`)
- Decisions: `decision-name.md` (e.g., `vault-path-decision.md`)
- People: `person-name.md` (e.g., `andrej-karpathy.md`)
