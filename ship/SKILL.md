---
name: ship
description: "End-to-end shipping workflow: detect base branch, merge, run tests, review diff, bump VERSION, update CHANGELOG, commit, push, create PR. Use when user says 'ship', 'deploy', 'push to main', 'create a PR', 'merge and push', 'ship it', or 'get it deployed'."
version: 1.0.0
author: Hermes Agent (adapted from garrytan/gstack /ship)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [ship, deploy, release, pr, workflow, automation]
    related_skills: [requesting-code-review, security-audit, retro, github-pr-workflow]
---

# Ship Workflow

End-to-end shipping workflow. Detect base branch → merge → run tests → review diff → bump VERSION → update CHANGELOG → commit → push → create PR.

**Core principle:** The user said "ship" which means DO IT. Run straight through. Only stop for real blockers.

## When to Use

- User says "ship", "deploy", "push to main", "create a PR", "merge and push", "ship it", "get it deployed"
- Code is ready and user wants to ship

## Stop Conditions

**Only stop for:**
- On the base branch (abort — ship from a feature branch)
- Merge conflicts that can't be auto-resolved
- Test failures that are clearly caused by the current changes
- Pre-landing review finds issues that need user judgment

**Never stop for:**
- Uncommitted changes (always include them)
- Version bump choice (auto-pick PATCH)
- CHANGELOG content (auto-generate from diff)
- Commit message (auto-generate)

## Workflow

### Step 0: Detect Platform and Base Branch

Detect the git hosting platform:
- Check `git remote get-url origin` for "github.com" or "gitlab"
- Or check CLI: `gh auth status` (GitHub) / `glab auth status` (GitLab)

Determine the base branch:
1. Try: `gh pr view --json baseRefName -q .baseRefName` (GitHub) or `glab mr view` (GitLab)
2. Fallback: `gh repo view --json defaultBranchRef -q .defaultBranchRef.name`
3. Git-native: `git symbolic-ref refs/remotes/origin/HEAD`
4. Last resort: try `origin/main`, then `origin/master`

### Step 1: Pre-flight

1. Check current branch. If on the base branch, **abort**: "You're on the base branch. Ship from a feature branch."
2. Run `git status` to see uncommitted changes
3. Run `git diff <base>...HEAD --stat` and `git log <base>..HEAD --oneline` to understand what's being shipped
4. Check if diff is >200 lines — if so, recommend running a review first

### Step 2: Merge Base Branch

Fetch and merge the base branch into the feature branch so tests run against the merged state:

```
git fetch origin <base> && git merge origin/<base> --no-edit
```

**If merge conflicts:** Try to auto-resolve simple ones (VERSION, CHANGELOG ordering). If complex, **STOP** and show conflicts.

### Step 3: Run Tests

Detect and run the project's test suite:

**Detect test framework:**
- Node.js: `jest`, `vitest`, `mocha`, `playwright` (check `package.json` scripts)
- Ruby: `rspec`, `minitest` (check `Gemfile`)
- Python: `pytest`, `unittest` (check `pyproject.toml`, `setup.py`)
- Go: `go test`
- Rust: `cargo test`
- PHP: `phpunit`
- Elixir: `mix test`

**Run tests:**
- Use the appropriate test command for the detected framework
- If no test framework detected, skip with note: "No test framework detected — skipping tests"

**If tests fail:**
- Analyze failure output
- If failures are clearly caused by current changes: **STOP** and report
- If failures are pre-existing: note them and continue

### Step 4: Pre-Landing Review

Run a quick review of the diff:

1. Check for SQL safety issues
2. Check for LLM trust boundary violations
3. Check for conditional side effects
4. Check for hardcoded secrets
5. Check for obvious bugs or logic errors

If issues found that need user judgment, **STOP** and report. Otherwise continue.

### Step 5: Distribution Pipeline Check

If the diff introduces a new standalone artifact (CLI binary, library package):
- Check for a release workflow (`.github/workflows/release.yml`, etc.)
- If no release pipeline exists, warn but don't block

### Step 6: Version Bump

Check if VERSION file or version in `package.json`/`Cargo.toml`/etc. needs bumping:

**Version bump rules:**
- If CHANGELOG has breaking changes → MAJOR bump
- If CHANGELOG has new features → MINOR bump
- Otherwise → PATCH bump (default)

Auto-patch if no user input available. Update:
- `VERSION` file (if exists)
- `package.json` version field (if exists)
- `Cargo.toml` version field (if exists)
- Any other version files

### Step 7: Update CHANGELOG

Auto-generate CHANGELOG entry from commits since base branch:

```markdown
## [vX.Y.Z] — YYYY-MM-DD

### Features
- [Feature description from commit message]

### Fixes
- [Fix description from commit message]

### Security
- [Security fix from commit message]
```

Prepend to `CHANGELOG.md` (or create if doesn't exist).

### Step 8: Stage and Commit

Stage all intentional changes:
```
git add -A
```

**IMPORTANT:** Review what you're staging. Don't commit:
- `node_modules/`, `venv/`, `.venv/`
- Build artifacts (`dist/`, `build/`, `*.o`, `*.pyc`)
- IDE files (`.vscode/`, `.idea/`)
- OS files (`.DS_Store`, `Thumbs.db`)

Commit with auto-generated message:
```
git commit -m "chore(ship): bump version to vX.Y.Z, update CHANGELOG"
```

### Step 9: Push

```
git push origin <current-branch>
```

If push fails due to remote changes, pull and retry.

### Step 10: Create PR

**If GitHub:**
```
gh pr create --title "<title>" --body "<body>"
```

**If GitLab:**
```
glab mr create --title "<title>" --description "<body>"
```

**PR title:** Use the first commit message or a summary of changes

**PR body template:**
```markdown
## Summary
[What changed and why]

## Changes
- Change 1
- Change 2

## Testing
- [ ] Tests pass
- [ ] Manual testing done (if applicable)

## Checklist
- [ ] Version bumped
- [ ] CHANGELOG updated
- [ ] No hardcoded secrets
- [ ] No merge conflicts
```

### Step 11: Report

Print the PR URL and summary:

```
SHIPPED ✓
══════════
PR: https://github.com/user/repo/pull/123
Branch: feature/xyz → main
Version: v1.2.3 → v1.2.4
Commits: 5
Files changed: 12
```

## Voice

- Lead with the point. Say what shipped and what changed.
- Be concrete. Name files, functions, line numbers, and real numbers.
- Be direct about quality. Bugs matter. Edge cases matter.
- Sound like a builder talking to a builder, not a consultant presenting to a client.
- Never corporate, academic, PR, or hype.
