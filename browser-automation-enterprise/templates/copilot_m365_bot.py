"""
Copilot M365 Enterprise Automation Bot v2
==========================================
Automate sending prompts to M365 Copilot via Playwright.

URL: https://m365.cloud.microsoft/chat/

Usage:
  python copilot_m365_v2.py --prompt "Ringkas poin penting" --file chunk_001.txt
  python copilot_m365_v2.py --prompt "Analisis data" --input-dir ./chunks/ --output-dir ./results/
  python copilot_m365_v2.py --prompt "Kapan GPT-5.5 dirilis?" --model gpt-5.5-think-deeper
"""

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("ERROR: Playwright not installed. Run: pip install playwright && python -m playwright install chromium")
    sys.exit(1)


# ── Configuration ──────────────────────────────────────────────────────────

COPILOT_URL = "https://m365.cloud.microsoft/chat/?auth=2&origindomain=Office"
SESSION_DIR = str(Path.home() / ".copilot-m365-session")
COOKIES_FILE = str(Path.home() / ".copilot-m365-session" / "cookies.json")

# Selectors (confirmed working 2026-05-16)
TEXTAREA_SELECTOR = "textarea, [contenteditable='true']"
SEND_BUTTON_SELECTOR = "button[type='submit'], button[aria-label*='Send'], button[aria-label*='Kirim']"
RESPONSE_SELECTOR = "[data-testid='lastChatMessage']"
MODEL_SELECTOR_BTN = "#gptModeSwitcher"
OPENAI_SUBMENU = '[data-test-id="gptSubMenuModelTrigger-OpenAI"]'
FILE_INPUT_SELECTOR = "input[type='file']"


# ── Helpers ─────────────────────────────────────────────────────────────────

def timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def load_cookies() -> list:
    if Path(COOKIES_FILE).exists():
        with open(COOKIES_FILE, "r") as f:
            return json.load(f)
    return []


def save_cookies(cookies: list):
    Path(COOKIES_FILE).parent.mkdir(parents=True, exist_ok=True)
    with open(COOKIES_FILE, "w") as f:
        json.dump(cookies, f, indent=2)
    print(f"[cookies] Saved {len(cookies)} cookies")


# ── Core Bot ────────────────────────────────────────────────────────────────

class CopilotM365Bot:
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.context = None
        self.page = None

    async def start(self, cookies: list = None):
        pw = await async_playwright().start()
        self.context = await pw.chromium.launch_persistent_context(
            SESSION_DIR,
            headless=self.headless,
            viewport={"width": 1280, "height": 900},
            locale="id-ID",
            timezone_id="Asia/Jakarta",
        )
        if cookies:
            await self.context.add_cookies(cookies)
            print(f"[bot] Injected {len(cookies)} cookies")
        self.page = self.context.pages[0] if self.context.pages else await self.context.new_page()

    async def navigate(self, url: str = COPILOT_URL):
        print(f"[bot] Navigating to {url} ...")
        await self.page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await self.page.wait_for_timeout(5000)
        print(f"[bot] Page loaded: {self.page.url}")

    async def wait_for_login(self, timeout: int = 300):
        if "login" in self.page.url.lower():
            print("\n" + "=" * 50)
            print("  ⚠️  LOGIN REQUIRED")
            print("  Browser window is open. Please login.")
            print(f"  Waiting up to {timeout}s...")
            print("=" * 50 + "\n")
            await self.page.wait_for_url(
                lambda url: "login" not in url.lower(),
                timeout=timeout * 1000
            )
            print("[bot] Login successful!")
            cookies = await self.context.cookies()
            save_cookies(cookies)
            await self.page.wait_for_timeout(3000)

    async def select_model(self, model: str = "gpt-5.5-think-deeper"):
        """Select model via 3-step flow: main dropdown → OpenAI submenu → model option."""
        print(f"[bot] Selecting model: {model} ...")
        model_btn = self.page.locator(MODEL_SELECTOR_BTN).first
        if not await model_btn.is_visible(timeout=5000):
            print("[bot] Model selector not found, using current model")
            return False

        await model_btn.click()
        await self.page.wait_for_timeout(1500)

        openai_submenu = self.page.locator(OPENAI_SUBMENU).first
        if await openai_submenu.is_visible(timeout=3000):
            await openai_submenu.click()
            await self.page.wait_for_timeout(1500)
        else:
            print("[bot] OpenAI submenu not found")
            await self.page.keyboard.press("Escape")
            return False

        model_selectors = {
            "gpt-5.5-think-deeper": "text=GPT 5.5 Think Deeper",
            "gpt-5.5": "text=GPT 5.5",
            "think-deeper": "text=Think Deeper",
            "auto": "text=Auto",
        }
        selector = model_selectors.get(model, f"text={model}")
        option = self.page.locator(selector).first
        if await option.is_visible(timeout=3000):
            await option.click()
            await self.page.wait_for_timeout(1000)
            print(f"[bot] Model selected: {model}")
            return True

        print(f"[bot] Model option not found: {model}")
        await self.page.keyboard.press("Escape")
        return False

    async def send_prompt(self, prompt: str, file_path: str = None) -> str:
        page = self.page

        # Find input
        textarea = page.locator(TEXTAREA_SELECTOR).first
        if not await textarea.is_visible(timeout=10000):
            print("[ERROR] No input found!")
            return ""

        # Attach file
        if file_path:
            abs_path = str(Path(file_path).resolve())
            file_input = page.locator(FILE_INPUT_SELECTOR).first
            if await file_input.is_visible(timeout=3000):
                await file_input.set_input_files(abs_path)
                await page.wait_for_timeout(2000)

        # Type prompt
        await textarea.click()
        await page.wait_for_timeout(500)
        await textarea.fill("")
        await textarea.type(prompt, delay=30)
        await page.wait_for_timeout(500)

        # Send
        send_btn = page.locator(SEND_BUTTON_SELECTOR).first
        if await send_btn.is_visible(timeout=3000):
            await send_btn.click()
        else:
            await page.keyboard.press("Enter")

        # Wait for response
        print("[bot] Waiting for response ...")
        await page.wait_for_timeout(3000)
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(2000)

        max_wait = 180
        interval = 5
        elapsed = 5
        while elapsed < max_wait:
            stop_btn = page.locator("button[aria-label*='Stop']").first
            if await stop_btn.is_visible(timeout=1000):
                print(f"[bot] Still generating... ({elapsed}s)")
                await page.wait_for_timeout(interval)
                elapsed += interval
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            else:
                break

        await page.wait_for_timeout(3000)
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(2000)

        # Scrape response
        print("[bot] Scraping response ...")
        last_msg = page.locator(RESPONSE_SELECTOR).first
        if await last_msg.is_visible(timeout=5000):
            replies = last_msg.locator("[data-testid='markdown-reply']")
            count = await replies.count()
            if count > 0:
                last_reply = replies.nth(count - 1)
                text = await last_reply.inner_text()
                if text and len(text) > 10:
                    print(f"[bot] Response received ({len(text)} chars)")
                    return text

        print("[bot] Could not find response element")
        return ""

    async def close(self):
        if self.context:
            print("\n[bot] Browser stays open for 60s for inspection...")
            await asyncio.sleep(60)
            await self.context.close()
            print("[bot] Browser closed")


# ── CLI ─────────────────────────────────────────────────────────────────────

async def main():
    parser = argparse.ArgumentParser(description="Copilot M365 Enterprise Bot v2")
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--file", help="Single file to attach")
    parser.add_argument("--input-dir", help="Directory of .txt chunks")
    parser.add_argument("--output-dir", default="./results")
    parser.add_argument("--model", default=None, help="gpt-5.5-think-deeper, gpt-5.5, think-deeper, auto")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--screenshot", help="Screenshot path (debug)")

    args = parser.parse_args()
    cookies = load_cookies()
    bot = CopilotM365Bot(headless=args.headless)

    try:
        await bot.start(cookies=cookies)
        await bot.navigate()
        await bot.wait_for_login()

        if args.model:
            await bot.select_model(args.model)

        response = await bot.send_prompt(args.prompt, args.file)

        if response:
            out_name = f"{timestamp()}.txt"
            out_path = os.path.join(args.output_dir, out_name)
            ensure_dir(args.output_dir)
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(response)
            print(f"[pipeline] Saved: {out_path}")

        if args.screenshot:
            await bot.page.screenshot(path=args.screenshot)

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
    finally:
        await bot.close()


if __name__ == "__main__":
    asyncio.run(main())
