# Reference: Working Copilot M365 Playwright Bot

The full working script is at `Documents\copilot_hermes\copilot_bot.py` on the user's machine.

## Key Technical Details from Testing

### What Works
- Playwright opens Copilot M365 page successfully
- File upload via `set_input_files()` works
- Prompt typing via `type()` works
- Response scraping via `inner_text()` on `main` element works
- Persistent context saves session (login once)
- Screenshot capture for debugging works

### Selectors That Work (as of May 2026)
```python
PROMPT_TEXTAREA_SELECTOR = "textarea[data-id='prompt-textarea']"
SEND_BUTTON_SELECTOR = "button[data-id='send-button']"
RESPONSE_SELECTOR = "[data-content-editable-root]"
FILE_INPUT_SELECTOR = "input[type='file']"
MODEL_DROPDOWN_SELECTOR = "button[aria-label='Model selector']"
```

### Fallback Selectors
If primary selectors fail (UI updates), use:

    # Textarea fallback
    page.locator("textarea").first

    # Response fallback
    page.locator("main").first

### Response Scraping Pattern

    # Try specific selector first
    response_el = page.locator(RESPONSE_SELECTOR).last
    if await response_el.is_visible(timeout=5000):
        text = await response_el.inner_text()
    else:
        # Fallback to main content area
        main = page.locator("main").first
        if await main.is_visible(timeout=3000):
            text = await main.inner_text()

### Waiting for Response Complete

    # Wait until "Stop generating" button disappears
    stop_btn = page.locator("button[aria-label='Stop generating']").first
    if await stop_btn.is_visible(timeout=1000):
        # Still generating, wait more
        await page.wait_for_timeout(3000)

### Python Path for Hermes Venv
    C:\Users\MSI Thin 15\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe

### Running from Hermes TUI
    terminal("python Documents/copilot_hermes/copilot_bot.py --prompt 'Ringkas poin penting' --file chunks/chunk_001.txt")

### Asyncio Cleanup Warning (Windows)
The script may show `ValueError: I/O operation on closed pipe` at exit. This is a known Windows asyncio issue — harmless, can be ignored.

## Integration with Hermes Orchestrator

The script is called from Hermes TUI via the `terminal` tool:

    User: "Proses semua chunk di folder chunks/"
      ↓
    Hermes (Gemma):
      1. search_files("*.txt", path="./chunks/")
      2. For each file:
         terminal("python copilot_bot.py --prompt '...' --file ...")
      3. Collect results from results/ folder
      4. Feed to LLM Wiki

Hermes never reads file contents — only paths and commands.
