class AppState:
    def __init__(self):
        # 현재 단계
        self.stage = 0
        self.gpt_stage = 0

        # 결과 데이터
        self.ban_champions = []
        self.detected_text = None

        self.gpt_results = None      # GPT 원본 응답 문자열
        self.gpt_parsed = {}         # GPT 파싱 결과 dict

        # 디버그 카운터
        self.text_stage_count = 0
        self.ban_champion_stage_call_count = 0
        self.stick_stage_count = 0

    # stage 변경 시 호출
    def next_stage(self):
        self.stage += 1
        self.reset_stage_counters()

    # 카운터 초기화
    def reset_stage_counters(self):
        self.text_stage_count = 0
        self.ban_champion_stage_call_count = 0
        self.stick_stage_count = 0
        self.gpt_stage = 0