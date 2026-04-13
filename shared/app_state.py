class AppState:
    def __init__(self):
        self.stage = 0
        self.gpt_stage = 0
        self.ban_champions = []

        self.debug_save_index = 0

        self.debug = {
            "TextStage": {
                "original": None,
                "roi": [],
                "processed": [],
                "result": [],
            },
            "BanChampionStage": {
                "original": None,
                "roi": [],
                "processed": [],
                "result": [],
            },
            "StickStage": {
                "original": None,
                "roi": [],
                "processed": [],
                "result": [],
            },
        }