import time


CHATGPT_URL_KEYWORDS = ("chatgpt.com", "chat.openai.com")
CHATGPT_HOME_URL = "https://chatgpt.com"


def _is_chatgpt_page(page) -> bool:
    try:
        url = page.url or ""
        return any(keyword in url for keyword in CHATGPT_URL_KEYWORDS)
    except Exception:
        return False


def get_chatgpt_page(context):
    # 이미 열린 ChatGPT 탭 찾기
    for page in context.pages:
        if _is_chatgpt_page(page):
            try:
                page.bring_to_front()
            except Exception:
                pass
            return page

    # 없으면 새 탭 생성
    page = context.new_page()
    page.goto(CHATGPT_HOME_URL, wait_until="domcontentloaded", timeout=30000)
    return page


def ensure_chatgpt_page_ready(page) -> None:
    try:
        page.wait_for_load_state("domcontentloaded", timeout=15000)
    except Exception:
        pass

    # 로그인/로딩/초기 렌더링 대기용
    time.sleep(2.0)


def get_input_box(page):
    selectors = [
        "div[contenteditable='true'][role='textbox']",
        "div[contenteditable='true']",
        "textarea",
    ]

    for selector in selectors:
        try:
            locator = page.locator(selector).first
            locator.wait_for(state="visible", timeout=10000)
            return locator
        except Exception:
            continue

    raise RuntimeError("ChatGPT 입력창을 찾지 못함")


def get_last_answer(page) -> str:
    selectors = [
        "[data-message-author-role='assistant']",
        "article",
    ]

    for selector in selectors:
        try:
            nodes = page.locator(selector)
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


def wait_until_answer_done(page, timeout_sec: int = 120) -> None:
    start = time.time()
    stable_count = 0
    last_text = ""

    while time.time() - start < timeout_sec:
        # 생성 중인지 확인
        try:
            stop_btn = page.locator("button:has-text('Stop')").first
            if stop_btn.is_visible(timeout=300):
                time.sleep(0.8)
                continue
        except Exception:
            pass

        try:
            current_text = get_last_answer(page)
        except Exception:
            current_text = ""

        if current_text and current_text == last_text:
            stable_count += 1
        else:
            stable_count = 0
            last_text = current_text

        if stable_count >= 3:
            return

        time.sleep(1.0)

    raise TimeoutError("GPT 응답 대기 시간 초과")