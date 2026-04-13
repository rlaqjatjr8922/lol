import subprocess
import time
from pathlib import Path

from playwright.sync_api import sync_playwright


class GPTBrowser:
    def __init__(self):
        self.chrome_path = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
        self.debug_port = 9222
        self.user_data_dir = Path(r"C:\chrome-debug")
        self.url = "https://chatgpt.com"

        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    def start(self):
        print("[browser] GPT 크롬 디버그 모드 실행")

        self.user_data_dir.mkdir(parents=True, exist_ok=True)

        subprocess.Popen(
            [
                str(self.chrome_path),
                f"--remote-debugging-port={self.debug_port}",
                f"--user-data-dir={self.user_data_dir}",
                self.url,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        time.sleep(2)

    def connect(self):
        print("[browser] CDP 연결 시도")

        self.playwright = sync_playwright().start()

        self.browser = self.playwright.chromium.connect_over_cdp(
            f"http://127.0.0.1:{self.debug_port}"
        )

        if not self.browser.contexts:
            raise RuntimeError("브라우저 context가 없음")

        self.context = self.browser.contexts[0]

        self.page = self._get_chatgpt_page()

        try:
            self.page.wait_for_load_state("domcontentloaded", timeout=15000)
        except Exception:
            pass

        time.sleep(2)

        print("[browser] 연결 완료")
        return self.page

    def start_and_connect(self):
        self.start()
        return self.connect()

    def _is_chatgpt_page(self, page):
        try:
            url = page.url or ""
            return "chatgpt.com" in url or "chat.openai.com" in url
        except Exception:
            return False

    def _get_chatgpt_page(self):
        for page in self.context.pages:
            if self._is_chatgpt_page(page):
                try:
                    page.bring_to_front()
                except Exception:
                    pass
                return page

        page = self.context.new_page()
        page.goto(self.url, wait_until="domcontentloaded", timeout=30000)
        return page

    def _get_input_box(self):
        selectors = [
            "div[contenteditable='true'][role='textbox']",
            "div[contenteditable='true']",
            "textarea",
        ]

        for selector in selectors:
            try:
                locator = self.page.locator(selector).first
                locator.wait_for(state="visible", timeout=10000)
                return locator
            except Exception:
                continue

        raise RuntimeError("ChatGPT 입력창을 찾지 못함")

    def _clear_input(self, input_box):
        try:
            input_box.click()
        except Exception:
            pass

        try:
            input_box.fill("")
            return
        except Exception:
            pass

        try:
            self.page.keyboard.press("Control+A")
            self.page.keyboard.press("Backspace")
        except Exception:
            pass

    def _click_send_button(self):
        selectors = [
            "button[data-testid='send-button']",
            "button[aria-label*='Send']",
            "button:has-text('Send')",
        ]

        for selector in selectors:
            try:
                btn = self.page.locator(selector).first
                if btn.is_visible(timeout=500):
                    btn.click()
                    return True
            except Exception:
                continue

        return False

    def a(self, prompt):
        if not prompt or not prompt.strip():
            raise ValueError("prompt가 비어 있음")

        input_box = self._get_input_box()
        self._clear_input(input_box)

        try:
            input_box.fill(prompt)
        except Exception:
            input_box.type(prompt, delay=10)

        sent = self._click_send_button()

        if not sent:
            try:
                input_box.press("Enter")
                sent = True
            except Exception:
                pass

        if not sent:
            raise RuntimeError("프롬프트 전송 실패")

        print("[browser] 프롬프트 전송 완료")

    def b(self):
        selectors = [
            "button:has-text('Stop')",
            "button[aria-label*='Stop']",
        ]

        for selector in selectors:
            try:
                btn = self.page.locator(selector).first
                if btn.is_visible(timeout=300):
                    return True
            except Exception:
                continue

        return False

    def _get_last_answer(self):
        selectors = [
            "[data-message-author-role='assistant']",
            "article",
        ]

        for selector in selectors:
            try:
                nodes = self.page.locator(selector)
                count = nodes.count()

                if count == 0:
                    continue

                for i in range(count - 1, -1, -1):
                    text = nodes.nth(i).inner_text().strip()
                    if text:
                        return text
            except Exception:
                continue

        return ""

    def c(self, timeout_sec=120):
        start = time.time()
        stable_count = 0
        last_text = ""

        while time.time() - start < timeout_sec:
            if self.b():
                time.sleep(0.8)
                continue

            current_text = self._get_last_answer()

            if current_text and current_text == last_text:
                stable_count += 1
            else:
                stable_count = 0
                last_text = current_text

            if stable_count >= 3:
                print("[browser] 응답 읽기 완료")
                return current_text

            time.sleep(1.0)

        raise TimeoutError("GPT 응답 대기 시간 초과")