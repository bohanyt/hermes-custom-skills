---
title: Hermes Web UI Dashboard Discovery & Local Testing
sessions: [20260517_233528_84bcf2]
date: 2026-05-17
platform: cli
model: openrouter/owl-alpha
total_messages: 54 (6 user, 48 assistant)
tags: [hermes-dashboard, web-ui, react, fastapi, local-testing]
---

# Hermes Web UI Dashboard Discovery & Local Testing

**Date:** 2026-05-17 23:35 | **Platform:** CLI | **Messages:** 54

## What Happened

User asked about multi-session UI for Hermes Agent accessible via Chrome. Investigated Hermes built-in Web UI dashboard. Successfully ran it and confirmed it works — accessible from phone browser on same network.

## Discovery: Hermes Has Built-in Web UI

**Stack:**
- **Frontend:** React 19 + TypeScript + Vite + Tailwind CSS v4 (dark theme)
- **Components:** shadcn/ui-style
- **Backend:** FastAPI (`python -m hermes_cli.main web --no-open`, port 9119)
- **Real-time:** WebSocket with JSON-RPC protocol

## Pages Available (12+ pages)

| Page | Path | Function |
|------|------|----------|
| **Sessions** | `/sessions` | List sessions, search, delete, view messages |
| **Chat** | `/chat` | Embedded terminal (xterm.js) + WebSocket PTY |
| **Analytics** | `/analytics` | Usage stats, model analytics |
| **Models** | `/models` | Model info, assignment, opt |
| **Logs** | `/logs` | View logs |
| **Cron** | `/cron` | Manage cron jobs |
| **Skills** | `/skills` | Manage skills |
| **Plugins** | `/plugins` | Manage plugins |
| **Profiles** | `/profiles` | Manage profiles |
| **Config** | `/config` | Edit `config.yaml` via form or raw YAML |
| **Keys** | `/keys` | Manage API keys |
| **Documentation** | `/docs` | View docs |

## Config Page Details

- **Config path:** `C:\USERS\MSI THIN 15\APPDATA\LOCAL\HERMES\CONFIG.YAML`
- **Edit flow:** Edit fields → click **SAVE** (manual save, not auto-apply)
- **YAML mode:** Can switch to raw YAML editor
- **Search filter** in banner
- **28 sections** in sidebar: General (9), Agent (32), Terminal (22), Display (32), etc.
- **Some settings require restart** (model, provider, etc.)

## Local Testing Results

- **Dashboard URL:** `http://172.20.10.10:9119`
- **Phone access:** ✅ Worked on same WiFi network
- **Sessions page showed:** 34 sessions with preview, message count, tools, source
- **Gateway status:** STOPPED (Chat page needs gateway)
- **Auth:** Using `--insecure` flag (no login required)

## Notes

- Docker setup (`SOUL.md` + `entrypoint.sh`) is just the Docker image, not a web UI
- Gateway (Telegram/Discord) is separate from the web UI
- Dashboard runs as **background process** — terminal doesn't need to stay visible
- For server deployment: can run as a Windows service
- User's long-term plan: deploy on office local server with Docker + LM Studio (Gemma 4 e2b Q6)

## Related

- [[hermes-desktop-setup]] — Hermes Desktop + LM Studio setup
- [[cloudflare-tunnel-hermes-remote]] — Making dashboard accessible from internet (session 20260518_061437_f2e056d3)
- [[multi-session-management]] — Session management

## Detail Files

- `sessions/detail/20260517_233528_84bcf2.md` — 54 messages
