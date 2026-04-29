import cv2
from pathlib import Path


class PickChampionStage:
    def __init__(self, app_state, screen_source, roi_extractor, champion_detector):
        self.app_state = app_state
        self.screen_source = screen_source
        self.roi_extractor = roi_extractor
        self.champion_detector = champion_detector

    def _get_slots_from_lit_bars_calc(self, stage_config):
        ally_picks = stage_config.get("ally_picks", [])
        enemy_picks = stage_config.get("enemy_picks", [])

        lit_bars_calc = getattr(self.app_state, "lit_bars_calc", [(), ()])

        ally_active_slots = lit_bars_calc[0] if len(lit_bars_calc) > 0 else ()
        enemy_active_slots = lit_bars_calc[1] if len(lit_bars_calc) > 1 else ()

        result = []

        for slot_no in ally_active_slots:
            idx = slot_no - 1
            if 0 <= idx < len(ally_picks):
                result.append(("ally", idx, ally_picks[idx]))

        for slot_no in enemy_active_slots:
            idx = slot_no - 1
            if 0 <= idx < len(enemy_picks):
                result.append(("enemy", idx, enemy_picks[idx]))

        return result

    def _draw_slot_rect(self, image, slot, label):
        h, w = image.shape[:2]

        x_ratio, y_ratio, width_ratio, height_ratio = slot

        x1 = int(x_ratio * w)
        y1 = int(y_ratio * h)
        x2 = int((x_ratio + width_ratio) * w)
        y2 = int((y_ratio + height_ratio) * h)

        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)

        cv2.putText(
            image,
            label,
            (x1, max(20, y1 - 5)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2
        )

    def _save_pick_ui_debug(self, base_dir, result_dir, call_idx, active_slots):
        pick_ui_path = base_dir / "assets" / "ui" / "pick.png"

        if not pick_ui_path.exists():
            print(f"[PickChampionStage] pick.png 없음: {pick_ui_path}")
            return

        ui_img = cv2.imread(str(pick_ui_path), cv2.IMREAD_COLOR)

        if ui_img is None:
            print(f"[PickChampionStage] pick.png 읽기 실패: {pick_ui_path}")
            return

        for team, idx, slot in active_slots:
            label = f"{team}_{idx + 1}"
            self._draw_slot_rect(ui_img, slot, label)

        save_path = result_dir / f"{call_idx}_pick_ui_slots.png"
        cv2.imwrite(str(save_path), ui_img)

        print(f"[PickChampionStage] pick UI 검사 이미지 저장: {save_path}")

    def _make_empty_pick_champions(self, ally_count, enemy_count):
        return {
            "ally": [None] * ally_count,
            "enemy": [None] * enemy_count,
        }

    def _normalize_pick_champions(self, pick_champions, ally_count, enemy_count):
        if not isinstance(pick_champions, dict):
            pick_champions = self._make_empty_pick_champions(ally_count, enemy_count)

        if "ally" not in pick_champions or not isinstance(pick_champions["ally"], list):
            pick_champions["ally"] = [None] * ally_count

        if "enemy" not in pick_champions or not isinstance(pick_champions["enemy"], list):
            pick_champions["enemy"] = [None] * enemy_count

        while len(pick_champions["ally"]) < ally_count:
            pick_champions["ally"].append(None)

        while len(pick_champions["enemy"]) < enemy_count:
            pick_champions["enemy"].append(None)

        if len(pick_champions["ally"]) > ally_count:
            pick_champions["ally"] = pick_champions["ally"][:ally_count]

        if len(pick_champions["enemy"]) > enemy_count:
            pick_champions["enemy"] = pick_champions["enemy"][:enemy_count]

        return pick_champions

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

        active_slots = self._get_slots_from_lit_bars_calc(stage_config)

        print(f"[PickChampionStage] lit_bars_calc = {self.app_state.lit_bars_calc}")
        print(f"[PickChampionStage] 검사 슬롯 = {[(team, idx + 1) for team, idx, _ in active_slots]}")

        self._save_pick_ui_debug(base_dir, result_dir, call_idx, active_slots)

        ally_count = len(stage_config.get("ally_picks", []))
        enemy_count = len(stage_config.get("enemy_picks", []))

        old_pick_champions = getattr(self.app_state, "pick_champions", None)
        pick_champions = self._normalize_pick_champions(
            old_pick_champions,
            ally_count,
            enemy_count
        )

        for team, idx, slot in active_slots:
            roi = self.roi_extractor.extract(frame, slot)

            if roi is None:
                print(f"[PickChampionStage] roi is None: team={team}, slot={idx + 1}")
                pick_champions[team][idx] = None
                continue

            cv2.imwrite(str(roi_dir / f"{call_idx}_{team}_{idx}.png"), roi)

            champ_name, debug_images = self.champion_detector.detect(roi, stage_config)

            if debug_images is None:
                debug_images = {}

            score = debug_images.get("best_score", -1.0)
            if score is None:
                score = -1.0

            print(
                f"[PickChampionStage] team={team}, "
                f"slot={idx + 1}, "
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
                        str(processed_dir / f"{call_idx}_{team}_{idx}_{save_idx}.png"),
                        img
                    )
                    save_idx += 1

            with open(result_dir / f"{call_idx}_{team}_{idx}.txt", "w", encoding="utf-8") as f:
                f.write(f"team: {team}\n")
                f.write(f"slot_index: {idx}\n")
                f.write(f"slot_number: {idx + 1}\n")
                f.write(f"detected_name: {champ_name}\n")
                f.write(f"best_name: {debug_images.get('best_name')}\n")
                f.write(f"best_score: {score}\n")

                top_candidates = debug_images.get("top_candidates", [])
                f.write("\ntop_candidates:\n")

                for candidate in top_candidates:
                    f.write(str(candidate) + "\n")

            pick_champions[team][idx] = champ_name

        print(f"[PickChampionStage] 현재 챔피언 = {pick_champions}")

        self.app_state.pick_champion_stage_call_count += 1

        if pick_champions != self.app_state.pick_champions:
            print("[PickChampionStage] 변화 감지됨")
            print(f"[PickChampionStage] 이전 = {self.app_state.pick_champions}")

            self.app_state.pick_champions = pick_champions
            return True

        print("[PickChampionStage] 변화 없음")
        return False