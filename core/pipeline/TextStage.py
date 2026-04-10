import os


class TextStage:
    def __init__(self, app_state, screen_source, roi_extractor, text_checker):
        self.app_state = app_state
        self.screen_source = screen_source
        self.roi_extractor = roi_extractor
        self.text_checker = text_checker

    def run(self, stage_config):
        print("[TextStage] 시작")

        if stage_config is None:
            print("[TextStage] stage_config 없음")
            return False

        writing_roi = stage_config.get("writing")
        template_paths = stage_config.get("template_path", [])
        threshold = stage_config.get("threshold", 0.03)

        if writing_roi is None:
            print("[TextStage] writing 값 없음")
            return False

        if not template_paths:
            print("[TextStage] template_path 값 없음")
            return False

        frame = self.screen_source.capture()
        if frame is None:
            print("[TextStage] frame 캡처 실패")
            return False

        self.app_state.current_frame = frame

        roi = self.roi_extractor.extract(frame, writing_roi)
        if roi is None:
            print("[TextStage] ROI 추출 실패")
            return False

        self.app_state.current_roi = roi

        matched_path, matched_score = self.text_checker.check(
            roi=roi,
            template_paths=template_paths,
            threshold=threshold
        )

        print(f"[TextStage] matched_path = {matched_path}")
        print(f"[TextStage] matched_score = {matched_score}")

        if matched_path is None:
            print("[TextStage] 조건 불만족")
            return False

        cleaned_name = os.path.basename(matched_path)
        print(f"[TextStage] 조건 만족: {cleaned_name}")

        self.app_state.last_matched_template = cleaned_name
        self.app_state.last_matched_score = matched_score

        if hasattr(self.app_state, "stage"):
            self.app_state.stage += 1
            print(f"[TextStage] 다음 stage = {self.app_state.stage}")

        return True