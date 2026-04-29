class AppState:
    def __init__(self):
        # 현재 단계
        self.stage = 0
        self.gpt_stage = 0
        self.previous_stage=0

        # 결과 데이터
        self.ban_champions = {
        "ally": [],
        "enemy": []
        }
        self.detected_text = None

        self.gpt_results = None
        self.gpt_parsed = {}

        # Pick 결과
        self.pick_champions = {
            "ally": [],
            "enemy": []
        }

        # Stick 결과
        self.lit_bars = [[], [], None]
        self.lit_bars_calc = [(), ()]
        self.pick_turn_team = None
        self.is_my_turn = False
        self.pick_order = None
        self.stick_last_info = None

        # 디버그 카운터
        self.text_stage_count = 0
        self.ban_champion_stage_call_count = 0
        self.pick_champion_stage_call_count = 0
        self.stick_stage_count = 0

    def next_stage(self):
        self.stage += 1
        self.reset_stage_counters()

    def reset_stage_counters(self):
        self.text_stage_count = 0
        self.ban_champion_stage_call_count = 0
        self.pick_champion_stage_call_count = 0
        self.stick_stage_count = 0
        self.gpt_stage = 0
        self.previous_stage=0