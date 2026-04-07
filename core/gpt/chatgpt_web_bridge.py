from core.gpt.chat_page import get_input_box, get_last_answer, wait_until_answer_done


def _clear_input(page, input_box) -> None:
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
        page.keyboard.press("Control+A")
        page.keyboard.press("Backspace")
    except Exception:
        pass


def _fill_prompt(input_box, prompt: str) -> None:
    try:
        input_box.fill(prompt)
    except Exception:
        input_box.type(prompt, delay=10)


def _click_send_button(page) -> bool:
    send_button_selectors = [
        "button[data-testid='send-button']",
        "button[aria-label*='Send']",
        "button:has-text('Send')",
    ]

    for selector in send_button_selectors:
        try:
            btn = page.locator(selector).first
            if btn.is_visible(timeout=500):
                btn.click()
                return True
        except Exception:
            continue

    return False


def send_prompt(page, prompt: str) -> str:
    if not prompt or not prompt.strip():
        raise ValueError("prompt가 비어 있음")

    input_box = get_input_box(page)

    _clear_input(page, input_box)
    _fill_prompt(input_box, prompt)

    sent = _click_send_button(page)

    if not sent:
        try:
            input_box.press("Enter")
            sent = True
        except Exception:
            pass

    if not sent:
        raise RuntimeError("프롬프트 전송 실패")

    wait_until_answer_done(page)

    answer = get_last_answer(page)
    if not answer.strip():
        raise RuntimeError("GPT 응답 읽기 실패")

    return answer