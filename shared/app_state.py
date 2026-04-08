class AppState:
    def __init__(self):
        self.current_stage = 0
        self.a = 0
        self.current_frame = None
        self.gpt_answer = None
        self.matched_template_name = None
        self.frequent_champions = None