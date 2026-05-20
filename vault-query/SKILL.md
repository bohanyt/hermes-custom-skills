---
name: vault-query
description: Query the Hermes Vault before answering questions. Scan index.md first, only open relevant files. Use when the user asks about past topics, decisions, or anything that might be in the vault.
---

# Vault Query

## When to Use

- User asks about a topic that might have been discussed before
- User references something from a past session
- Before answering, check if the vault has relevant knowledge
- User explicitly says "cek vault" or "ada di vault?"

## Config

1. Read `~/.obsidian-wiki/config` or check `C:\Users\MSI Thin 15\Documents\hermes-vault\` for vault path
2. Vault path = `C:\Users\MSI Thin 15\Documents\hermes-vault\`

## Query Flow

1. **Read index.md** — scan for relevant topics (cheap, ~100-200 tokens)
2. **Match** — does the user's question relate to any indexed topic?
3. **If yes** — open only the relevant file(s), read summary
4. **If no** — answer normally, no vault lookup needed
5. **Cite** — if vault content is used, mention source: `[vault: filename.md]`

## Output Format

When vault content is relevant:
```
[vault: concepts/vault-project.md] Based on what we discussed before...
```

When no vault content:
- Answer normally, no citation needed

## Examples

User: "aku udah pernah setup vault belum?"
→ Read index.md → find vault-project entry → open file → answer with citation

User: "gimana cara fix rate limit?"
→ Read index.md → no match → answer normally
