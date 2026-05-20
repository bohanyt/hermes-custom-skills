---
name: handoff
description: Compact the current conversation into a handoff document so another agent or future session can continue the work. Use when user says "handoff", "save this for later", "another agent will continue", "compact this", or when context window is running low and work is incomplete.
---

# Handoff

Write a handoff document summarizing the current conversation so a fresh agent can continue the work.

## When to Use

- Context window is running low and work is incomplete
- User says "handoff" or "save this for later"
- Switching from one agent to another
- Ending a long session that will continue later
- Delegating work to a subagent that needs full context

## Process

1. **Summarize the goal** — What are we trying to accomplish?
2. **Document current state** — What's done, what's in progress, what's blocked?
3. **List decisions made** — Key decisions and their rationale.
4. **Note open questions** — What's still unresolved?
5. **Suggest next steps** — What should the next agent do first?
6. **Reference artifacts** — Link to PRDs, plans, ADRs, issues, commits, diffs. Don't duplicate content that already exists in other artifacts.

## Output Format

```markdown
# Handoff: [Brief Title]

**Date:** YYYY-MM-DD
**From:** [Current agent/session]
**To:** [Next agent/session focus]

## Goal
One sentence: what are we building/fixing?

## Current State
- **Done:** [list]
- **In Progress:** [list]
- **Blocked:** [list]

## Key Decisions
1. **Decision:** [what was decided] — **Why:** [rationale]

## Open Questions
- [ ] Question 1
- [ ] Question 2

## Next Steps
1. First thing to do
2. Then...

## Artifacts
- Plan: `docs/plans/...`
- PRD: [link]
- Issue: #[number]
- Branch: `feature/...`
- Commit: `abc1234`

## Skills to Use
- `skill-name` — for [reason]
```

## Save Location

Save to a path like `docs/handoffs/YYYY-MM-DD-title.md` or use `mktemp` for temporary handoffs.

## Integration

- Use `session-vault` to also capture the handoff in the vault for long-term memory.
- Reference the handoff in the next session's context.
