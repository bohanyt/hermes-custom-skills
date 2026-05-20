# M365 Copilot Cookie Injection Pattern

## Overview

M365 Copilot requires cookie-based authentication. This document covers the tested pattern for extracting cookies from a logged-in browser session and injecting them into Playwright.

## Why Cookies?

Playwright launches a fresh Chromium instance with no existing session. Unlike `launch_persistent_context` (which saves session after manual login), cookie injection lets you:
- Test on a different machine without re-login
- Share session between browser and Playwright
- Automate the login step for testing

## Cookie Extraction Steps

1. **Login to M365 Copilot** in browser (Chrome/Edge/incognito)
2. **F12** → **Application** tab → **Cookies** → `https://m365.cloud.microsoft`
3. **Select all cookies** (Ctrl+A in the table)
4. **Copy** (Ctrl+C) — format is tab-separated: `Name\tValue\tDomain\tPath\tExpires\t...`
5. **Parse** into list of `{"name": ..., "value": ..., "domain": ..., "path": "/"}` objects

## Minimum Required Cookies

| Cookie | Purpose | Required? |
|--------|---------|-----------|
| `OhpAuthC1` | Auth token utama | ✅ YES |
| `OhpAuthC2` | Auth token kedua | ✅ YES |
| `OhpToken` | OAuth token | ✅ YES |
| `OH.SID` | Session ID | ✅ YES |
| `userid` | User ID kantor | ✅ YES |
| `OhpAuth` | Auth chunks | ✅ YES |
| All others | Session/analytics | Include all for best results |

**Tested:** 19 cookies injected → successfully bypasses `login.microsoftonline.com` redirect.

## Injection Code

```python
import asyncio
from playwright.async_api import async_playwright

COOKIES = [
    {"name": "OhpAuthC1", "value": "...", "domain": "m365.cloud.microsoft", "path": "/"},
    {"name": "OhpAuthC2", "value": "...", "domain": "m365.cloud.microsoft", "path": "/"},
    {"name": "OhpToken", "value": "...", "domain": "m365.cloud.microsoft", "path": "/"},
    {"name": "OH.SID", "value": "...", "domain": "m365.cloud.microsoft", "path": "/"},
    {"name": "userid", "value": "...", "domain": "m365.cloud.microsoft", "path": "/"},
    # ... all 19 cookies
]

async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False)
        context = await browser.new_context(viewport={"width": 1280, "height": 900})
        await context.add_cookies(COOKIES)
        
        page = await context.new_page()
        await page.goto("https://m365.cloud.microsoft/chat/?auth=2&origindomain=Office", 
                        wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(8000)
        
        # Check if login bypass worked
        if "login" in page.url.lower():
            print("❌ Still redirected — cookies expired or incomplete")
        elif "m365" in page.url:
            print("✅ On Copilot M365!")
```

## Response Scraping

After sending a prompt, the response can be scraped. However, the `main` selector returns the **full chat history**, not just the latest response.

**Tested selectors:**
- `[data-testid='response']` — not found
- `[class*='response']` — returns full chat history
- `main` — returns full chat history (1054 chars in test)

**Next step needed:** Inspect the DOM to find a selector that targets only the **last response** (not full history). Likely need to find the last `[class*='message']` or similar.

## Playwright API Gotcha

```python
# ❌ WRONG — TypeError: BrowserType.launch() got an unexpected keyword argument 'viewport'
browser = await pw.chromium.launch(headless=False, viewport={"width": 1280, "height": 900})

# ✅ CORRECT — viewport goes in new_context()
browser = await pw.chromium.launch(headless=False)
context = await browser.new_context(viewport={"width": 1280, "height": 900})
```

## Confirmed Working (2026-05-16)

- ✅ 19 cookies injected → bypasses login redirect
- ✅ `m365.cloud.microsoft/chat/?auth=2` URL loads correctly
- ✅ Textarea found via `page.locator("textarea").first`
- ✅ Prompt typed and sent via `keyboard.press("Enter")`
- ✅ Response received (30s wait) and scraped from `main` selector
- ⚠️ Response is full chat history, not just latest message — needs selector refinement
