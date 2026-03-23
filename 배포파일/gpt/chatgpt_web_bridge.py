import subprocess
import time

import requests
from playwright.sync_api import sync_playwright

PORT = 9222
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
USER_DATA_DIR = r"C:\chrome-debug"


def is_debug_browser_running():
    try:
        r = requests.get(f"http://127.0.0.1:{PORT}/json/version", timeout=2)
        return r.status_code == 200
    except Exception:
        return False


def start_debug_chrome():
    subprocess.Popen([
        CHROME_PATH,
        f"--remote-debugging-port={PORT}",
        f"--user-data-dir={USER_DATA_DIR}",
        "https://chatgpt.com"
    ])
    for _ in range(20):
        if is_debug_browser_running():
            return True
        time.sleep(1)
    return False


def get_chatgpt_page(context):
    for pg in context.pages:
        if "chatgpt.com" in pg.url or "chat.openai.com" in pg.url:
            return pg
    page = context.new_page()
    page.goto("https://chatgpt.com", wait_until="domcontentloaded")
    return page


def get_input_box(page):
    selectors = ["div[contenteditable='true']", "textarea"]
    end = time.time() + 20
    while time.time() < end:
        for sel in selectors:
            loc = page.locator(sel)
            try:
                count = loc.count()
            except Exception:
                count = 0
            for i in range(count):
                el = loc.nth(i)
                try:
                    if el.is_visible():
                        return el
                except Exception:
                    pass
        page.wait_for_timeout(300)
    raise RuntimeError("입력창 못찾음")


def wait_until_answer_done(page):
    saw_generation = False
    while True:
        stop_btn = page.locator("button[data-testid='stop-button']")
        try:
            visible = stop_btn.count() > 0 and stop_btn.first.is_visible()
        except Exception:
            visible = False
        if visible:
            saw_generation = True
        else:
            if saw_generation:
                return
        page.wait_for_timeout(700)


def get_last_answer(page):
    selectors = [
        "[data-message-author-role='assistant']",
        "[data-testid^='conversation-turn-']",
        "article"
    ]
    for sel in selectors:
        loc = page.locator(sel)
        try:
            count = loc.count()
        except Exception:
            count = 0
        if count <= 0:
            continue
        for i in range(count - 1, -1, -1):
            try:
                txt = loc.nth(i).inner_text().strip()
                if txt:
                    return txt
            except Exception:
                pass
    return ""


def ask_chatgpt(prompt: str) -> str:
    if not is_debug_browser_running():
        if not start_debug_chrome():
            return ""
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(f"http://127.0.0.1:{PORT}")
        if not browser.contexts:
            return ""
        context = browser.contexts[0]
        page = get_chatgpt_page(context)
        page.bring_to_front()
        page.wait_for_timeout(1500)
        box = get_input_box(page)
        box.click()
        try:
            page.keyboard.press("Control+A")
            page.keyboard.press("Backspace")
        except Exception:
            pass
        try:
            box.fill(prompt)
        except Exception:
            page.keyboard.insert_text(prompt)
        page.wait_for_timeout(300)
        page.keyboard.press("Enter")
        wait_until_answer_done(page)
        return get_last_answer(page)
