# stages.py

class StickStage:
    def __init__(self, stage_key, stages, roi_extractor, stick_checker):
        self.stage_key = stage_key
        self.stages = stages
        self.roi_extractor = roi_extractor
        self.stick_checker = stick_checker

    def run(self, app_state, screen_source):
        print(f"[StickStage {self.stage_key}] 시작")

        stage = self.stages.get(self.stage_key)
        if stage is None:
            return False

        frame = screen_source.capture()
        if frame is None:
            return False

        app_state.current_frame = frame

        ally_roi = self.roi_extractor.extract(frame, stage.get("ally_turn_bar_roi"))
        enemy_roi = self.roi_extractor.extract(frame, stage.get("enemy_turn_bar_roi"))

        if ally_roi is None or enemy_roi is None:
            return False

        lit_bars = self.stick_checker.check(
            ally_roi,
            enemy_roi,
            colors=["blue", "yellow", "red"],
            stage_config=stage,
        )

        app_state.lit_bars = lit_bars
        print("lit_bars =", lit_bars)

        return len(lit_bars) > 0