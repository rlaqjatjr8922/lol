import time


def get_chatgpt_page(context):
    for pg in context.pages:
        try:
            url = pg.url or ""
        except Exception:
            url = ""

        if "chatgpt.com" in url or "chat.openai.com" in url:
            try:
                pg.bring_to_front()
            except Exception:
                pass
            return pg

    page = context.new_page()
    page.goto("https://chatgpt.com", wait_until="domcontentloaded")
    return page


def get_input_box(page):
    selectors = [
        "div[contenteditable='true'][role='textbox']",
        "div[contenteditable='true']",
        "textarea",
    ]

    end = time.time() + 30

    while time.time() < end:
        for sel in selectors:
            loc = page.locator(sel)
            try:
                count = loc.count()
            except Exception:
                count = 0

            if count <= 0:
                continue

            for i in range(count):
                el = loc.nth(i)
                try:
                    if el.is_visible():
                        return el
                except Exception:
                    pass

        page.wait_for_timeout(500)

    raise RuntimeError("ChatGPT 입력창을 찾지 못했습니다.")


def wait_until_answer_done(page, timeout_ms=120000):
    start = time.time()
    saw_generation = False

    while (time.time() - start) * 1000 < timeout_ms:
        try:
            stop_btn = page.locator("button[data-testid='stop-button']")
            if stop_btn.count() > 0 and stop_btn.first.is_visible():
                saw_generation = True
                page.wait_for_timeout(700)
                continue
        except Exception:
            pass

        try:
            streaming = page.locator("[data-testid='conversation-turn-typing-indicator']")
            if streaming.count() > 0 and streaming.first.is_visible():
                saw_generation = True
                page.wait_for_timeout(700)
                continue
        except Exception:
            pass

        if saw_generation:
            page.wait_for_timeout(1000)
            return

        page.wait_for_timeout(700)

    raise RuntimeError("ChatGPT 응답 대기 시간 초과")


def get_last_answer(page) -> str:
    selectors = [
        "[data-message-author-role='assistant']",
        "[data-testid^='conversation-turn-']",
        "article",
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