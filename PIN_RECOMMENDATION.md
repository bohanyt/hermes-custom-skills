# PIN Recommendation — FINAL
# Generated: 2026-05-20

## Token Budget Analysis

Total context window: ~128K tokens
System prompt (est): ~2-4K tokens
**Available for skills: ~8-12K tokens** (sisanya buat conversation)

## Custom Skills PIN Cost

| Skill | Tokens | Always On? | Worth It? |
|-------|--------|------------|-----------|
| caveman | 493 | ✅ Yes — communication style | ⭐ WORTH |
| vault-query | 393 | ✅ Yes — cek vault sebelum jawab | ⭐ WORTH |
| vault-update | 838 | ⚠️ End of session only | ❌ On-demand |
| vault-session-capture | 509 | ⚠️ End of session only | ❌ On-demand |
| handoff | 540 | ⚠️ Context full only | ❌ On-demand |
| grill-me | 592 | ⚠️ Before implementation | ❌ On-demand |
| zoom-out | 287 | ⚠️ User confused only | ❌ On-demand |
| **TOTAL CUSTOM** | **3652** | | |

## Default Skills PIN Cost

| Skill | Tokens | Always On? | Worth It? |
|-------|--------|------------|-----------|
| hermes-agent | 12,553 | ⚠️ Self-config only | ❌ TOO BIG |
| hermes-agent-skill-authoring | 2,306 | ⚠️ Writing skills only | ❌ On-demand |
| writing-plans | 2,041 | ✅ Yes — plan before execute | ⭐ WORTH |
| requesting-code-review | 2,379 | ⚠️ Before commit only | ❌ On-demand |
| systematic-debugging | 3,002 | ⚠️ Debugging only | ❌ On-demand |
| **TOTAL DEFAULT** | **22,281** | | |

## 📌 FINAL PIN LIST (4 skills, ~5K tokens)

### Custom (2)
1. **caveman** (493 tokens) — Communication style, harusnya always on
2. **vault-query** (393 tokens) — Cek vault sebelum jawab, harusnya always on

### Default (2)
3. **writing-plans** (2,041 tokens) — Plan dulu sebelum eksekusi
4. **systematic-debugging** (3,002 tokens) — Debug terstruktur

**Total PIN cost: ~5,929 tokens** (~4.6% of 128K context)

## ❌ NOT PINNED — On Demand

### Custom (5)
- vault-update — End of session
- vault-session-capture — End of session
- handoff — Context full
- grill-me — Before implementation
- zoom-out — User confused

### Default (3)
- hermes-agent — Too big (12K), on-demand
- hermes-agent-skill-authoring — Writing skills only
- requesting-code-review — Before commit only

## Summary

| Category | Count | Tokens |
|----------|-------|--------|
| 📌 PIN (always on) | 4 | ~5,929 |
| ✅ On-demand | 40+ | loaded as needed |
| 🗑️ Archived | 26 | 0 (not loaded) |

## How to PIN

```bash
# Pin custom skills
hermes skills pin caveman
hermes skills pin vault-query

# Pin default skills
hermes skills pin writing-plans
hermes skills pin systematic-debugging
```

## How to ARCHIVE (already done)

26 skills moved to `.archive/` folder:
- apple-notes, apple-reminders, findmy, imessage, macos-computer-use
- minecraft-modpack-server, pokemon-player
- heartmula, songsee, songwriting-and-ai-music
- dspy, llama-cpp, obliteratus, weights-and-biases
- godmode
- airtable, blogwatcher, dogfood, linear, nano-pdf, notion, polymarket, research-paper-writing, touchdesigner-mcp
- xurl, popular-web-designs, pretext
