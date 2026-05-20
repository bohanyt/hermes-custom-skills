# Session: Skills Enrichment — mattpocock/skills + skills.sh

**Date:** 2026-05-18
**Topic:** Skills enrichment — belajar dari repositori skills orang lain untuk upgrade OWL Agent
**Type:** session-summary

## Goal
Scan semua skills dari 3 sources (GitHub mattpocock/skills, skills.sh marketplace, skills.sh/mattpocock/skills), compare dengan existing Hermes skills, upgrade yang udah ada kalau ada yang lebih bagus, tambah yang baru dan relevan.

## Sources Scanned
1. **github.com/mattpocock/skills** — 34 skills, 91.2k stars. "Skills for Real Engineers"
2. **skills.sh/mattpocock/skills** — Installable via `npx skills add mattpocock/skills`
3. **skills.sh** — Agent Skills Directory, 390k+ installs

## Actions Taken

### 5 New Skills Created
1. `improve-codebase-architecture` — Deep module analysis, deletion test, locality/leverage
2. `grill-me` — Relentless plan interviewing, one question at a time
3. `handoff` — Conversation compaction for agent handoff
4. `caveman` — Ultra-compressed communication (~75% token reduction)
5. `zoom-out` — Higher-level code context / module map

### 5 Skills Upgraded
1. `systematic-debugging` v1→v2 — 4-phase → 6-phase diagnose loop (feedback loop first, 10 loop types, tagged logs, post-mortem)
2. `test-driven-development` v1→v2 — Added horizontal slice anti-pattern, vertical tracer bullets, mocking rules
3. `spike` v1→v2 — Added logic/UI prototype branches, surface state rule, one command to run
4. `writing-plans` v1→v2 — Added vertical slice guidance, HITL vs AFK classification
5. `requesting-code-review` v2→v3 — Added two-axis review (Standards + Spec)

### 1 Skill Patched
- `hermes-agent-skill-authoring` — Added description requirements, when to add scripts, when to split files, review checklist

## Key Concepts Learned
- Ubiquitous Language (CONTEXT.md as glossary not spec)
- Deep vs Shallow modules (deletion test)
- Tracer Bullets / Vertical Slices (one test → one impl → repeat)
- Feedback Loop Debugging (10 ways to construct loops)
- Leverage vs Locality
- Seams (one adapter = hypothetical, two adapters = real)

## Files Created/Modified
- `skills/software-development/improve-codebase-architecture/SKILL.md` — NEW
- `skills/software-development/grill-me/SKILL.md` — NEW
- `skills/productivity/handoff/SKILL.md` — NEW
- `skills/productivity/caveman/SKILL.md` — NEW
- `skills/software-development/zoom-out/SKILL.md` — NEW
- `skills/software-development/systematic-debugging/SKILL.md` — UPGRADED
- `skills/software-development/test-driven-development/SKILL.md` — UPGRADED
- `skills/software-development/spike/SKILL.md` — UPGRADED
- `skills/software-development/writing-plans/SKILL.md` — UPGRADED
- `skills/software-development/requesting-code-review/SKILL.md` — UPGRADED
- `skills/software-development/hermes-agent-skill-authoring/SKILL.md` — PATCHED
- `hermes-vault/concepts/skills-enrichment.md` — NEW (vault concept)
- `hermes-vault/index.md` — UPDATED (added concept, bumped count)
- `Downloads/skills-enrichment-recap.html` — NEW (visual recap)

## Not Added (with reasons)
- triage / to-prd / to-issues — Too GitHub-issue-tracker specific
- grill-with-docs — Domain-specific grilling, can add later
- git-guardrails — Claude Code hooks specific
- setup-pre-commit — Can add later if needed
- obsidian-vault (personal) — Path-specific
- review (in-progress) — Not stable yet
- writing-beats/fragments/shape — Too niche

## Related Concepts
- [[skills-enrichment]]
- [[systematic-debugging]]
- [[test-driven-development]]
- [[spike]]
- [[writing-plans]]
- [[requesting-code-review]]
