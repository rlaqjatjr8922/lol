import os


class TextStage:
    def __init__(self, app_state, screen_source, roi_extractor, text_checker):
        self.app_state = app_state
        self.screen_source = screen_source
        self.roi_extractor = roi_extractor
        self.text_checker = text_checker

    def run(self, stage_config):
        print("[TextStage] 시작")

        writing_roi = stage_config["writing"]
        template_paths = stage_config["template_path"]
        threshold = stage_config["threshold"]

        frame = self.screen_source.capture()
        self.app_state.current_frame = frame

        roi_list = []
        roi = self.roi_extractor.extract(frame, writing_roi)
        roi_list.append(roi)

        current_results = []

        debug_stage = self.app_state.debug["TextStage"]
        debug_stage["original"] = frame
        debug_stage["roi"] = []
        debug_stage["processed"] = []
        debug_stage["result"] = []

        for roi in roi_list:
            self.app_state.current_roi = roi

            matched, matched_path, matched_score, matched_template_img = self.text_checker.check(
                roi=roi,
                template_paths=template_paths,
                threshold=threshold
            )

            if roi is not None:
                debug_stage["roi"].append(roi)

            last_debug = self.text_checker.last_debug

            if last_debug is not None:
                roi_steps = last_debug.get("roi_steps", [])
                matched_template_steps = last_debug.get("matched_template_steps", [])

                for step_name, img in roi_steps:
                    if img is not None:
                        debug_stage["processed"].append(img)

                for step_name, img in matched_template_steps:
                    if img is not None:
                        debug_stage["processed"].append(img)

            if matched_template_img is not None and roi is not None:
                debug_stage["result"].append([matched_template_img, roi, matched_score])

            current_results.append((matched, matched_path, matched_score))

        matched, matched_path, matched_score = current_results[0]

        print(f"[TextStage] matched = {matched}")
        print(f"[TextStage] matched_path = {matched_path}")
        print(f"[TextStage] matched_score = {matched_score}")

        if not matched:
            print("[TextStage] 매칭 실패")
            return False

        cleaned_name = os.path.basename(matched_path)
        print(f"[TextStage] 조건 만족: {cleaned_name}")

        self.app_state.last_matched_template = cleaned_name
        self.app_state.last_matched_score = matched_score

        self.app_state.stage += 1
        print(f"[TextStage] 다음 stage = {self.app_state.stage}")

        return True