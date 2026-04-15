import subprocess
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

        # 🔥 자동 실행

    def start_and_connect(self):
        self.start()
        self.connect()
    # -------------------------
    # 크롬 실행
    # -------------------------
    def start(self):
        print("[browser] 크롬 실행")

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

    # -------------------------
    # playwright 연결
    # -------------------------
    def connect(self):
        print("[browser] playwright 연결")

        self.playwright = sync_playwright().start()

        self.browser = self.playwright.chromium.connect_over_cdp(
            f"http://127.0.0.1:{self.debug_port}"
        )

        if not self.browser.contexts:
            raise RuntimeError("context 없음")

        self.context = self.browser.contexts[0]

        # 페이지 가져오기 or 생성
        if self.context.pages:
            self.page = self.context.pages[0]
        else:
            self.page = self.context.new_page()
            self.page.goto(self.url)

        print("[browser] 연결 완료")

    # -------------------------
    # 응답 중지 버튼 클릭
    # -------------------------
    def stop_response(self):
        selectors = [
            "button[data-testid='stop-button']",
            "button[aria-label*='Stop']",
        ]
    
        for selector in selectors:
            try:
                btn = self.page.locator(selector).first
                if btn.is_visible(timeout=300):
                    btn.click()
                    print("[browser] 응답 중지")
                    return True
            except Exception:
                continue
            
        return False

    # -------------------------
    # 프롬프트 전송
    # -------------------------
    def send_new_prompt(self, text):
        if not text or not text.strip():
            raise ValueError("입력값 없음")

        input_box = self.page.locator(
            "div[contenteditable='true'][role='textbox']"
        ).first

        input_box.wait_for(state="visible", timeout=10000)

        # 기존 내용 삭제
        try:
            input_box.click()
            self.page.keyboard.press("Control+A")
            self.page.keyboard.press("Backspace")
        except Exception:
            pass

        # 입력
        try:
            input_box.fill(text)
        except Exception:
            input_box.type(text, delay=10)

        # 전송
        input_box.press("Enter")

        print("[browser] 전송 완료")

    # -------------------------
    # 생성 중 여부 (Stop 버튼 기준)
    # -------------------------
    def is_generating(self):
        try:
            btn = self.page.locator("button[data-testid='stop-button']").first
            return btn.is_visible(timeout=200)
        except:
            return False

    # -------------------------
    # 마지막 응답 가져오기
    # -------------------------
    def get_last_answer(self):
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

                text = nodes.nth(count - 1).inner_text().strip()

                if text:
                    return text

            except Exception:
                continue

        return ""

