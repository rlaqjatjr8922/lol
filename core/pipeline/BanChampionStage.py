import cv2
from pathlib import Path


class BanChampionStage:
    def __init__(self, app_state, screen_source, roi_extractor, Banchampion_detector):
        self.app_state = app_state
        self.screen_source = screen_source
        self.roi_extractor = roi_extractor
        self.Banchampion_detector = Banchampion_detector

    def run(self, stage_config):
        print("[BanChampionStage] 시작")

        stage_idx = self.app_state.stage
        call_idx = self.app_state.ban_champion_stage_call_count

        base_dir = Path(__file__).resolve().parents[2]
        debug_dir = base_dir / "debug" / f"stage_{stage_idx}" / "BanChampionStage"

        original_dir = debug_dir / "original"
        roi_dir = debug_dir / "roi"
        result_dir = debug_dir / "result"

        original_dir.mkdir(parents=True, exist_ok=True)
        roi_dir.mkdir(parents=True, exist_ok=True)
        result_dir.mkdir(parents=True, exist_ok=True)

        frame = self.screen_source.capture()
        if frame is None:
            print("[BanChampionStage] frame is None")
            return False

        cv2.imwrite(str(original_dir / f"{call_idx}_0.png"), frame)

        pick_slots = stage_config.get("pick_slots", [])

        roi_results = []

        for roi_idx, slot in enumerate(pick_slots):
            roi = self.roi_extractor.extract(frame, slot)

            if roi is not None:
                cv2.imwrite(str(roi_dir / f"{call_idx}_{roi_idx}.png"), roi)
            else:
                print(f"[BanChampionStage] roi is None: index={roi_idx}")
                roi_results.append(None)
                continue

            champ_name, debug_images = self.Banchampion_detector.detect(
                roi,
                stage_config
            )

            if debug_images is None:
                debug_images = {}

            score = debug_images.get("best_score", -1.0)
            if score is None:
                score = -1.0

            print(
                f"[BanChampionStage] roi_idx={roi_idx}, "
                f"champ={champ_name}, "
                f"best_name={debug_images.get('best_name')}, "
                f"score={score}"
            )

            save_order = [
                "roi_resized",
                "roi_gray_big",
                "roi_gray_eq_big",
                "roi_binary_big",
                "best_template_resized",
                "best_template_gray_big",
                "best_template_gray_eq_big",
                "best_template_binary_big",
            ]

            save_idx = 0
            for key in save_order:
                img = debug_images.get(key)
                if img is not None:
                    cv2.imwrite(
                        str(result_dir / f"{call_idx}_{roi_idx}_{save_idx}.png"),
                        img
                    )
                    save_idx += 1

            with open(result_dir / f"{call_idx}_{roi_idx}.txt", "w", encoding="utf-8") as f:
                f.write(f"roi_index: {roi_idx}\n")
                f.write(f"detected_name: {champ_name}\n")
                f.write(f"best_name: {debug_images.get('best_name')}\n")
                f.write(f"best_score: {score}\n")

            roi_results.append(champ_name)

        print(f"[BanChampionStage] ROI별 결과 = {roi_results}")

        self.app_state.ban_champion_stage_call_count += 1

        final_champions = roi_results

        if final_champions != self.app_state.ban_champions:
            print("[BanChampionStage] 변화 감지됨")
            print(f"[BanChampionStage] 이전 = {self.app_state.ban_champions}")

            self.app_state.ban_champions = final_champions
            return True

        print("[BanChampionStage] 변화 없음")
        return False