# gpt/gpt_runner.py

from playwright.sync_api import sync_playwright

from core.gpt.browser import ensure_debug_chrome
from core.gpt.chat_page import (
    get_chatgpt_page,
    ensure_chatgpt_page_ready,
)
from core.gpt.chatgpt_web_bridge import send_prompt


def run_prompt(prompt: str):
    with sync_playwright() as p:
        ensure_debug_chrome()

        browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        context = browser.contexts[0]

        page = get_chatgpt_page(context)
        ensure_chatgpt_page_ready(page)

        answer = send_prompt(page, prompt)
        return answer