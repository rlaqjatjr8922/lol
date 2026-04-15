import cv2
from pathlib import Path


class BanChampionStage:
    def __init__(self, app_state, screen_source, roi_extractor, champion_detector):
        self.app_state = app_state
        self.screen_source = screen_source
        self.roi_extractor = roi_extractor
        self.champion_detector = champion_detector

    def run(self, stage_config):
        print("[BanChampionStage] 시작")

        stage_idx = self.app_state.stage
        call_idx = self.app_state.ban_champion_stage_call_count

        base_dir = Path(__file__).resolve().parents[2]
        debug_dir = base_dir / "debug" / f"stage_{stage_idx}" / "BanChampionStage"

        original_dir = debug_dir / "original"
        roi_dir = debug_dir / "roi"
        processed_dir = debug_dir / "processed"
        result_dir = debug_dir / "result"

        frame = self.screen_source.capture()
        cv2.imwrite(str(original_dir / f"{call_idx}_0.png"), frame)

        pick_slots = stage_config["pick_slots"]

        roi_list = []
        for slot in pick_slots:
            roi = self.roi_extractor.extract(frame, slot)
            roi_list.append(roi)

        current_champions = []

        for roi_idx, roi in enumerate(roi_list):
            if roi is not None:
                cv2.imwrite(str(roi_dir / f"{call_idx}_{roi_idx}.png"), roi)

            champ_name = self.champion_detector.detect(roi, stage_config)

            last_debug = self.champion_detector.last_debug

            processed_idx = 0
            if last_debug is not None:
                roi_steps = last_debug.get("roi_steps", [])
                matched_template_steps = last_debug.get("matched_template_steps", [])

                for _, img in roi_steps:
                    if img is not None:
                        cv2.imwrite(
                            str(processed_dir / f"{call_idx}_{roi_idx}_{processed_idx}.png"),
                            img
                        )
                        processed_idx += 1

                for _, img in matched_template_steps:
                    if img is not None:
                        cv2.imwrite(
                            str(processed_dir / f"{call_idx}_{roi_idx}_{processed_idx}.png"),
                            img
                        )
                        processed_idx += 1

            result_text = "None" if champ_name is None else str(champ_name)
            with open(result_dir / f"{call_idx}_{roi_idx}.txt", "w", encoding="utf-8") as f:
                f.write(result_text)

            current_champions.append(champ_name)

        print(f"[BanChampionStage] 현재 챔피언 = {current_champions}")

        self.app_state.ban_champion_stage_call_count += 1

        if current_champions != self.app_state.ban_champions:
            print("[BanChampionStage] 변화 감지됨")
            print(f"[BanChampionStage] 이전 = {self.app_state.ban_champions}")

            self.app_state.ban_champions = current_champions
            return True

        print("[BanChampionStage] 변화 없음")
        return False