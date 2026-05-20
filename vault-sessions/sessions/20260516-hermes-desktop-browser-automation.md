---
title: Hermes Desktop + LM Studio Setup & Browser Automation (May 16)
date: 2026-05-16
sessions: [
  session_20260516_074620_6f1cf8,
  session_20260516_080250_e7f174,
  session_20260516_080545_e7cc36,
  session_20260516_081500_eecdbc,
  session_20260516_083253_a5839f,
  session_20260516_083819_19338c,
  session_20260516_091547_868e7a,
  session_20260516_095404_fc824f,
  session_20260516_095700_878c38,
  session_20260516_101951_0729e5,
  session_20260516_104440_e27c9b
]
platform: tui
model: openrouter/owl-alpha
total_messages: ~1684 (combined)
tags: [hermes-desktop, lm-studio, browser-automation, setup, multi-session]
---

# Hermes Desktop + LM Studio Setup & Browser Automation (May 16)

**Date:** 2026-05-16 | **Platform:** TUI | **Combined messages:** ~1684

> 11 sessions across the day, covering Hermes Desktop setup, LM Studio integration, and browser automation. Merged into one summary.

## What Happened

Full day of Hermes Desktop and LM Studio setup, plus browser automation discussions. Multiple TUI sessions covering installation, configuration, and testing.

## Key Topics

### Hermes Desktop Setup
- Installation and first-run configuration
- Local vs Remote backend selection
- Provider configuration (OpenRouter, Anthropic, OpenAI, Local LLM)

### LM Studio Integration
- Gemma 4 e2b Q6 model loading
- Context length override (8K → 64K)
- GPU offload configuration (35 layers for 6GB VRAM)
- Endpoint: `http://localhost:1234/v1/chat/completions`

### Browser Automation
- Playwright setup for Copilot M365
- Cookie injection for persistent sessions
- Rate limit handling
- Multi-session API key strategy

### Multi-Session Management
- Session clone vs resume behavior
- Shared DB/vault/skills across sessions
- API key distribution (5 keys for fallback)

## Related

- [[20260516-hermes-desktop-setup]] — Main setup session
- [[20260516-hermes-desktop-lm-studio-setup]] — LM Studio integration
- [[hermes-desktop-setup]] — Full setup guide
