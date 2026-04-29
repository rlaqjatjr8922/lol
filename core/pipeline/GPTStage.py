class GPTStage:
    def __init__(self, app_state, gpt_browser):
        self.app_state = app_state
        self.gpt_browser = gpt_browser

    # -------------------------
    # 프롬프트 생성
    # -------------------------
    def _build_prompt(self, prompt_data):
        prompt_template = prompt_data["prompt"]
    
        detected = self.app_state.detected_text or "알 수 없음"
    
        bans = self.app_state.ban_champions
    
        if not bans:
            bans_str = "없음"
        else:
            bans_str = ", ".join(bans)
    
        return prompt_template.format(
            detected_text=detected,
            ban_champions=bans_str
        )
    
    # -------------------------
    # GPT 결과 파싱
    # -------------------------
    def _parse(self, text):
        result = {}

        if not text:
            return result

        text = text.strip()

        # ``` 제거 (GPT가 가끔 붙임)
        text = text.replace("```", "")

        # { } 제거
        text = text.strip("{}")

        lines = text.splitlines()

        for line in lines:
            line = line.strip().rstrip(",")

            if not line or ":" not in line:
                continue

            key, value = line.split(":", 1)

            key = key.strip()
            value = value.strip().strip("[]")

            tags = [v.strip() for v in value.split(",") if v.strip()]

            result[key] = tags

        return result

    # -------------------------
    # 실행
    # -------------------------
    def run(self, prompt_data):
        prompt = self._build_prompt(prompt_data)

        # 0단계
        if self.app_state.gpt_stage == 0:
            print(f"[GPTStage] 지우기")
            self.gpt_browser.stop_response()
            self.app_state.gpt_stage = 1

        # 1단계
        if self.app_state.gpt_stage == 1:
            print(f"[GPTStage] 프롬프트 전송: {prompt}")
            self.gpt_browser.send_new_prompt(prompt)
            self.app_state.gpt_stage = 2

        # 2단계
        if self.app_state.gpt_stage == 2:
            print(f"[GPTStage] 응답 대기")
            if self.gpt_browser.is_generating():
                return False
            else:
                self.app_state.gpt_stage = 3

        # 3단계
        if self.app_state.gpt_stage == 3:
            print(f"[GPTStage] 응답 받음, 파싱 시작")
            raw = self.gpt_browser.get_last_answer()

            self.app_state.gpt_results = raw
            self.app_state.gpt_parsed = self._parse(raw)
            print(f"[GPTStage] 파싱 결과: {raw}=> {self.app_state.gpt_parsed}")

            return True

        return False