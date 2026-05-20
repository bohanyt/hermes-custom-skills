# Skills Audit Report — FINAL
# Generated: 2026-05-20

## Executive Summary

- **Truly custom skills**: 18 (not in bundled manifest, created by user/OWL)
- **Default skills misidentified as custom**: 1 (creative-ideation = default ideation)
- **Internal overlaps**: 3 groups (vault, pipeline, hermes-ops) — NOT duplicates, complementary
- **Default skills auto-upgraded by Hermes**: 70+ (hash mismatch = normal Hermes update)
- **Default skills with user modification**: 0 confirmed
- **Total files in export**: 59 (18 custom skills + hermes-tools + README + this audit)

---

## 1. CUSTOM SKILLS — Complete List (18)

### A. Pipeline & Content Factory (3)

| Skill | Path | Size | Description |
|-------|------|------|-------------|
| content-pipeline-builder | root | 368 lines | Multi-agent content pipeline architecture, 9-stage flow, Windows workarounds |
| hermes-python-pipeline | root | 250 lines | Python script patterns, VTT parsing, chunking, API config |
| live2video-pipeline | mlops/ | 382 lines | YouTube livestream → short clips, topic-first approach, 5C storytelling |

**Overlap**: content-pipeline-builder = architecture layer, hermes-python-pipeline = coding patterns, live2video-pipeline = specific implementation. All 3 reference each other. Keep all.

### B. Hermes Operations (4)

| Skill | Path | Size | Description |
|-------|------|------|-------------|
| hermes-multi-session | root | 216 lines | Multi-terminal manager, lock/queue, shared DB/vault |
| hermes-save-session | root | 61 lines | Force-save session DB, WAL flush |
| hermes-fix-session-index | root | 67 lines | Fix unindexed CLI sessions (Hermes v0.14.0 bug) |
| hermes-tools/ | Documents/ | 8 files | Shell scripts (lock, save, fix, multi-launch) |

**Overlap**: Each solves different problem. hermes-tools/ contains scripts referenced by the 3 skills. Keep all.

### C. Vault System (4)

| Skill | Path | Size | Description |
|-------|------|------|-------------|
| vault-query | .hermes/ | 44 lines | Query vault before answering questions |
| vault-update | .hermes/ | 76 lines | Write session knowledge to vault |
| vault-session-capture | devops/ | 55 lines | Auto-extract at end of significant session |
| vault-management | devops/ | 41 lines | Umbrella + audit workflow, references other 3 |

**Overlap**: vault-management is the umbrella. vault-query/read, vault-update/write, vault-session-capture/auto. Keep all 4.

### D. Storytime & Clipping (1)

| Skill | Path | Size | Description |
|-------|------|------|-------------|
| storytime-pipeline | devops/ | 196 lines | SRT chunking + keyword-based topic labeling, 8 video types |

### E. Context & Delegation (1)

| Skill | Path | Size | Description |
|-------|------|------|-------------|
| context-delegation | devops/ | 69 lines | Context window overload handling, batch processing |

### F. Communication Modes (2)

| Skill | Path | Size | Description |
|-------|------|------|-------------|
| caveman | productivity/ | 42 lines | Ultra-compressed communication, ~75% token reduction |
| handoff | productivity/ | 73 lines | Compact conversation for agent handoff |

### G. Code & Architecture (2)

| Skill | Path | Size | Description |
|-------|------|------|-------------|
| improve-codebase-architecture | software-dev/ | 65 lines | Find deepening opportunities, module depth analysis |
| zoom-out | software-dev/ | 29 lines | Give broader code context, module map |

### H. Planning & Interview (1)

| Skill | Path | Size | Description |
|-------|------|------|-------------|
| grill-me | software-dev/ | 44 lines | Interview user relentlessly about plans |

### I. Enterprise Automation (1)

| Skill | Path | Size | Description |
|-------|------|------|-------------|
| browser-automation-enterprise | software-dev/ | 639 lines | M365/Teams browser automation, Playwright patterns |

---

## 2. DEFAULT SKILLS — Misidentified as Custom

| Skill | Actual Status | Notes |
|-------|--------------|-------|
| creative-ideation | **DEFAULT bundled** | author: SHL0MS, v1.0.0. Name in folder is "creative-ideation" but frontmatter says "ideation". Already removed from export. |

---

## 3. DEFAULT SKILLS — Auto-Upgraded by Hermes

70+ default skills show hash mismatch vs bundled manifest. This is **normal Hermes auto-update behavior** — not user modification. All were updated in batch on May 17 23:28 (Hermes upgrade).

3 skills were further upgraded on May 19:
- devops/kanban-worker (v2.0.0)
- creative/baoyu-article-illustrator
- autonomous-ai-agents/kanban-codex-lane

These are all default bundled skills. No user modification detected.

---

## 4. DEFAULT SKILLS — Related to Custom (NOT Overlapping)

These default skills are in the same domain as custom skills but serve different purposes:

| Default Skill | Custom Counterpart | Relationship |
|--------------|-------------------|--------------|
| session-vault (note-taking/) | vault-query, vault-update | Default = generic vault. Custom = specific to user's vault setup with Windows paths, audit workflow |
| writing-plans (software-dev/) | handoff | Default = implementation plans. Custom = conversation compaction for agent handoff |
| kanban-orchestrator (devops/) | context-delegation | Default = kanban routing. Custom = context window overload handling |
| kanban-worker (devops/) | — | Default kanban worker. No custom equivalent. |
| ideation (creative/) | — | Default creative ideation. Was misidentified as custom. |

**Verdict**: No overlap. Default and custom skills serve different purposes.

---

## 5. CONSOLIDATION OPTIONS

If you want to reduce 18 skills:

### Option A: Merge by Domain (18 → 12)

| Merged Skill | Contains |
|-------------|----------|
| content-factory | content-pipeline-builder + hermes-python-pipeline + live2video-pipeline |
| hermes-ops | hermes-multi-session + hermes-save-session + hermes-fix-session-index |
| vault | vault-query + vault-update + vault-session-capture + vault-management |
| devops-utils | context-delegation + storytime-pipeline |
| code-tools | improve-codebase-architecture + zoom-out + grill-me |
| comms | caveman + handoff |
| browser-automation-enterprise | (keep as-is) |

### Option B: Keep All 18

Skills are modular and reference each other. No strong reason to consolidate unless you want fewer folders.

---

## 6. EXPORT FOLDER STATUS

```
Documents/hermes-skills-export/
├── browser-automation-enterprise/     (7 files)
├── caveman/                           (1 file)
├── content-pipeline-builder/          (3 files)
├── context-delegation/                (1 file)
├── grill-me/                          (1 file)
├── handoff/                           (1 file)
├── hermes-fix-session-index/          (2 files)
├── hermes-multi-session/              (7 files)
├── hermes-python-pipeline/            (3 files)
├── hermes-save-session/               (2 files)
├── hermes-tools/                      (8 files)
├── improve-codebase-architecture/     (1 file)
├── live2video-pipeline/               (10 files)
├── storytime-pipeline/                (2 files)
├── vault-management/                  (2 files)
├── vault-query/                       (1 file)
├── vault-session-capture/             (1 file)
├── vault-update/                      (1 file)
├── zoom-out/                          (1 file)
├── README.md
└── SKILLS_AUDIT.md (this file)

Total: 20 folders, 59 files
```

---

## 7. RECOMMENDATION

1. **No duplicates found** — all 18 custom skills are unique
2. **No default skills need export** — all defaults are either unmodified or auto-upgraded by Hermes
3. **Export folder is ready** for GitHub upload
4. **Optional**: Consolidate to 12 skills if desired (Option A above)
