# M365 Copilot Playwright Bot — Confirmed Working Script

This is the tested and confirmed working script for automating M365 Copilot via Playwright.

## Key Selectors (confirmed 2026-05-16)

| Element | Selector |
|---------|----------|
| Model selector button | `#gptModeSwitcher` |
| OpenAI submenu | `[data-test-id="gptSubMenuModelTrigger-OpenAI"]` |
| GPT 5.5 Think Deeper option | `text=GPT 5.5 Think Deeper` |
| Textarea input | `textarea, [contenteditable='true']` |
| Send button | `button[type='submit']` |
| Last response container | `[data-testid='lastChatMessage']` |
| Final reply text | `[data-testid='lastChatMessage'] [data-testid='markdown-reply']` (last one) |
| Stop generating button | `button[aria-label*='Stop']` |
| File upload | `input[type='file']` |

## Model Selection Flow

1. Click `#gptModeSwitcher` → dropdown appears
2. Click `[data-test-id="gptSubMenuModelTrigger-OpenAI"]` → submenu expands
3. Click `text=GPT 5.5 Think Deeper` → model selected

## Response Scraping

```python
last_msg = page.locator("[data-testid='lastChatMessage']").first
if await last_msg.is_visible(timeout=5000):
    replies = last_msg.locator("[data-testid='markdown-reply']")
    count = await replies.count()
    if count > 0:
        last_reply = replies.nth(count - 1)
        text = await last_reply.inner_text()
```

## Wait for Response Complete

```python
max_wait = 180
interval = 5
elapsed = 5
while elapsed < max_wait:
    stop_btn = page.locator("button[aria-label*='Stop']").first
    if await stop_btn.is_visible(timeout=1000):
        await page.wait_for_timeout(interval)
        elapsed += interval
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    else:
        break
```

## Cookie Injection (for cross-device)

```python
# After login, save cookies
cookies = await context.cookies()
with open("cookies.json", "w") as f:
    json.dump(cookies, f)

# On another device, load cookies
with open("cookies.json", "r") as f:
    cookies = json.load(f)
await context.add_cookies(cookies)
```

## Full Script

See `copilot_m365_v2.py` in the project directory for the complete working script.
