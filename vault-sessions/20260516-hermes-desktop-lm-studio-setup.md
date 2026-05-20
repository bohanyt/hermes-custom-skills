---
title: Hermes Desktop + LM Studio Setup & Testing
date: 2026-05-16
sessions: [
  session_20260516_081500_eecdbc,
  session_20260516_083253_a5839f,
  session_20260516_083819_19338c
]
platform: tui
model: openrouter/owl-alpha
total_messages: ~586 (combined)
tags: [hermes-desktop, lm-studio, local-ai, setup, testing]
---

# Hermes Desktop + LM Studio Setup & Testing

**Date:** 2026-05-16 | **Platform:** TUI | **Combined messages:** ~586

## What Happened

Full day of Hermes Desktop and LM Studio setup and testing. Multiple sessions covering installation, configuration, and troubleshooting.

## Key Topics

### Hermes Desktop Installation
- Download from GitHub releases
- First-run: choose Local or Remote backend
- Local mode: auto-installs Hermes Agent with dependency resolution
- Supported providers: OpenRouter, Anthropic, OpenAI, Local LLM

### LM Studio Integration

**Setup:**
1. LM Studio → Local Server tab → Load Gemma 4 e2b → Start Server
2. Default: `http://127.0.0.1:1234`
3. Hermes Desktop → Settings → Models → Add → LM Studio

**Config override for Gemma 4 e2b (8K context):**
```yaml
model:
  context_length: 8192
  base_url: http://127.0.0.1:1234/v1
```

### Multi-Session Support

**Multiple TUI sessions:**
```bash
# Terminal 1
hermes --tui
# Terminal 2 (new session)
hermes --tui --new
# Resume specific session
hermes --tui --resume <session-id>
```

**Each session is separate** — different context, different conversation.

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| Context window 8K < 64K | Gemma 4 default context too small | Override `context_length: 8192` in config.yaml |
| No Windows console | Called from Desktop without TTY | Use CLI directly |
| 400 Bad Request | Wrong endpoint | Use `/v1/chat/completions` |
| Rate limit 429 | Too many concurrent requests | Add delay 15-30s, retry with backoff |
| API key not saved | `.env` empty | Check `~/.hermes/.env` |

### UI Stability

| UI | Status | Notes |
|----|--------|-------|
| Hermes Desktop | Buggy | Error 400, crash |
| AionUI | Buggy | User reported issues |
| Hermes TUI | More stable | Terminal-based |
| CLI directly | Most stable | `hermes --yolo "prompt"` |

**Recommendation:** Use CLI directly for stability. UI can be added later when stable.

## Related

- [[hermes-desktop-setup]] — Hermes Desktop configuration
- [[lm-studio-integration]] — LM Studio integration guide
- [[multi-session-management]] — Multi-session behavior
