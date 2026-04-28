import cv2
from pathlib import Path


class PickChampionStage:
    def __init__(self, app_state, screen_source, roi_extractor, champion_detector):
        self.app_state = app_state
        self.screen_source = screen_source
        self.roi_extractor = roi_extractor
        self.champion_detector = champion_detector

    def _get_active_pick_slots(self, pick_slots):
        lit_bars_calc = getattr(self.app_state, "lit_bars_calc", [(), ()])

        ally_active_slots = lit_bars_calc[0] if len(lit_bars_calc) > 0 else ()
        enemy_active_slots = lit_bars_calc[1] if len(lit_bars_calc) > 1 else ()

        active_slots = list(ally_active_slots) + list(enemy_active_slots)

        result = []

        for slot_no in active_slots:
            # lit_bars_calc는 1번 슬롯부터 시작한다고 보고 -1 처리
            pick_idx = slot_no - 1

            if 0 <= pick_idx < len(pick_slots):
                result.append((pick_idx, pick_slots[pick_idx]))

        return result

    def run(self, stage_config):
        print("[PickChampionStage] 시작")

        stage_idx = self.app_state.stage
        call_idx = self.app_state.pick_champion_stage_call_count

        base_dir = Path(__file__).resolve().parents[2]
        debug_dir = base_dir / "debug" / f"stage_{stage_idx}" / "PickChampionStage"

        original_dir = debug_dir / "original"
        roi_dir = debug_dir / "roi"
        processed_dir = debug_dir / "processed"
        result_dir = debug_dir / "result"

        original_dir.mkdir(parents=True, exist_ok=True)
        roi_dir.mkdir(parents=True, exist_ok=True)
        processed_dir.mkdir(parents=True, exist_ok=True)
        result_dir.mkdir(parents=True, exist_ok=True)

        frame = self.screen_source.capture()
        if frame is None:
            print("[PickChampionStage] frame is None")
            return False

        cv2.imwrite(str(original_dir / f"{call_idx}_0.png"), frame)

        pick_slots = stage_config.get("pick_slots", [])

        active_pick_slots = self._get_active_pick_slots(pick_slots)

        print(f"[PickChampionStage] lit_bars_calc = {self.app_state.lit_bars_calc}")
        print(f"[PickChampionStage] 검사할 슬롯 = {[idx + 1 for idx, _ in active_pick_slots]}")

        current_champions = list(getattr(self.app_state, "pick_champions", []))

        while len(current_champions) < len(pick_slots):
            current_champions.append(None)

        for roi_idx, slot in active_pick_slots:
            roi = self.roi_extractor.extract(frame, slot)

            if roi is None:
                print(f"[PickChampionStage] roi is None: slot={roi_idx + 1}")
                current_champions[roi_idx] = None
                continue

            cv2.imwrite(str(roi_dir / f"{call_idx}_{roi_idx}.png"), roi)

            champ_name = self.champion_detector.detect(roi, stage_config)

            last_debug = getattr(self.champion_detector, "last_debug", None)

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

            current_champions[roi_idx] = champ_name

        print(f"[PickChampionStage] 현재 챔피언 = {current_champions}")

        self.app_state.pick_champion_stage_call_count += 1

        if current_champions != self.app_state.pick_champions:
            print("[PickChampionStage] 변화 감지됨")
            print(f"[PickChampionStage] 이전 = {self.app_state.pick_champions}")

            self.app_state.pick_champions = current_champions
            return True

        print("[PickChampionStage] 변화 없음")
        return False