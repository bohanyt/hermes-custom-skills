# Hermes Custom Skills

Custom skills untuk [Hermes Agent](https://hermes-agent.nousresearch.com/docs) — dibuat oleh @bohan.

## Daftar Skills (21 custom + scripts)

### Pipeline & Content Factory
- **content-pipeline-builder** — Arsitektur multi-agent content pipeline
- **hermes-python-pipeline** — Python script patterns, VTT parsing, chunking
- **live2video-pipeline** — YouTube livestream → short clips (v1.3)
  - `scripts/` — 22 Python scripts + 17 outdated versions (portable, no API key needed)

### Hermes Operations
- **hermes-multi-session** — Multi-terminal manager, lock/queue, shared DB/vault
- **hermes-save-session** — Force-save session DB, WAL flush
- **hermes-fix-session-index** — Fix unindexed CLI sessions bug
- **hermes-tools/** — Shell scripts untuk multi-session setup

### Vault System
- **vault-query** — Query vault sebelum jawab pertanyaan
- **vault-update** — Write session knowledge ke vault
- **vault-session-capture** — Auto-extract knowledge di akhir session
- **vault-management** — Umbrella + audit workflow

### Content Processing
- **storytime-pipeline** — SRT chunking + keyword-based topic labeling
- **context-delegation** — Context window overload handling

### Communication
- **caveman** — Ultra-compressed communication mode (~75% token reduction)
- **handoff** — Compact conversation untuk agent handoff

### Code & Architecture
- **improve-codebase-architecture** — Find deepening opportunities
- **zoom-out** — Give broader code context
- **grill-me** — Interview user relentlessly about plans

### Enterprise
- **browser-automation-enterprise** — M365/Teams browser automation

### Security & Review (new)
- **security-audit** — OWASP Top 10 + STRIDE security audit (from gstack /cso)
- **retro** — Weekly engineering retrospective (from gstack /retro)
- **ship** — End-to-end shipping workflow, auto PR (from gstack /ship)

## Struktur Folder

```
hermes-skills-export/
+-- live2video-pipeline/
|   +-- SKILL.md              # Pipeline documentation
|   +-- scripts/              # 22 active Python scripts (standalone)
|   |   +-- pipeline_runner.py      # Entry point / orchestrator
|   |   +-- srt_cleaner.py          # Bersihkan SRT
|   |   +-- topic_chunker.py        # Chunk + label transkrip
|   |   +-- pipeline_cutter.py      # Cut video per label
|   |   +-- storytime_scanner.py    # Scan storytime (standalone)
|   |   +-- storytime_keywords.json # Config keyword
|   |   +-- ... (16 lagi)
|   +-- outdated/             # 17 old versions (reference)
+-- storytime-pipeline/
|   +-- SKILL.md
|   +-- scripts/topic_chunker.py
+-- hermes-multi-session/
|   +-- SKILL.md
|   +-- references/ (6 shell scripts + docs)
+-- hermes-tools/             # Multi-session shell scripts
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
+-- zoom-out/                 # SKILL.md only
+-- browser-automation-enterprise/ # SKILL.md + 5 refs + 1 template
+-- README.md
+-- SKILLS_AUDIT.md           # Audit report (duplikat, maturity)
+-- MATURITY_REPORT.md        # Maturity analysis
```

## Cara Pakai

Setiap folder berisi `SKILL.md` (utama) + optional `scripts/`, `references/`, `templates/`.

Untuk install ke Hermes lain:
```bash
# Copy skill folder ke Hermes skills directory
cp -r <skill-name> ~/.hermes/skills/
# atau
cp -r <skill-name> ~/AppData/Local/hermes/skills/
```

Untuk pipeline scripts (standalone, tanpa Hermes):
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
| STUB | 1 | zoom-out (minimal) |

Lihat `MATURITY_REPORT.md` untuk detail.

## Upload Plan (TODO)

- [ ] Buat GitHub repo (private atau public)
- [ ] `git init` + initial commit
- [ ] Push ke GitHub
- [ ] Setup sync script untuk update otomatis

## Catatan

- Semua scripts **standalone** — bisa jalan tanpa Hermes
- Tidak ada API key di files (`.env` di-gitignore)
- Pipeline scripts tested on: GTA Anime NTE stream (2 jam → 40 chunks → storytime detected)
- `hermes-tools/` untuk Windows/MSYS environment
- Vault-related skills dependen pada Hermes Vault setup di `Documents/hermes-vault/`
