class DetectStage:
    def __init__(self, stage_key, stages, roi_extractor, checker):
        self.stage_key = stage_key
        self.stages = stages
        self.roi_extractor = roi_extractor
        self.checker = checker

    def run(self, app_state, screen_source):
        print(f"[DetectStage {self.stage_key}] 시작")

        stage = self.stages[self.stage_key]

        frame = screen_source.capture()
        if frame is None:
            print("frame 없음")
            return False

        app_state.current_frame = frame

        roi_box = stage.get("writing")
        template_paths = stage.get("template_path", [])

        roi = self.roi_extractor.extract(frame, roi_box)
        if roi is None:
            return False

        result, name, score = self.checker.check(roi, template_paths, threshold=stage.get('threshold'))

        print(f"result = {result}, name = {name}, score = {score:.3f}")

        if not result:
            print(f"[DetectStage {self.stage_key}] template match 실패, template_paths={template_paths}")

        return result