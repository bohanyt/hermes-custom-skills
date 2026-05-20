# M365 Copilot — Confirmed Working Reference (May 2026)

## Tested Environment
- Playwright 1.59.0, Chromium
- M365 Copilot Chat: `https://m365.cloud.microsoft/chat/?auth=2&origindomain=Office`
- Model: GPT-5.5 Think Deeper
- Auth: Cookie injection (19 cookies from browser session)

## Confirmed Selectors

| Element | Selector | Notes |
|---------|----------|-------|
| Model selector button | `#gptModeSwitcher` | Opens model dropdown |
| "Think Deeper" option | `text=Think Deeper` | In dropdown menu |
| Text input | `textarea, [contenteditable='true']` | Fallback chain |
| Send button | `button[type='submit']` | Or aria-label containing "Send" |
| **Response (last)** | `[data-testid='lastChatMessage']` | Confirmed working |
| File upload | `input[type='file']` | Standard file input |
| Stop generating | `button[aria-label*='Stop']` | Disappears when done |

## Response Scraping Pattern

```python
# Wait for response to complete (stop button disappears)
max_wait = 120
interval = 3
elapsed = 5
while elapsed < max_wait:
    stop_btn = page.locator("button[aria-label*='Stop']").first
    if await stop_btn.is_visible(timeout=1000):
        await page.wait_for_timeout(interval)
        elapsed += interval
    else:
        break

await page.wait_for_timeout(3000)

# Scrape the last response
response = page.locator("[data-testid='lastChatMessage']").first
if await response.is_visible(timeout=5000):
    text = await response.inner_text()
```

## Model Selection Pattern

```python
model_btn = page.locator("#gptModeSwitcher").first
await model_btn.click()
await page.wait_for_timeout(1500)
option = page.locator("text=Think Deeper").first
if await option.is_visible(timeout=3000):
    await option.click()
```

## Known Issues

1. `[data-content-editable-root]` is WRONG for M365 Copilot — that's the input area. Use `[data-testid='lastChatMessage']`.
2. `Browser.pages` doesn't exist — use `Context.pages`.
3. `viewport` in `launch()` — must be in `new_context()`.
4. Single `OhpToken` cookie is NOT enough — need all 19 cookies.
5. Hermes browser tools can't render M365 Copilot — use Playwright via `terminal`.
6. "Service communication is currently unavailable" — transient error, retry after delay.
