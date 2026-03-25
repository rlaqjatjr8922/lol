from playwright.sync_api import sync_playwright

from gpt.browser import is_debug_browser_running, start_debug_chrome, PORT
from gpt.chat_page import (
    get_chatgpt_page,
    get_input_box,
    wait_until_answer_done,
    get_last_answer,
)


def ask_chatgpt(prompt: str) -> str:
    prompt = (prompt or "").strip()
    if not prompt:
        return ""

    if not is_debug_browser_running():
        if not start_debug_chrome():
            return "오류: 디버그 크롬 실행 실패"

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(f"http://127.0.0.1:{PORT}")

        if not browser.contexts:
            return "오류: 크롬 컨텍스트 없음"

        context = browser.contexts[0]
        page = get_chatgpt_page(context)

        try:
            page.bring_to_front()
        except Exception:
            pass

        page.wait_for_timeout(1500)

        input_box = get_input_box(page)

        try:
            input_box.scroll_into_view_if_needed()
        except Exception:
            pass

        page.wait_for_timeout(300)

        # 입력창 포커스 잡기
        clicked = False
        click_errors = []

        for _ in range(5):
            try:
                input_box.click(timeout=3000)
                clicked = True
                break
            except Exception as e:
                click_errors.append(str(e))
                page.wait_for_timeout(500)

        if not clicked:
            try:
                page.evaluate(
                    """
                    (el) => {
                        el.focus();
                    }
                    """,
                    input_box,
                )
                clicked = True
            except Exception as e:
                click_errors.append(str(e))

        if not clicked:
            return "오류: 입력창 클릭 실패\n" + "\n".join(click_errors)

        page.wait_for_timeout(300)

        # 기존 입력 내용 삭제
        try:
            input_box.press("Control+A")
            input_box.press("Backspace")
        except Exception:
            try:
                page.keyboard.press("Control+A")
                page.keyboard.press("Backspace")
            except Exception:
                pass

        page.wait_for_timeout(200)

        # 프롬프트 전체를 한 번에 입력
        injected = False
        inject_errors = []

        # 1순위: contenteditable/textbox 직접 입력
        try:
            page.evaluate(
                """
                ({text}) => {
                    const active = document.activeElement;
                    if (!active) return false;

                    if (
                        active.getAttribute("contenteditable") === "true" ||
                        active.getAttribute("role") === "textbox"
                    ) {
                        active.textContent = text;
                        active.dispatchEvent(new Event("input", { bubbles: true }));
                        return true;
                    }

                    if (active.tagName === "TEXTAREA") {
                        active.value = text;
                        active.dispatchEvent(new Event("input", { bubbles: true }));
                        return true;
                    }

                    return false;
                }
                """,
                {"text": prompt},
            )
            injected = True
        except Exception as e:
            inject_errors.append(str(e))

        # 2순위: type으로 직접 입력
        if not injected:
            try:
                input_box.type(prompt, delay=0)
                injected = True
            except Exception as e:
                inject_errors.append(str(e))

        if not injected:
            return "오류: 프롬프트 입력 실패\n" + "\n".join(inject_errors)

        page.wait_for_timeout(500)

        # 전송 버튼이 있으면 버튼 우선, 없으면 Enter
        sent = False
        send_errors = []

        send_selectors = [
            "button[data-testid='send-button']",
            "button[aria-label*='전송']",
            "button[aria-label*='Send']",
        ]

        for sel in send_selectors:
            try:
                btn = page.locator(sel)
                if btn.count() > 0 and btn.first.is_visible():
                    btn.first.click(timeout=3000)
                    sent = True
                    break
            except Exception as e:
                send_errors.append(f"{sel}: {e}")

        if not sent:
            try:
                input_box.press("Enter")
                sent = True
            except Exception as e:
                send_errors.append(str(e))

        if not sent:
            return "오류: 전송 실패\n" + "\n".join(send_errors)

        try:
            wait_until_answer_done(page)
            answer = get_last_answer(page).strip()
        except Exception as e:
            return f"오류: 응답 읽기 실패\n{e}"

        try:
            browser.close()
        except Exception:
            pass

        return answer