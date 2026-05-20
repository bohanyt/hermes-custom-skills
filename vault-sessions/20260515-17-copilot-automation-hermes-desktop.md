---
title: Copilot M365 Automation & Hermes Desktop Setup
sessions: [20260517_080634_ca6091, 20260515_182711_f2f3dc, 20260516_104440_e27c9b]
date: 2026-05-15 to 2026-05-17
platform: tui
model: openrouter/owl-alpha
total_messages: ~900 (combined)
tags: [copilot, m365, playwright, hermes-desktop, lm-studio, cloakbrowser, automation]
---

# Copilot M365 Automation & Hermes Desktop Setup

**Date:** 2026-05-15 to 2026-05-17 | **Platform:** TUI | **Combined messages:** ~900

## What Happened

Multiple sessions covering: Copilot M365 automation strategy, CloakBrowser evaluation, Playwright setup, Hermes Desktop installation, LM Studio integration, and multi-session troubleshooting.

## Copilot M365 Automation Strategy

### User's Goal
Automate Copilot M365 usage at the office — currently manual (copy-paste prompt, scrape results with Tampermonkey). Wants to automate: chunked transkrip → prompt → save results.

### Current Manual Flow
```
Livestream → PDF → OCR → TXT (500KB-3MB)
    ↓
Chunk per 50KB
    ↓
Copilot M365 (web) → manual prompt → Tampermonkey scrape → .txt file
```

### Proposed Automated Flow
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

### Playwright Setup

**Install:**
```bash
pip install playwright
playwright install chromium
```

**Headless mode (background):**
```python
browser = p.chromium.launch(headless=True)
```

**Background process:**
```bash
nohup python copilot_bot.py > output.log 2>&1 &
```

**Persistent context (login once):**
```python
context = browser.new_context(storage_state="auth.json")
```

### Copilot M365 Access Options

| Option | Can Automate? | Notes |
|--------|---------------|-------|
| Chrome/Edge browser | ✅ | Best for automation |
| Windows Copilot app | ❌ | Can't automate |
| Copilot in Teams/Outlook | ❌ | Embedded, limited |

**For automation: Use Chrome/Edge browser → copilot.microsoft.com**

### Model Selection

Always use "GPT 5.5 Think Deeper" for data processing tasks. Switch via `#gptModeSwitcher` dropdown.

## Hermes Desktop Setup

### Installation
1. Download from GitHub releases
2. First-run: choose Local or Remote backend
3. Local mode: auto-installs Hermes Agent with dependency resolution
4. Supported providers: OpenRouter, Anthropic, OpenAI, Local LLM

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

**Practical setup:**
| Process | Terminal | Function |
|---------|----------|----------|
| LM Studio Server | Background | Model server |
| Hermes TUI | Terminal 1 | Chat + orchestration |
| Copilot script | Terminal 2 | Browser automation |

**Only 1 Hermes TUI active at a time.**

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

### Rate Limit Handling

```python
# Delay between requests
import time
time.sleep(15)  # 15-30 seconds

# Retry with exponential backoff
for attempt in range(3):
    try:
        response = call_api()
        break
    except RateLimitError:
        time.sleep(10 * (attempt + 1))  # 10s, 20s, 30s
```

## Related

- [[copilot-m365-pipeline]] — Full automation architecture
- [[playwright-m365-automation]] — Playwright technical details
- [[hermes-desktop-setup]] — Hermes Desktop configuration
- [[lm-studio-integration]] — LM Studio integration guide
- [[reject-cloakbrowser]] — Why CloakBrowser not needed
- [[multi-session-management]] — Multi-session behavior

## Detail Files

- `sessions/detail/20260517_080634_ca6091.md` — 255 messages, CloakBrowser evaluation
- `sessions/detail/20260515_182711_f2f3dc.md` — 249 messages, Copilot automation planning
- `sessions/detail/20260516_104440_e27c9b.md` — 227 messages, Hermes Desktop setup
