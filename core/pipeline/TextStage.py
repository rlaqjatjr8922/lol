import os
import cv2
from pathlib import Path


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

        stage_idx = self.app_state.stage
        call_idx = self.app_state.text_stage_count

        base_dir = Path(__file__).resolve().parents[2]
        debug_dir = base_dir / "debug" / f"stage_{stage_idx}" / "TextStage"

        original_dir = debug_dir / "original"
        roi_dir = debug_dir / "roi"
        processed_dir = debug_dir / "processed"
        result_dir = debug_dir / "result"

        frame = self.screen_source.capture()
        cv2.imwrite(str(original_dir / f"{call_idx}_0.png"), frame)

        roi = self.roi_extractor.extract(frame, writing_roi)

        if roi is not None:
            cv2.imwrite(str(roi_dir / f"{call_idx}_0.png"), roi)

        matched, matched_path, matched_score, matched_template_img = self.text_checker.check(
            roi=roi,
            template_paths=template_paths,
            threshold=threshold
        )

        last_debug = self.text_checker.last_debug

        processed_idx = 0
        if last_debug is not None:
            roi_steps = last_debug.get("roi_steps", [])
            matched_template_steps = last_debug.get("matched_template_steps", [])

            for _, img in roi_steps:
                if img is not None:
                    cv2.imwrite(
                        str(processed_dir / f"{call_idx}_0_{processed_idx}.png"),
                        img
                    )
                    processed_idx += 1

            for _, img in matched_template_steps:
                if img is not None:
                    cv2.imwrite(
                        str(processed_dir / f"{call_idx}_0_{processed_idx}.png"),
                        img
                    )
                    processed_idx += 1

        if matched_template_img is not None:
            cv2.imwrite(str(result_dir / f"{call_idx}_0.png"), matched_template_img)

        print(f"[TextStage] matched = {matched}")
        print(f"[TextStage] matched_path = {matched_path}")
        print(f"[TextStage] matched_score = {matched_score}")

        self.app_state.text_stage_count += 1

        if not matched:
            print("[TextStage] 매칭 실패")
            return False

        cleaned_name = os.path.basename(matched_path)
        cleaned_name = os.path.splitext(cleaned_name)[0]

        self.app_state.detected_text = cleaned_name

        print(f"[TextStage] 조건 만족: {cleaned_name}")

        self.app_state.next_stage()

        print(f"[TextStage] 다음 stage = {self.app_state.stage}")
        return True