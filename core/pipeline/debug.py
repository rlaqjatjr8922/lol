from pathlib import Path
import shutil
import cv2
import numpy as np


class debug:
    def __init__(self, app_state):
        self.app_state = app_state

        self.project_root = Path(__file__).resolve().parents[2]
        self.base_dir = self.project_root / "debug"

        self._reset_debug_dir()
        self._create_debug_structure()

    def _reset_debug_dir(self):
        if self.base_dir.exists():
            shutil.rmtree(self.base_dir)
            print("[Debug] debug 폴더 삭제")

        self.base_dir.mkdir(parents=True, exist_ok=True)
        print(f"[Debug] debug 폴더 생성: {self.base_dir}")

    def _create_debug_structure(self):
        structure = {
            "stage_0": ["TextStage"],
            "stage_1": ["TextStage", "BanChampionStage"],
            "stage_2": ["TextStage", "BanChampionStage", "StickStage"],
        }

        sub_dirs = ["original", "roi", "processed", "result"]

        for stage_name, stage_list in structure.items():
            for pipeline_stage in stage_list:
                stage_path = self.base_dir / stage_name / pipeline_stage
                for sub_dir in sub_dirs:
                    (stage_path / sub_dir).mkdir(parents=True, exist_ok=True)

        print("[Debug] 디버그 폴더 구조 생성 완료")

    def save(self):
        print("[Debug] 저장 시작")

        save_index = self._get_save_index()
        print(f"[Debug] 현재 save_index = {save_index}")

        for stage_name, data in self.app_state.debug.items():
            print(f"[Debug] 저장 대상 stage_name = {stage_name}")

            if data["original"] is None:
                print(f"[Debug] {stage_name} original 없음 -> 저장 스킵")
                continue

            stage_idx = self._resolve_stage_index(data)
            stage_root = self.base_dir / f"stage_{stage_idx}"

            print(f"[Debug] {stage_name} 저장 stage_root = {stage_root}")

            self._save_stage(stage_root, stage_name, data, save_index)
            self._clear_stage(data)

        print("[Debug] 저장 완료")

    def _resolve_stage_index(self, data):
        if len(data["processed"]) > 0:
            stage_idx = self.app_state.stage
        else:
            stage_idx = self.app_state.stage - 1

        if stage_idx < 0:
            stage_idx = 0

        return stage_idx

    def _get_save_index(self):
        if not hasattr(self.app_state, "debug_save_index"):
            self.app_state.debug_save_index = 0

        current_index = self.app_state.debug_save_index
        self.app_state.debug_save_index += 1
        return current_index

    def _save_stage(self, stage_root, stage_name, data, save_index):
        stage_dir = stage_root / stage_name

        original_dir = stage_dir / "original"
        roi_dir = stage_dir / "roi"
        processed_dir = stage_dir / "processed"
        result_dir = stage_dir / "result"

        original_dir.mkdir(parents=True, exist_ok=True)
        roi_dir.mkdir(parents=True, exist_ok=True)
        processed_dir.mkdir(parents=True, exist_ok=True)
        result_dir.mkdir(parents=True, exist_ok=True)

        self._write_image(original_dir / f"frame_{save_index}.png", data["original"])

        for i, roi_img in enumerate(data["roi"]):
            self._write_image(roi_dir / f"roi_{save_index}_{i}.png", roi_img)

        for i, processed_img in enumerate(data["processed"]):
            self._write_image(processed_dir / f"processed_{save_index}_{i}.png", processed_img)

        self._save_result(stage_name, result_dir, data["result"], save_index)

    def _save_result(self, stage_name, result_dir, results, save_index):
        if stage_name == "TextStage":
            self._save_text_stage_result(result_dir, results, save_index)
        elif stage_name == "BanChampionStage":
            self._save_ban_champion_stage_result(result_dir, results, save_index)
        elif stage_name == "StickStage":
            self._save_stick_stage_result(result_dir, results, save_index)
        else:
            result_path = result_dir / f"result_{save_index}.txt"
            with open(result_path, "w", encoding="utf-8") as f:
                for item in results:
                    f.write(f"{item}\n")
            print(f"[Debug] 저장 성공: {result_path}")

    def _save_text_stage_result(self, result_dir, results, save_index):
        for i, result in enumerate(results):
            if not isinstance(result, (list, tuple)):
                print(f"[Debug] TextStage result 스킵: list/tuple 아님 -> {type(result)}")
                continue

            if len(result) != 3:
                print(f"[Debug] TextStage result 스킵: 길이 3 아님 -> {len(result)}")
                continue

            img1, img2, score = result
            self._save_result_image(result_dir, save_index, i, img1, img2, score)

    def _save_ban_champion_stage_result(self, result_dir, results, save_index):
        result_path = result_dir / f"result_{save_index}.txt"

        with open(result_path, "w", encoding="utf-8") as f:
            for i, champ_name in enumerate(results):
                f.write(f"{i}: {champ_name}\n")

        print(f"[Debug] 저장 성공: {result_path}")

    def _save_stick_stage_result(self, result_dir, results, save_index):
        result_path = result_dir / f"result_{save_index}.txt"

        with open(result_path, "w", encoding="utf-8") as f:
            for i, item in enumerate(results):
                f.write(f"{i}: {item}\n")

        print(f"[Debug] 저장 성공: {result_path}")

    def _save_result_image(self, result_dir, save_index, index, img1, img2, score):
        if img1 is None or img2 is None:
            print(f"[Debug] result_{save_index}_{index} 저장 실패: img1 또는 img2 가 None")
            return

        img1 = self._ensure_color(img1)
        img2 = self._ensure_color(img2)

        target_height = max(img1.shape[0], img2.shape[0])

        img1 = self._resize_to_height(img1, target_height)
        img2 = self._resize_to_height(img2, target_height)

        combined = np.hstack((img1, img2))

        text_area = np.zeros((60, combined.shape[1], 3), dtype=np.uint8)

        try:
            score_text = f"score: {float(score):.4f}"
        except Exception:
            score_text = f"score: {score}"

        cv2.putText(
            text_area,
            score_text,
            (10, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
            cv2.LINE_AA
        )

        final_image = np.vstack((combined, text_area))

        self._write_image(result_dir / f"result_{save_index}_{index}.png", final_image)

    def _resize_to_height(self, img, target_height):
        h, w = img.shape[:2]

        if h == 0 or w == 0:
            return img

        scale = target_height / h
        new_width = int(w * scale)

        if new_width <= 0:
            new_width = 1

        return cv2.resize(img, (new_width, target_height))

    def _ensure_color(self, img):
        if len(img.shape) == 2:
            return cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

        if len(img.shape) == 3 and img.shape[2] == 1:
            return cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

        return img

    def _write_image(self, path, img):
        if img is None:
            print(f"[Debug] 저장 실패: {path} / img is None")
            return

        if not isinstance(img, np.ndarray):
            print(f"[Debug] 저장 실패: {path} / ndarray 아님: {type(img)}")
            return

        if img.size == 0:
            print(f"[Debug] 저장 실패: {path} / 빈 이미지")
            return

        if img.dtype != np.uint8:
            img = np.clip(img, 0, 255).astype(np.uint8)

        success = cv2.imwrite(str(path), img)

        if success:
            print(f"[Debug] 저장 성공: {path}")
        else:
            print(f"[Debug] 저장 실패: {path}")

    def _clear_stage(self, data):
        data["original"] = None
        data["roi"].clear()
        data["processed"].clear()
        data["result"].clear()