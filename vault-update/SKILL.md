---
name: vault-update
description: Update the Hermes Vault with knowledge from the current session. Extract topics, decisions, concepts, and write to vault. Run at end of session or when user says "simpen" or "save to vault". Now includes AUTOMATED scripts.
---

# Vault Update

## When to Use
- End of session (auto-trigger when session is wrapping up)
- User says "simpen", "save to vault", "update vault"
- Significant new knowledge was created (decisions, concepts, discoveries)

## Config
- Vault path: `C:\Users\<user>\Documents\hermes-vault\`
- Sessions path: `C:\Users\<user>\AppData\Local\hermes\sessions\`

## Automated Scripts

Scripts ada di `scripts/` folder (portable, standalone):

| Script | Purpose | Usage |
|--------|---------|-------|
| `vault_update.py` | Auto-extract sessions → vault | `python vault_update.py [--dry-run]` |
| `vault_concepts.py` | Extract concepts & decisions dari sessions | `python vault_concepts.py [--dry-run]` |

### Quick Run
```bash
# Update vault dari session files
python scripts/vault_update.py

# Extract concepts & decisions
python scripts/vault_concepts.py

# Dry run (preview only)
python scripts/vault_update.py --dry-run
```

### Cron Job (Auto-ingest)
Untuk auto-ingest setiap 2 jam:
```
hermes cron create --schedule "every 2h" --prompt "Run: python ~/Documents/hermes-vault/scripts/vault_update.py"
```

## Manual Update Flow (kalau nggak pake script)

1. **Extract** dari current session:
   - Main topics discussed
   - Decisions made
   - New concepts/ideas introduced
   - People mentioned
   - Action items

2. **Write session summary** to `sessions/YYYY-MM-DD-session-slug.md`

3. **Update/create concept files** in `concepts/` if new concepts emerged

4. **Update/create decision files** in `decisions/` if decisions were made

5. **Update/create people files** in `people/` if new people were discussed

6. **Update index.md** — add entries for new files

7. **Update .manifest.json** — increment counts, add session entry, update timestamp

## Concurrency Safety
- Each session writes its own file (no overwrites)
- Use append for index.md updates
- Check for `.lock` file before writing; if exists, wait 2s and retry

## File Naming
- Sessions: `YYYY-MM-DD-session-slug.md`
- Concepts: `concept-name.md`
- Decisions: `decision-name.md`
- People: `person-name.md`
