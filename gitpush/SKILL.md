---
name: gitpush
description: "Push custom Hermes skills to a GitHub repo for sharing. Creates or updates skill folders with proper SKILL.md frontmatter, staged commit with descriptive message, and push to remote. Use when user says 'gitpush', 'push skill', 'share skill', 'upload skill to github', 'publish skill', or wants to sync skills to hermes-custom-skills repo."
version: "1.0.0"
author: OWL / Bohan
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [git, github, share, publish, skills, automation, collaboration]
    related_skills: [skills-packaging]
---

# GitPush — Share Skills to GitHub

Push local custom Hermes skills to a GitHub repository for sharing with others. Handles staging, committing, and pushing with proper metadata.

## When to Use

- User says "gitpush", "push skill", "share this skill", "publish skill"
- After creating or updating a custom skill that should be shared
- Syncing local skills to `hermes-custom-skills` repo (or similar)

## Configuration

Default repo path (Windows):
```
C:\Users\<user>\hermes-custom-skills\
```

Default remote: `origin main`

Customize by setting environment variables or passing args:
- `HERMES_SKILLS_REPO` — path to local skills repo (default: `~/hermes-custom-skills`)
- `HERMES_SKILLS_REMOTE` — git remote name (default: `origin`)
- `HERMES_SKILLS_BRANCH` — git branch (default: `main`)

## Process

### 1. Identify Skill to Push

Ask the user which skill(s) to push, or infer from context.

Sources:
- Local skills: `~/.hermes/skills/<skill-name>/` (or `~/AppData/Local/hermes/skills/<skill-name>/` on Windows)
- Inline skill content (user provides SKILL.md text directly)
- Skill from any path user specifies

### 2. Validate

Before pushing, verify the skill has:

1. **Valid frontmatter** — `name` field required, `description` recommended
2. **SKILL.md present** — must exist at `<skill-name>/SKILL.md`
3. **No secrets** — scan for API keys, tokens, passwords. Warn if found.
4. **No absolute paths** — scan for user-specific paths like `C:\Users\<name>\`. Replace with `~` or `$HOME`.

```bash
# Validate frontmatter
head -10 <skill-name>/SKILL.md | grep "^name:"

# Check for secrets (basic)
grep -inE "(api_key|apikey|token|password|secret)" <skill-name>/SKILL.md

# Check for absolute paths  
grep -inE "C:\\\\Users" <skill-name>/SKILL.md
```

### 3. Copy to Repo

```bash
# Copy skill folder to repo (preserve existing repo structure)
cp -r <source-skill-path> <repo-path>/<skill-name>/

# If skill already exists in repo, merge (don't overwrite — check first)
if [ -d "<repo-path>/<skill-name>" ]; then
    echo "Skill already exists in repo. Showing diff..."
    diff -r <repo-path>/<skill-name>/ <source-skill-path>/ || true
fi
```

### 4. Commit & Push

```bash
cd <repo-path>

# Stage specific skill only
git add <skill-name>/

# Descriptive commit message
msg="skill(<skill-name>): <brief description>

<optional body with details>"

git commit -m "$msg"
git push <remote> <branch>
```

### 5. Update README

After pushing, update the repo's `README.md`:
- Add/update entry in skill list table
- Update count badges if present
- Update "last updated" timestamp

### 6. Verify

```bash
# Confirm push succeeded
git log --oneline -1

# Show remote status
git status
```

## Batch Push

To push multiple skills at once:

```bash
# Stage all skill folders
cd <repo-path>
git add <skill1>/ <skill2>/ <skill3>/

# Single commit with all skills
git commit -m "skills: push <skill1>, <skill2>, <skill3>

- <skill1>: <what changed>
- <skill2>: <what changed>"

git push origin main
```

## Creating a New Skill Directly in Repo

If the user wants to create a brand new skill and push it:

1. Create folder: `mkdir -p <repo-path>/<skill-name>`
2. Write `SKILL.md` with proper frontmatter (see `hermes-agent-skill-authoring` format)
3. Add supporting files: `scripts/`, `references/`, `templates/` as needed
4. Validate (step 2 above)
5. Commit & push (step 4 above)

## Frontmatter Template

Minimum required frontmatter for a shareable skill:

```yaml
---
name: <skill-name>
description: "<What it does>. Use when <trigger conditions>."
version: "1.0.0"
author: <your name>
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [tag1, tag2, tag3]
---
```

## Safety Rules

1. **Never push secrets** — always scan before commit
2. **Never force push** — use regular `git push` only
3. **Never push `.env` files** — ensure `.gitignore` excludes them
4. **Ask before overwriting** — if skill exists in repo, show diff and confirm
5. **One skill per commit** — unless batch push explicitly requested

## Repo Structure Convention

```
hermes-custom-skills/
├── <skill-name>/
│   ├── SKILL.md          # Required — main skill file
│   ├── scripts/           # Optional — executable scripts
│   ├── references/        # Optional — documentation
│   └── templates/         # Optional — templates
├── README.md              # Auto-updated
├── .gitignore             # Must include .env, *.key, *secret*
└── LICENSE                # Recommended
```

## Integration

- Use `hermes-agent-skill-authoring` for SKILL.md format validation
- Use `skills-packaging` for maturity assessment before publishing
- Use `github-repo-management` if repo setup/clone is needed first
