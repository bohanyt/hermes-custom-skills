---
title: Copilot M365 + CloakBrowser Evaluation
sessions: [20260515_182711_f2f3dc, 20260515_192028_c55b61, 20260515_195540_f2100e, 20260515_211817_a1c10d, 20260517_05-copilot-cloakbrowser-tui]
date: 2026-05-15 to 2026-05-17
platform: tui/cli
model: openrouter/owl-alpha
total_messages: ~350 (combined)
tags: [copilot, m365, cloakbrowser, browser-automation, enterprise]
---

# Copilot M365 + CloakBrowser Evaluation

**Date:** 2026-05-15 to 2026-05-17 | **Platform:** TUI/CLI | **Combined messages:** ~350

## What Happened

Evaluation of CloakBrowser for accessing Copilot M365 at the office. User wanted to automate Copilot usage without leaking data. Discussion of Playwright + cookie injection as alternative.

## CloakBrowser Overview

**What it is:** Stealth Chromium that passes bot detection tests. Drop-in Playwright/Puppeteer replacement.

**Key features:**
- 49 source-level C++ patches (canvas, WebGL, audio, fonts, GPU, etc.)
- `humanize=True` for human-like mouse/keyboard behavior
- 0.9 reCAPTCHA v3 score (human-level)
- Passes Cloudflare Turnstile, FingerprintJS, BrowserScan
- Auto-updating binary

## Decision: Reject CloakBrowser for Enterprise

**Rationale:**
- No bot detection bypass needed for internal tools
- Custom binary = compliance risk for enterprise
- Playwright + cookie injection is cleaner and more maintainable

## Approved Alternative: Playwright + Cookie Injection

**Architecture:**
```
Hermes Desktop (orchestrator)
    ↓
Playwright browser automation
    ↓
Cookie injection (~/.copilot-m365-session/cookies.json)
    ↓
M365 Copilot (GPT-5.5 Think Deeper)
    ↓
Response extraction via DOM selectors
```

**Key details:**
- URL: `https://m365.cloud.microsoft/chat/?auth=***`
- Model: GPT 5.5 Think Deeper
- Cookie path: `~/.copilot-m365-session/cookies.json` (34 cookies)
- Selectors: `#gptModeSwitcher` → GPT 5.5, `[data-testid='lastChatMessage']` → response
- Script: `copilot_hermes/v0.3/copilot_m365_v2.py`
- Flow: new chat per chunk, retry 3x, delay 20s

## Related

- [[copilot-m365-pipeline]] — Full architecture
- [[playwright-m365-automation]] — Technical details
- [[reject-cloakbrowser]] — Decision record
- [[browser-automation-enterprise]] — Skill documentation

## Detail Files

- `sessions/detail/20260515_182711_f2f3dc.md` — 249 messages, CloakBrowser evaluation
- `sessions/detail/20260515_192028_c55b61.md` — 28 messages, follow-up
- `sessions/detail/20260515_195540_f2100e.md` — 39 messages, implementation
- `sessions/detail/20260515_211817_a1c10d.md` — 48 messages, testing
