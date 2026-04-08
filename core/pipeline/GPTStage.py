from core.gpt.prompt_builder import run_ban


class GPTStage:
    def __init__(self, name="ban_gpt"):
        self.name = name

    def run(self, app_state, screen_source):
        print("[GPTStage] 시작")

        try:
            answer = run_ban(app_state)
            app_state.gpt_answer = answer

            print("[GPTStage] 결과 =", answer)
            return True

        except Exception as e:
            print("[GPTStage] 실패:", e)
            return False