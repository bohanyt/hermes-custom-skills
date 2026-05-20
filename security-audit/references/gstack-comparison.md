# gstack vs Hermes Skills Comparison (2026-05-20)

Research findings from comparing garrytan/gstack skills with existing Hermes skills.

## Adopted into Hermes

1. **security-audit** — from gstack `/cso`. 14-phase security audit: architecture, secrets, dependencies, CI/CD, infrastructure, webhooks, OWASP Top 10, STRIDE, active verification, LLM security, trend tracking.
2. **retro** — from gstack `/retro`. Weekly engineering retrospective with commit analysis, session detection, per-contributor breakdowns, trend tracking.
3. **ship** — from gstack `/ship`. End-to-end shipping: detect base, merge, test, review, version bump, CHANGELOG, commit, push, PR.

## Not Adopted

- agent-deck: Windows incompatible
- mem0: redundant dengan vault
- nano.py: ga practical
- pi: TypeScript beda ekosistem
- langfuse: ga perlu cost tracking
