# Hermes Vault — Master Index

> Extended memory untuk semua sesi Hermes. Terindex per topik, bisa di-query tanpa bawa semua history ke context.

## Status

- **Sessions**: 47 topic summaries
- **Concepts**: 41
- **Decisions**: 13
- **People**: 1
- **Cron**: `vault-update-auto` — runs every 2h for new sessions + LLM summary
- **Last updated**: 2026-05-20

## Cara Pakai

1. **Sebelum jawab pertanyaan** → cek index ini, cari topik yang relevan
2. **Kalo nemu yang relevan** → buka file yang bersangkutan, baca ringkasannya
3. **Butuh detail?** → buka `sessions/detail/` untuk condensed conversation
4. **Butuh raw?** → buka file JSON asli di `AppData/Local/hermes/sessions/`

## Quick Navigation

- 🗺️ [_meta/knowledge-map.md](_meta/knowledge-map.md) — Peta pengetahuan utama
- 🔧 [_meta/hermes-patterns.md](_meta/hermes-patterns.md) — Pattern & pitfalls
- 🎬 [concepts/live2video-pipeline.md](concepts/live2video-pipeline.md) — Live2Video pipeline
- 🤖 [concepts/copilot-m365-pipeline.md](concepts/copilot-m365-pipeline.md) — Copilot M365 automation
- 🏠 [concepts/hermes-desktop-setup.md](concepts/hermes-desktop-setup.md) — Hermes Desktop + LM Studio
- ⚖️ [concepts/kiro-judger.md](concepts/kiro-judger.md) — Kiro sebagai judger/auditor
- 🏗️ [concepts/multi-agent-architecture.md](concepts/multi-agent-architecture.md) — 4-agent architecture

## Sessions

### Live2Video Pipeline
- [20260518-live2video-v1.3-final](sessions/20260518-live2video-v1.3-final.md) — v1.3 5C long-form video, 213 messages
- [20260516-17-live2video-pipeline-v1.2](sessions/20260516-17-live2video-pipeline-v1.2.md) — v1.0→v1.2 full development, ~2272 messages

### Copilot M365 & Browser Automation
- [20260515-17-copilot-automation-hermes-desktop](sessions/20260515-17-copilot-automation-hermes-desktop.md) — Copilot automation + Hermes Desktop, ~900 messages
- [20260515-17-copilot-cloakbrowser](sessions/20260515-17-copilot-cloakbrowser.md) — CloakBrowser evaluation, ~350 messages

### Hermes Desktop & Local AI
- [20260516-hermes-desktop-setup](sessions/20260516-hermes-desktop-setup.md) — LM Studio setup & testing, ~1800 messages

### AionUI Troubleshooting
- [20260514-aionui-troubleshooting](sessions/20260514-aionui-troubleshooting.md) — Process management, rate limiting, ~215 messages

### Vault & Skills
- [20260517-vault-setup](sessions/20260517-vault-setup.md) — Vault architecture & implementation, ~1500 messages
- [20260518-vault-audit-repair](sessions/20260518-vault-audit-repair.md) — Full vault audit, cron fix, skill creation
- [20260518-skills-enrichment](sessions/20260518-skills-enrichment.md) — Skills enrichment from mattpocock/skills + skills.sh
- [20260520-skills-custom](sessions/20260520-skills-yang-udah-dibuat--bukan-bawaan-dari-hermes-.md) — Custom skills audit, 18 skills identified

### Multi-Session
- [20260520-multi-session](sessions/20260520-biar-beda-sesi-beda-api--gimana-cara-biar-aku-bisa.md) — Multi-session API key strategy, ~150 messages

### First Contact & Setup
- [20260513-01-first-contact](sessions/20260513-01-first-contact.md) — First contact via Discord, greeting
- [20260515-whatsapp-setup](sessions/20260515-whatsapp-setup.md) — WhatsApp connection setup
- [20260515-discord-connection-test](sessions/20260515-discord-connection-test.md) — Discord connection test & session management

### Kiro & Architecture
- [20260519-kiro-4agent-architecture](sessions/20260519-kiro-4agent-architecture.md) — Kiro judger + 4-agent design, ~45 messages

### Misc Testing
- [20260516-misc-testing](sessions/20260516-misc-testing.md) — Miscellaneous testing sessions

## Concepts

### Pipeline & Automation
- [live2video-pipeline](concepts/live2video-pipeline.md) — Automated video content production
- [live2video-detailed](concepts/live2video-detailed.md) — Detailed pipeline knowledge
- [live2video-troubleshooting](concepts/live2video-troubleshooting.md) — Problems & solutions evolution
- [copilot-m365-pipeline](concepts/copilot-m365-pipeline.md) — Browser automation for M365 Copilot
- [playwright-m365-automation](concepts/playwright-m365-automation.md) — Playwright technical details

### Hermes Setup & Config
- [hermes-desktop-setup](concepts/hermes-desktop-setup.md) — Hermes Desktop + LM Studio
- [lm-studio-integration](concepts/lm-studio-integration.md) — LM Studio integration guide
- [multi-session-management](concepts/multi-session-management.md) — Multi-session, AionUI, context management
- [hermes-web-ui](concepts/hermes-web-ui.md) — Hermes built-in Web UI dashboard
- [cloudflare-tunnel](concepts/cloudflare-tunnel.md) — Cloudflare Tunnel for remote access

### Vault & Memory
- [vault-pattern](concepts/vault-pattern.md) — Extended memory via indexed knowledge base
- [seo-memory](concepts/seo-memory.md) — Indexed knowledge for efficient retrieval
- [concurrency-lock](concepts/concurrency-lock.md) — File-based locking for multi-session writes

### Skills & Architecture
- [skills-enrichment](concepts/skills-enrichment.md) — Skills enrichment from external sources
- [kiro-judger](concepts/kiro-judger.md) — Kiro sebagai judger/auditor
- [multi-agent-architecture](concepts/multi-agent-architecture.md) — 4-agent security-first architecture

## Decisions

- [vault-path](decisions/vault-path.md) — Vault stored at `C:\Users\MSI Thin 15\Documents\hermes-vault/`
- [reject-cloakbrowser](decisions/reject-cloakbrowser.md) — CloakBrowser rejected for enterprise SaaS
- [custom-vault-over-framework](decisions/custom-vault-over-framework.md) — Custom vault instead of obsidian-wiki
- [vision-model-selection](decisions/vision-model-selection.md) — Nemotron Nano 12B VL for vision
- [html-context-preservation](decisions/html-context-preservation.md) — HTML files for cross-session knowledge
- [context-window-override](decisions/context-window-override.md) — Gemma 4 context window override

## People

- [andrej-karpathy](people/andrej-karpathy.md) — LLM Wiki pattern, knowledge base methodology
