---
name: browser-automation-enterprise
description: "Automate enterprise SaaS tools (M365 Copilot, Teams, SharePoint) via browser automation from Hermes. Covers Playwright patterns, Hermes browser tools, persistent sessions, model selection, and the orchestrator pattern where a small local model delegates heavy analysis to a cloud LLM via browser."
version: "1.0.0"
author: OWL
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [browser, automation, enterprise, m365, copilot, playwright, orchestrator]
---

# Browser Automation for Enterprise SaaS

Automate enterprise SaaS tools (M365 Copilot, Teams, SharePoint, etc.) using browser automation from Hermes. This skill covers the architecture, tool selection, and patterns for building pipelines that connect local AI models with cloud-based enterprise LLMs via browser.

## When to Use

- Automating M365 Copilot (or similar enterprise SaaS) without API access
- Building pipelines where a small local LLM orchestrates a powerful cloud LLM
- Replacing manual copy-paste workflows with browser automation
- Scraping responses from web-based AI tools into local files

---

## Tool Selection

### For Enterprise SaaS (M365, etc.)

| Tool | Use for enterprise? | Why |
|------|---------------------|-----|
| **Playwright + official browser** | ✅ YES | Uses corporate browser (Edge/Chrome), compliant, no custom binaries |
| **Hermes browser tools** | ✅ YES | Built into Hermes Desktop, no extra install, chat-driven |
| **CloakBrowser** | ❌ NO | Custom binary = red flag for IT security. Enterprise SaaS doesn't have bot detection like public sites. |
| **Selenium/undetected-chromedriver** | ❌ NO | Overkill, harder to maintain, same compliance issues as CloakBrowser |

### Key Insight

Enterprise SaaS tools (M365 Copilot, Teams, SharePoint) use **authorization-based access control**, not bot detection. They check:
- Is the session valid? (login/cookies)
- Is the device compliant? (conditional access)
- Is the request rate reasonable? (rate limiting)

They do NOT check `navigator.webdriver`, canvas fingerprints, or TLS signatures. **CloakBrowser provides zero value for enterprise SaaS and creates compliance risk.**

---

## Architecture: Small LLM Orchestrator + Cloud LLM

When your local model (e.g., Gemma 4 e2b Q6, 4.5GB VRAM) has a small context window, use this pattern:

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│   Local LLM (small context)                         │
│   = Project Manager                                 │
│   - Read file paths                                 │
│   - Loop through chunks                             │
│   - Send prompts to Copilot via browser             │
│   - Save responses to files                         │
│   - Feed results to next stage                      │
│                                                     │
│                  ↕ via browser                       │
│                                                     │
│   Cloud LLM (large context, e.g., GPT-5.5)          │
│   = Senior Analyst                                  │
│   - Read file contents (50KB+)                      │
│   - Analyze, summarize, synthesize                  │
│   - Interpret images                                │
│   - Complex reasoning                               │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### What the local LLM handles (small context OK):
- File path management
- Loop orchestration
- Prompt construction
- Response file saving
- Timestamp-based folder creation

### What the cloud LLM handles (needs large context):
- Reading 50KB+ file contents
- Analyzing long documents
- Image interpretation
- Complex synthesis

**The local LLM never reads file contents. It only handles paths and instructions.**

---

## Playwright Pattern for M365 Copilot

### Setup

```python
from playwright.sync_api import sync_playwright
import time, random

with sync_playwright() as p:
    # Use Edge (corporate default) with persistent context
    ctx = p.chromium.launch_persistent_context(
        user_data_dir="./copilot-session",
        headless=False,      # First run: visible for login
        channel="msedge"     # Use Edge, not Chromium
    )
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
```

### Login Once, Reuse Forever

```python
# First run: headless=False, login manually
# Subsequent runs: headless=True, session restored automatically
ctx = p.chromium.launch_persistent_context(
    user_data_dir="./copilot-session",
    headless=True,  # Background after initial login
    channel="msedge"
)
```

### Upload File + Send Prompt

```python
# Upload file
file_input = page.query_selector("input[type='file']")
file_input.set_input_files("path/to/chunk_001.txt")

# Type prompt with human-like delay
textarea = page.wait_for_selector("textarea", timeout=10000)
textarea.click()
textarea.type("Ringkas poin penting dari dokumen ini", delay=50)

# Submit
page.keyboard.press("Enter")

# Wait for response
time.sleep(15)  # Adjust based on response length
```

### Scrape Response (confirmed working selector)

M365 Copilot renders responses inside `[data-testid="lastChatMessage"]`. The actual reply text is in the LAST `[data-testid="markdown-reply"]` element (not the "Progress" type ones).

```python
# ✅ CORRECT — M365 Copilot response selector (confirmed working)
last_msg = page.locator("[data-testid='lastChatMessage']").first
if await last_msg.is_visible(timeout=5000):
    replies = last_msg.locator("[data-testid='markdown-reply']")
    count = await replies.count()
    if count > 0:
        last_reply = replies.nth(count - 1)  # Last one = final response
        text = await last_reply.inner_text()
```

**Why not just `inner_text()` on `lastChatMessage`?** — That includes all progress messages, thinking steps, and citations. Selecting the last `markdown-reply` gives only the final clean response.

**Wait for response complete:** Check for "Stop generating" button disappearing:
```python
while elapsed < max_wait:
    stop_btn = page.locator("button[aria-label*='Stop']").first
    if await stop_btn.is_visible(timeout=1000):
        await page.wait_for_timeout(5)
    else:
        break
```

**Scroll to bottom** before scraping — response may be below viewport:
```python
await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
await page.wait_for_timeout(2000)
```

### Model Selection (confirmed working)

```python
# Wait for response to complete
page.wait_for_selector("[data-content-editable-root]", timeout=60000)

# Get response text
response = page.query_selector("[data-content-editable-root]")
hasil = response.inner_text()

# Save to file
from datetime import datetime
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
with open(f"results/hasil_{timestamp}.txt", "w", encoding="utf-8") as f:
    f.write(hasil)
```

### Human-Like Delays

```python
def human_delay(min_s=1, max_s=3):
    time.sleep(random.uniform(min_s, max_s))

# Between actions
human_delay()
```

---

## Hermes Desktop Pattern

### ⚠️ CRITICAL: Hermes Browser Tools Cannot Render JS-Heavy Pages

**Hermes browser tools (`browser_navigate`, `browser_snapshot`, `browser_vision`) CANNOT properly render JavaScript-heavy pages like M365 Copilot.**

Symptoms:
- `browser_snapshot` returns empty ("no interactive elements detected")
- `browser_vision` returns black/empty screenshots
- `browser_get_images` returns SyntaxError
- Page URL is correct but content is invisible to the browser tool

**Root cause:** M365 Copilot renders via React/Next.js (heavy client-side JS). Hermes browser tools use a lightweight browser engine that doesn't fully execute modern JS frameworks.

**Solution: Use Playwright Python script called from Hermes via `terminal` tool.**

```
Hermes (Gemma) → terminal("python copilot_bot.py") → Playwright → Copilot M365
```

NOT:

```
Hermes (Gemma) → browser tools → Copilot M365  ← DOES NOT WORK
```

### When Hermes Browser Tools DO Work
- Static HTML pages
- Simple server-rendered pages
- Pages with minimal JavaScript
- Basic forms and navigation

### When You Need Playwright Instead
- React/Next.js/Angular SPAs
- M365 Copilot, Teams, SharePoint
- Any page that loads content dynamically via JS
- Pages requiring full browser rendering

### Available File Tools (these work fine)
- `read_file` — read local file
- `write_file` — write local file
- `terminal` — run shell commands (mkdir, python scripts, etc.)

### Revised Flow for Copilot M365

```
User: "Proses chunk transkrip rapat hari ini"

Hermes (Gemma 4 e2b):
1. List files in chunks/
2. terminal("python copilot_bot.py --chunk chunk_001.txt")
3. Playwright script handles:
   a. Open Edge → Copilot URL
   b. Upload file
   c. Type prompt
   d. Wait for response
   e. Scrape response
   f. Save to results/
4. Repeat for each chunk
5. Feed results to LLM Wiki
```

**The browser automation happens in Playwright, not in Hermes browser tools. Hermes orchestrates by calling the script.**

---

## End-to-End Pipeline: Docx → Knowledge Base

The full pipeline the user is building:

```
Docx (text + images)
    ↓
Local LLM: extract text + interpret images → markdown
    ↓
Split per 50KB chunks
    ↓
For each chunk:
  Upload to Copilot M365 (GPT-5.5 Think Deeper) via browser
  Scrape response
  Save as results/YYYYMMDD_HHMMSS.txt
    ↓
Optional: compress summaries via Copilot again (< 10KB)
    ↓
Feed to LLM Wiki (local knowledge base, markdown)
    ↓
Knowledge base per project/topic
```

### Key Insight: Local LLM Never Reads File Contents

The local LLM (Gemma 4 e2b Q6, 8K context) only handles:
- File paths
- Loop orchestration
- Prompt construction
- Browser automation commands
- Save instructions

File CONTENTS (50KB+) are sent to Copilot (GPT-5.5) via browser. The local LLM never loads them into its own context.

### Hermes Desktop as the UI

Everything runs inside Hermes Desktop — no separate scripts, no .bat files, no terminal:

1. User types: "Proses chunk transkrip rapat hari ini"
2. Hermes (Gemma) orchestrates:
   - List files in chunks/
   - For each chunk: browser_navigate → upload → prompt → scrape → save
   - Feed results to LLM Wiki
3. All from one chat window

### Folder Structure

```
copilot-pipeline/
├── input/              # Raw files (docx, txt, pdf)
├── markdown/           # After docx → markdown conversion
├── chunks/             # Split per 50KB
├── results/            # Copilot responses (timestamped)
│   ├── 20260515_143022.txt
│   └── 20260515_143145.txt
├── wiki/               # LLM Wiki — knowledge base
│   ├── proyek-a/
│   └── proyek-b/
├── copilot-session/    # Browser session (auto-generated)
└── pipeline.log        # Process log
```

---

## M365 Copilot Specifics

### Model Selection (GPT-5.5 Think Deeper)

M365 Copilot model selection is a **3-step process** (confirmed working):

1. Click `#gptModeSwitcher` button (main dropdown, shows current model like "Auto")
2. Click `data-test-id="gptSubMenuModelTrigger-OpenAI"` (expands GPT OpenAI submenu)
3. Click the model option (e.g., `text=GPT 5.5 Think Deeper`)

```python
# Step 1: Click main dropdown
model_btn = page.locator("#gptModeSwitcher").first
await model_btn.click()
await page.wait_for_timeout(1500)

# Step 2: Click "GPT Open AI" submenu to expand
openai_submenu = page.locator('[data-test-id="gptSubMenuModelTrigger-OpenAI"]').first
if await openai_submenu.is_visible(timeout=3000):
    await openai_submenu.click()
    await page.wait_for_timeout(1500)

# Step 3: Click the model option
option = page.locator("text=GPT 5.5 Think Deeper").first
if await option.is_visible(timeout=3000):
    await option.click()
    await page.wait_for_timeout(1000)
```

**Important:** The model selector button shows the CURRENT model (e.g., "Auto"), not a generic label. The `aria-label` is "Model Selector".

**Available models in GPT OpenAI submenu:**
- GPT 5.5 Think Deeper (reasoning model)
- GPT 5.5 (standard)
- Other models vary by tenant configuration

### File Upload

M365 Copilot supports drag-drop file upload:
```python
file_input = page.query_selector("input[type='file']")
file_input.set_input_files("path/to/file.txt")
```

### Session Management

- First login: manual (headless=False)
- Session persists in `user_data_dir`
- Subsequent runs: automatic (headless=True)
- If session expires: re-login manually once

---

## LM Studio Setup for Hermes

When using LM Studio as the local LLM backend for Hermes:

### Config

```yaml
model:
  default: "google/gemma-4-e2b"
  provider: "lmstudio"          # Use lmstudio preset, NOT "custom"
  base_url: "http://127.0.0.1:1234/v1"  # MUST include /v1
  context_length: 8192          # Override if model reports < 64K
  api_key: "lmstudio"           # LM Studio doesn't need a real key
```

### Critical: Base URL must include `/v1`

LM Studio exposes OpenAI-compatible API at `/v1/chat/completions`, NOT `/chat/completions`.

```
❌ http://127.0.0.1:1234        → "Unexpected endpoint" error
✅ http://127.0.0.1:1234/v1     → Correct
```

If you see `Unexpected endpoint or method. (POST /chat/completions)` in LM Studio logs, the base URL is missing `/v1`.

### Context Length Override

Hermes enforces a minimum 64K context window. For models with smaller contexts (e.g., Gemma 4 e2b at 8K), you MUST set `context_length` in config.yaml. Without this, Hermes refuses to start.

### LM Studio Server Setup

1. Load model in LM Studio
2. Go to **Local Server** tab
3. Set GPU offload (e.g., 35 layers for 6GB VRAM)
4. Start server (default port: 1234)
5. Verify: `curl http://127.0.0.1:1234/v1/models` should return JSON

### Provider Selection

| Provider value | When to use |
|----------------|-------------|
| `lmstudio` | LM Studio local server (recommended) |
| `custom` | Other OpenAI-compatible endpoints (Ollama, vLLM) |

---

### Login Wait Pattern

When M365 Copilot redirects to login, the script should wait for the user to complete login before proceeding:

```python
async def wait_for_login(self, timeout=300):
    if "login" in self.page.url.lower():
        print("Login required — please login in the browser window...")
        await self.page.wait_for_url(
            lambda url: "login" not in url.lower(),
            timeout=timeout * 1000
        )
        print("Login successful!")
        # Save cookies after login for future use
        cookies = await self.context.cookies()
        save_cookies(cookies)
```

After login, cookies are saved to `~/.copilot-m365-session/cookies.json` for reuse.

### Screenshot debugging

### ❌ Don't use CloakBrowser for enterprise SaaS
Enterprise tools don't have bot detection. CloakBrowser's custom binary is a compliance risk with zero benefit.

### ❌ Don't read file contents into local LLM context
The local LLM (small context) should only handle paths and instructions. File contents go to the cloud LLM.

### ❌ Don't skip delays between actions
Even without bot detection, rapid-fire requests look unnatural and may trigger rate limits.

### ❌ Don't use headless mode for first run
Login requires visible browser. Use `headless=False` first, then `headless=True` after session is saved.

### ❌ Don't expect multi-session support
Hermes does NOT support multiple concurrent sessions to the same provider. One session per provider. Use one TUI for orchestration, and call Playwright scripts via `terminal` tool for browser automation.

### ❌ Don't forget `/v1` in LM Studio base URL
LM Studio requires `/v1` in the path. Without it, you get "Unexpected endpoint" errors.

Also: Hermes enforces minimum 64K context. For small models (Gemma 4 e2b at 8K), you MUST set `context_length: 8192` in config.yaml. Without this, Hermes refuses to start with error "context window below minimum 64,000".

### ✅ Do use persistent context
`launch_persistent_context` saves cookies/session. Login once, reuse forever.

```python
context = await pw.chromium.launch_persistent_context(
    user_data_dir="./copilot-session",
    headless=False,  # First run: visible for login
    viewport={"width": 1280, "height": 900},
    locale="id-ID",
    timezone_id="Asia/Jakarta",
)
page = context.pages[0] if context.pages else context.new_page()
```

After login, save cookies for reuse across devices:
```python
cookies = await context.cookies()
save_cookies(cookies)  # Save to ~/.copilot-m365-session/cookies.json
```

### ✅ Do use the corporate browser (Edge/Chrome)
Don't install custom browsers. Use what's already on the corporate device.

### ✅ Do scrape directly with Playwright
No need for TamperMonkey. Playwright's `inner_text()` and `snapshot()` can extract any page content.

### ✅ Do set context_length for small models
Override `context_length` in config.yaml for models with < 64K context (e.g., Gemma 4 e2b at 8K).

### ✅ Do use the correct M365 Copilot URL
M365 Copilot Chat URL: `https://m365.cloud.microsoft/chat/?auth=2&origindomain=Office`
NOT `https://copilot.microsoft.com` (public Copilot, different product).

### ✅ Do handle login via Microsoft OAuth
M365 Copilot redirects to `login.microsoftonline.com`. User must login manually first time. Session is then saved to `user_data_dir` for reuse. For cross-device testing, extract cookies from incognito and inject via `context.add_cookies()`.

### ❌ Don't use Hermes browser tools for JS-heavy pages
Hermes browser tools (`browser_navigate`, `browser_snapshot`, `browser_vision`) CANNOT render JavaScript-heavy pages like M365 Copilot (React/Next.js). Use Playwright Python script called via `terminal` tool instead.

**Confirmed symptoms (tested):**
- `browser_snapshot` → "no interactive elements detected" (page URL is correct but content invisible)
- `browser_vision` → black/empty screenshot
- `browser_get_images` → SyntaxError: Unexpected end of input
- `browser_console` → no errors found, but page content is invisible

**Root cause:** M365 Copilot is a React/Next.js SPA with heavy client-side rendering. Hermes browser tools use a lightweight engine that doesn't fully execute modern JS frameworks.

### ❌ Don't use Hermes Desktop if unstable
Hermes Desktop is buggy (error 400, crashes when switching menus). Use **Hermes TUI** (`hermes --tui`) instead — same agent, same tools, more stable.

### ❌ Don't put output files in raw_footages/
When processing sessions or running pipelines, never put output files in the source folder. Use a separate output directory. For vault: use `sessions/detail/` for condensed files. For Live2Video: use `testing/v{version}_tes{N}/`.

### ❌ Don't claim "all done" when work remains
If processing 89 session files and you've done 44, don't say "all sessions processed". State the actual count: "44 of 89 processed". Use `_meta/_processing_state.json` to track progress accurately.

### ✅ Do process in small batches with tracking
For large batch jobs (89+ files), process 3-5 items per run. Track state in `_meta/_processing_state.json`. Let cron jobs handle the continuation. This prevents context overflow and allows incremental progress.

### ✅ Do use knowledge-map + hermes-patterns as navigation hubs
Maintain `_meta/knowledge-map.md` as the central navigation hub mapping all topics to files. Maintain `_meta/hermes-patterns.md` for reusable patterns and pitfalls. Update both when new knowledge is extracted.

### ✅ Do use 4-level drill-down hierarchy
```
Level 1: concepts/          ← High-level knowledge (always check first)
Level 1: decisions/         ← Decisions made (linked to concepts)
Level 1: people/            ← People mentioned (linked to sessions)
Level 2: sessions/          ← Session summaries (one per unique topic/project)
Level 3: sessions/detail/   ← Condensed conversations (drill-down)
Level 4: AppData/Local/hermes/sessions/*.json  ← Raw JSON (last resort)
```

### ❌ Don't put `viewport` in `launch()`
Playwright's `chromium.launch()` does NOT accept `viewport` parameter. Use `new_context()` instead:

```python
# ❌ WRONG — TypeError
browser = await pw.chromium.launch(headless=False, viewport={"width": 1280, "height": 900})

# ✅ CORRECT
browser = await pw.chromium.launch(headless=False)
context = await browser.new_context(viewport={"width": 1280, "height": 900})
```

### ❌ Don't use `Browser.pages` — use `Context.pages` (or `launch_persistent_context`)

Playwright's `chromium.launch()` returns a `Browser` object which does NOT have a `.pages` attribute. Use `Context.pages` instead:

```python
# ❌ WRONG — AttributeError: 'Browser' object has no attribute 'pages'
browser = await pw.chromium.launch(headless=False)
page = browser.pages[0] if browser.pages else browser.new_page()

# ✅ CORRECT — Use context
browser = await pw.chromium.launch(headless=False)
context = await browser.new_context(viewport={"width": 1280, "height": 900})
page = context.pages[0] if context.pages else context.new_page()
```

**Exception:** `launch_persistent_context()` returns a `BrowserContext` (not `Browser`), which DOES have `.pages`:

```python
# ✅ CORRECT — persistent context returns context directly
context = await pw.chromium.launch_persistent_context(
    user_data_dir="./session",
    headless=False,
    viewport={"width": 1280, "height": 900}
)
page = context.pages[0] if context.pages else context.new_page()
```

### ❌ Don't use only `OhpToken` cookie
M365 Copilot requires MULTIPLE cookies for auth. `OhpToken` alone is NOT enough — still redirects to login.

**Minimum cookies needed (19 total):**
- `OhpAuthC1` — auth token utama (wajib)
- `OhpAuthC2` — auth token kedua (wajib)
- `OhpToken` — OAuth token (wajib)
- `OH.SID` — session ID (wajib)
- `userid` — user ID kantor (wajib)
- `OhpAuth` — auth chunks
- `MSCC`, `NavCS`, `OH.DCAffinity`, `OH.FLID`, `OH.RNG`, `SSREnabled`, `UserIndex` — session cookies
- `at_check`, `CS`, `msal.cache.encryption` — MSAL/auth cookies
- `kndctr_*_AdobeOrg_identity`, `mbox`, `MC1` — analytics (optional but include anyway)

**How to extract:** F12 → Application → Cookies → `https://m365.cloud.microsoft` → select all → copy → paste into script.

**Confirmed working:** 19 cookies injected via `context.add_cookies()` → successfully bypasses login redirect.

---

## Docx Processing Pipeline

When input files contain docx (text + images):

1. **Extract text** from docx (python-docx or pandoc)
2. **Extract images** from docx (it's a ZIP file with media/)
3. **Interpret images** using vision model (local or Copilot)
4. **Combine** text + image descriptions into markdown
5. **Chunk** markdown per 50KB
6. **Feed** chunks to Copilot for analysis
7. **Save** results to knowledge base

## Reference: Working Script

See `references/copilot-bot-script.md` for the tested Playwright bot script, confirmed working selectors, and integration patterns with Hermes TUI.

---

## Rate Limiting

M365 Copilot has per-user rate limits. Guidelines:
- Add 30-60 second delays between requests
- Don't run concurrent sessions on the same account
- If you hit 429: wait 60s and retry
- Process chunks sequentially, not in parallel

---

## Security Notes

- Data stays within M365 tenant (Copilot enterprise doesn't send data externally)
- Browser session is stored locally on the corporate device
- No custom binaries or unauthorized software
- All automation runs locally — no data sent to third parties
- Check corporate policy before automating internal tools
