---
name: retro
description: "Weekly engineering retrospective. Analyzes commit history, work patterns, and code quality metrics with persistent history and trend tracking. Team-aware: breaks down per-person contributions with praise and growth areas. Use when user says 'weekly retro', 'what did we ship', 'engineering retrospective', or 'retro'."
version: 1.0.0
author: Hermes Agent (adapted from garrytan/gstack /retro)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [retrospective, review, metrics, team, productivity, git]
    related_skills: [security-audit, ship, requesting-code-review]
---

# Weekly Engineering Retrospective

Generates a comprehensive engineering retrospective analyzing commit history, work patterns, and code quality metrics. Team-aware: identifies the user running the command, then analyzes every contributor with per-person praise and growth opportunities.

## When to Use

- User says "weekly retro", "what did we ship", "engineering retrospective", "retro"
- End of work week or sprint
- Before planning next sprint

## Arguments

- `retro` — default: last 7 days
- `retro 24h` — last 24 hours
- `retro 14d` — last 14 days
- `retro 30d` — last 30 days
- `retro compare` — compare current window vs prior same-length window
- `retro compare 14d` — compare with explicit window

## Instructions

Parse the argument to determine the time window. Default to 7 days if no argument given. All times should be reported in the user's **local timezone**.

**Midnight-aligned windows:** For day (`d`) and week (`w`) units, compute an absolute start date at local midnight. For hour (`h`) units, use relative time since midnight alignment does not apply.

### Step 1: Gather Raw Data

First, fetch origin and identify the current user:
- `git config user.name` — this is "you", the person reading this retro
- All other authors are teammates

Run these git commands to gather data:

1. **All commits in window** — timestamps, subject, hash, author, files changed, insertions, deletions
2. **Per-commit test vs total LOC breakdown** — separate test files from production files
3. **Commit timestamps** — for session detection and hourly distribution
4. **Files most frequently changed** — hotspot analysis
5. **PR/MR numbers** from commit messages
6. **Per-author file hotspots** — who touches what
7. **Per-author commit counts** — quick summary
8. **Test file count** — total test files in project
9. **Regression test commits** in window

Also check for:
- `TODOS.md` or `TODO.md` — backlog health
- `CHANGELOG.md` — features shipped
- `.hermes/retros/` — prior retros for trend tracking

### Step 2: Compute Metrics

Calculate and present these metrics:

| Metric | Value |
|--------|-------|
| **Features shipped** (from CHANGELOG + merged PR titles) | N |
| Commits to main | N |
| Contributors | N |
| PRs merged | N |
| **Logical SLOC added** (non-blank, non-comment) | N |
| Raw LOC: insertions | N |
| Raw LOC: deletions | N |
| Test LOC ratio | N% |
| Active days | N |
| Test Health | N total · M added this period |

Then show a **per-author leaderboard**:

```
Contributor         Commits   +/-          Top area
You (name)              32   +2400/-300   src/auth/
alice                   12   +800/-150    app/services/
bob                      3   +120/-40     tests/
```

Sort by commits descending. The current user always appears first, labeled "You (name)".

**Backlog Health (if TODOS.md exists):**
- Total open TODOs
- P0/P1 count (critical/urgent)
- Items completed this period
- Items added this period

### Step 3: Session Detection

Analyze commit timestamps to detect work sessions:
- Group commits by author
- Detect session boundaries (gaps > 2 hours between commits)
- Count sessions per author
- Calculate average session length

```
SESSION ANALYSIS
════════════════
You:        8 sessions, avg 1.2 hours, longest 3.5 hours
Alice:      5 sessions, avg 0.8 hours, longest 2.1 hours
Bob:        2 sessions, avg 0.5 hours, longest 0.8 hours
```

### Step 4: Work Pattern Analysis

Identify patterns in the data:

**Productivity patterns:**
- Peak work hours (when are most commits made?)
- Active days vs inactive days
- Commit frequency trend (increasing / stable / decreasing)

**Code quality signals:**
- Test ratio (test LOC / total LOC) — higher is better
- Deletion ratio (deletions / insertions) — healthy refactoring shows balanced delete/insert
- Hotspot files (frequently changed files may indicate instability)

**Collaboration patterns:**
- Who reviews whose code?
- Are there knowledge silos (only one person touches certain files)?
- Cross-team contributions

### Step 5: Per-Contributor Analysis

For each contributor, provide:

**Praise (what went well):**
- Features shipped
- Code quality improvements
- Test coverage additions
- Helpful reviews or documentation

**Growth areas (constructive feedback):**
- Knowledge silos to break
- Test coverage gaps
- Commit message quality
- Areas to expand into

Be specific and actionable. Never vague.

### Step 6: Trend Tracking (if prior retros exist)

Compare with previous retro periods:

```
TREND (vs prior 7 days)
═══════════════════════
Features shipped:    5 → 8 (+60%)
Commits:             32 → 45 (+41%)
Test ratio:          12% → 18% (+6pp)
Active days:         5 → 6 (+1)
Contributors:        2 → 3 (+1)
```

### Step 7: Retrospective Narrative

Write a narrative summary covering:

1. **What shipped** — features, fixes, improvements
2. **How it went** — velocity, quality, collaboration
3. **What to improve** — specific, actionable items
4. **What to keep doing** — positive patterns to reinforce

### Step 8: Save Retro Report

Save the retro report to `.hermes/retros/YYYY-MM-DD.md` for future trend tracking.

Format:
```markdown
# Engineering Retro — YYYY-MM-DD

## Summary
[2-3 sentence overview]

## Metrics
[metrics table]

## Per-Contributor
[analysis]

## Trends
[if applicable]

## Action Items
- [ ] Item 1
- [ ] Item 2
```

## Voice

- Lead with the point. Say what it does, why it matters.
- Be concrete. Name files, functions, line numbers, and real numbers.
- Be direct about quality. Praise specifically, critique constructively.
- Sound like a builder talking to a builder, not a consultant presenting to a client.
- Never corporate, academic, PR, or hype.
