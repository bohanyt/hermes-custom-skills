---
title: AionUI Troubleshooting & Process Management
sessions: [20260514_083636_de88e5, 20260514_085509_2e3068, 20260514_090128_1d6118]
date: 2026-05-14
platform: cli
model: openrouter/owl-alpha
total_messages: ~215 (combined)
tags: [aionui, troubleshooting, process-management, multi-session]
---

# AionUI Troubleshooting & Process Management

**Date:** 2026-05-14 | **Platform:** CLI | **Combined messages:** ~215

## What Happened

Multiple sessions troubleshooting AionUI (Hermes frontend) issues: why it sometimes doesn't start, how to kill it properly, and multi-session rate limiting problems.

## Key Learnings

### Why AionUI Sometimes Doesn't Start

1. **Gateway not running** — AionUI is just frontend, Hermes Gateway (backend) must be running first
2. **Port conflict** — Gateway uses port 3578; if another process uses it, gateway can't start
3. **Token expired / rate limit** — Cloud provider (OpenRouter) token may expire or hit quota
4. **Config file corrupt** — `config.yaml` corruption prevents startup
5. **Network issues** — Hermes needs internet for LLM API calls

### Multi-Session Rate Limiting

**Problem:** 3 sessions (1 terminal + 2 AionUI) using same API key → rate limit / hang

**Causes:**
- Rate limit / concurrent request limit per API key
- Context window sharing across sessions
- Token bucket drain with multiple active sessions

**Solutions:**
- Close idle sessions when working in one
- Check rate limit dashboard (OpenRouter)
- Use different model/provider per session
- Set fallback provider (Gemini as backup for OpenRouter)

### How to Kill AionUI Properly

**Don't kill individual `hermes acp` processes** — AionUI auto-spawns new ones.

**Correct approach:**
1. Close AionUI app directly (Task Manager or system tray)
2. Or kill all `hermes acp` processes (not `hermes chat --yolo`)
3. Verify with `tasklist | findstr hermes`

**Process identification:**
- `hermes.exe chat --yolo` = CLI session (DON'T KILL)
- `hermes acp` = AionUI session (safe to kill)
- Parent process: `cmd.exe` for AionUI, `powershell` for CLI

### Memory Safety

**Killing process ≠ losing memory.** Session data is stored in files (`~/AppData/Local/hermes/`), not in process memory. Restarting loads from disk.

## Related

- [[multi-session-management]] — Multi-session behavior
- [[hermes-desktop-setup]] — Hermes Desktop configuration

## Detail Files

- `sessions/detail/20260514_083636_de88e5.md` — 57 messages, AionUI troubleshooting
- `sessions/detail/20260514_085509_2e3068.md` — 77 messages, rate limit discussion
- `sessions/detail/20260514_090128_1d6118.md` — 81 messages, process kill walkthrough
