# Hermes Custom Skills

Custom skills untuk [Hermes Agent](https://hermes-agent.nousresearch.com/docs) — dibuat & dikumpulkan oleh @bohan.

## Daftar Skills (18 skills + scripts)

### Pipeline & Content Factory
| Skill | Description |
|-------|-------------|
| **content-pipeline-builder** | Arsitektur multi-agent content pipeline |
| **hermes-python-pipeline** | Python script patterns, VTT parsing, chunking |
| **live2video-pipeline** | YouTube livestream → short clips (v1.3) |
| `live2video-pipeline/scripts/` | 22 Python scripts + 17 outdated versions (portable, no API key needed) |

### Hermes Operations
| Skill | Description |
|-------|-------------|
| **hermes-multi-session** | Multi-terminal manager, lock/queue, shared DB/vault |
| `hermes-multi-session/references/` | Shell scripts (lock, safe, multi-launch, save, session-DB docs) |

### Vault System
| Skill | Description |
|-------|-------------|
| **vault-query** | Query vault sebelum jawab pertanyaan |
| **vault-update** | Write session knowledge ke vault |
| **vault-session-capture** | Auto-extract knowledge di akhir session |
| **vault-management** | Umbrella + audit workflow |

### Content Processing
| Skill | Description |
|-------|-------------|
| **storytime-pipeline** | SRT chunking + keyword-based topic labeling |
| **context-delegation** | Context window overload handling |

### Communication
| Skill | Description |
|-------|-------------|
| **caveman** | Ultra-compressed communication mode (~75% token reduction) |
| **handoff** | Compact conversation untuk agent handoff |

### Code & Architecture
| Skill | Description |
|-------|-------------|
| **improve-codebase-architecture** | Find deepening opportunities (deep/shallow modules, deletion test) |
| **grill-me** | Interview user relentlessly about plans |

### Enterprise Automation
| Skill | Description |
|-------|-------------|
| **browser-automation-enterprise** | M365/Teams browser automation, Playwright patterns |

### Security & DevOps (adapted from [gstack](https://github.com/garrytan/gstack))
| Skill | Description |
|-------|-------------|
| **security-audit** | OWASP Top 10 + STRIDE threat modeling |
| **retro** | Weekly engineering retrospective |
| **ship** | End-to-end shipping workflow, auto PR |

### Publishing
| Skill | Description |
|-------|-------------|
| **gitpush** | Push custom skills to GitHub repo for sharing |

## Struktur Folder

```
hermes-custom-skills/
+-- live2video-pipeline/
|   +-- SKILL.md              # Pipeline documentation
|   +-- scripts/              # 22 active Python scripts (standalone)
|   +-- outdated/             # 17 old versions (reference)
+-- storytime-pipeline/
|   +-- SKILL.md
|   +-- scripts/topic_chunker.py
+-- hermes-multi-session/
|   +-- SKILL.md
|   +-- references/           # Shell scripts + docs
+-- vault-query/              # SKILL.md only
+-- vault-update/             # SKILL.md only
+-- vault-session-capture/    # SKILL.md only
+-- vault-management/         # SKILL.md + audit reference
+-- content-pipeline-builder/ # SKILL.md + 2 references
+-- context-delegation/       # SKILL.md only
+-- caveman/                  # SKILL.md only
+-- grill-me/                 # SKILL.md only
+-- handoff/                  # SKILL.md only
+-- improve-codebase-architecture/ # SKILL.md only
+-- browser-automation-enterprise/ # SKILL.md + 5 refs + 1 template
+-- gitpush/                  # SKILL.md (new!)
+-- retro/                    # SKILL.md (from gstack)
+-- security-audit/           # SKILL.md (from gstack)
+-- ship/                     # SKILL.md (from gstack)
+-- README.md
+-- .gitignore
+-- LICENSE
```

## Cara Pakai

### Install ke Hermes lain

```bash
# Via git clone (recommended)
git clone https://github.com/bohanyt/hermes-custom-skills.git
cd hermes-custom-skills

# Copy skill(s) ke Hermes skills directory
cp -r <skill-name> ~/.hermes/skills/
# Windows:
cp -r <skill-name> ~/AppData/Local/hermes/skills/
```

### Install semua sekaligus

```bash
# Linux/Mac:
cp -r */ ~/.hermes/skills/

# Windows (PowerShell):
Get-ChildItem -Directory | Copy-Item -Destination "$env:APPDATA\Local\hermes\skills\" -Recurse
```

### Pipeline scripts (standalone, tanpa Hermes)

```bash
cd live2video-pipeline/scripts
python pipeline_runner.py video.mp4 stream.id.srt
```

## Maturity Levels

| Level | Count | Notes |
|-------|-------|-------|
| PRODUCTION | 9 | Tested, real output, daily driver |
| FUNCTIONAL | 5 | Works but partial/untested |
| REFERENCE | 4 | SOP/documentation only |

## Catatan

- Semua scripts **standalone** — bisa jalan tanpa Hermes
- Tidak ada API key di files (`.env` di-gitignore)
- Pipeline scripts tested on: GTA Anime NTE stream (2 jam → 40 chunks → storytime detected)
- Vault-related skills dependen pada Hermes Vault setup di `Documents/hermes-vault/`
- `security-audit`, `retro`, `ship` adapted dari [gstack](https://github.com/garrytan/gstack) oleh Garry Tan
- `gitpush` — **unique skill**, nggak ada di Hermes default. Push skills ke GitHub langsung dari Hermes
