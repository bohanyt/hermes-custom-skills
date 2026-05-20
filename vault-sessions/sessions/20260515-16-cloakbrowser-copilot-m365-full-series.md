---
title: CloakBrowser Evaluation & Copilot M365 Automation (Full Series)
date: 2026-05-15 to 2026-05-16
sessions: [
  session_20260515_182711_f2f3dc,
  session_20260515_192028_c55b61,
  session_20260515_195540_f2100e,
  session_20260516_055701_f2c3b4,
  session_20260516_070153_03f116,
  session_20260516_074620_6f1cf8,
  session_20260516_080250_e7f174,
  session_20260516_080545_e7cc36,
  session_20260516_081500_eecdbc,
  session_20260516_083253_a5839f,
  session_20260516_083819_19338c,
  session_20260516_091547_868e7a,
  session_20260516_095404_fc824f,
  session_20260516_095700_878c38,
  session_20260516_101951_0729e5
]
platform: tui/cli
model: openrouter/owl-alpha
total_messages: ~2500 (combined)
tags: [cloakbrowser, copilot, m365, browser-automation, enterprise, playwright]
---

# CloakBrowser Evaluation & Copilot M365 Automation

**Date:** 2026-05-15 to 2026-05-16 | **Platform:** TUI/CLI | **Combined messages:** ~2500

> Multiple sessions covering the same topic across multi-session workflow. Merged into one summary.

## What Happened

Extensive discussion about automating Copilot M365 at the office. User wants to automate the manual workflow of copy-pasting prompts to Copilot M365 and scraping results with Tampermonkey.

## Key Topics

### CloakBrowser Evaluation

**What it is:** Stealth Chromium with 49 C++ source-level patches for bot detection bypass.

**Test results:**
- reCAPTCHA v3: 0.9 (human-level) vs stock Playwright 0.1 (bot)
- Cloudflare Turnstile: Pass vs Fail
- FingerprintJS, BrowserScan: Pass

**Decision: NOT needed for Copilot M365**
- M365 Copilot is enterprise internal, no Cloudflare/reCAPTCHA
- Microsoft doesn't have aggressive bot detection on enterprise tenant
- Playwright + cookie injection is sufficient and cleaner

### Copilot M365 Access Options

| Option | Can Automate? | Notes |
|--------|---------------|-------|
| Chrome/Edge browser | ✅ | Best for automation |
| Windows Copilot app | ❌ | Can't automate |
| Copilot in Teams/Outlook | ❌ | Embedded, limited |

**For automation: Use Chrome/Edge browser → copilot.microsoft.com**

### Playwright Setup

```bash
pip install playwright
playwright install chromium
```

**Headless mode:**
```python
browser = p.chromium.launch(headless=True)
```

**Persistent context (login once):**
```python
context = browser.new_context(storage_state="auth.json")
```

### Rate Limit Handling

```python
import time
time.sleep(15)  # 15-30 seconds between requests

# Retry with exponential backoff
for attempt in range(3):
    try:
        response = call_api()
        break
    except RateLimitError:
        time.sleep(10 * (attempt + 1))
```

### Multi-Session Strategy

**Problem:** Multiple sessions using same API key → rate limit / hang

**Solutions:**
- Close idle sessions when working in one
- Use different API key per session
- Set fallback provider (Gemini as backup for OpenRouter)

## Related

- [[copilot-m365-pipeline]] — Full automation architecture
- [[playwright-m365-automation]] — Playwright technical details
- [[reject-cloakbrowser]] — Why CloakBrowser not needed
- [[multi-session-management]] — Multi-session behavior
