import time


class GPTStage:
    def __init__(self, app_state):
        self.app_state = app_state

    def run(self, stage_key):
        print("[GPTStage] 시작")

        browser = self.app_state.gpt_browser
        stage_data = self.app_state.gpt_stages[stage_key]
        prompt = stage_data["prompt"]

        print("[GPTStage] 프롬프트 전송")
        browser.a(prompt)

        print("[GPTStage] 응답 생성 대기")

        generating = browser.b()

        if generating:
            print("[GPTStage] GPT 응답 생성 중")
        else:
            return False

        answer = browser.c()

        self.app_state.gpt_answer = answer

        print("[GPTStage] 응답 완료")
        print(answer)

        return True