import json
import os
from pathlib import Path

import cv2

from core.vision.roi_extractor import ROIExtractor
from core.vision.text_template_checker import TextTemplateChecker
from core.vision.stick_checker import StickChecker
from core.vision.champion_image_detector import ChampionImageDetector
from core.gpt.prompt_builder import run_ban


class DetectStage:
    def __init__(self, stage_key, config, roi_extractor, checker, pipeline):
        self.stage_key = stage_key
        self.config = config
        self.roi_extractor = roi_extractor
        self.checker = checker
        self.pipeline = pipeline

    def _clean_template_name(self, template_name):
        if not template_name:
            return None
        return os.path.basename(template_name)

    def _xywh_to_xyxy_ratio(self, roi_box):
        if roi_box is None:
            return None

        if len(roi_box) != 4:
            return None

        x, y, w, h = roi_box
        x1 = x
        y1 = y
        x2 = x + w
        y2 = y + h
        return [x1, y1, x2, y2]

    def run(self, app_state, screen_source):
        print(f"[DetectStage {self.stage_key}] 시작")

        stage = self.config["stages"][self.stage_key]

        matched_template_path = None
        matched_template_name = None
        matched_score = -1.0

        while True:
            frame = screen_source.capture()

            if frame is None:
                print(f"[DetectStage {self.stage_key}] frame 없음 -> 재시도")
                continue

            app_state.current_frame = frame

            # -------------------------
            # stage 2 : StickChecker
            # -------------------------
            if self.stage_key == "2":
                ally_roi_box_xywh = stage.get("ally_turn_bar_roi")
                enemy_roi_box_xywh = stage.get("enemy_turn_bar_roi")

                print(f"[DetectStage {self.stage_key}] stage = {stage}")
                print(f"[DetectStage {self.stage_key}] ally_turn_bar_roi(x,y,w,h) = {ally_roi_box_xywh}")
                print(f"[DetectStage {self.stage_key}] enemy_turn_bar_roi(x,y,w,h) = {enemy_roi_box_xywh}")

                if ally_roi_box_xywh is None:
                    print(f"[DetectStage {self.stage_key}] ally_turn_bar_roi 없음")
                    return False

                if enemy_roi_box_xywh is None:
                    print(f"[DetectStage {self.stage_key}] enemy_turn_bar_roi 없음")
                    return False

                ally_roi_box = self._xywh_to_xyxy_ratio(ally_roi_box_xywh)
                enemy_roi_box = self._xywh_to_xyxy_ratio(enemy_roi_box_xywh)

                print(f"[DetectStage {self.stage_key}] ally_turn_bar_roi(x1,y1,x2,y2) = {ally_roi_box}")
                print(f"[DetectStage {self.stage_key}] enemy_turn_bar_roi(x1,y1,x2,y2) = {enemy_roi_box}")

                if ally_roi_box is None:
                    print(f"[DetectStage {self.stage_key}] ally roi 변환 실패")
                    return False

                if enemy_roi_box is None:
                    print(f"[DetectStage {self.stage_key}] enemy roi 변환 실패")
                    return False

                ally_roi = self.roi_extractor.extract(frame, ally_roi_box)
                enemy_roi = self.roi_extractor.extract(frame, enemy_roi_box)

                if ally_roi is None:
                    print(f"[DetectStage {self.stage_key}] ally_roi 추출 실패")
                    return False

                if enemy_roi is None:
                    print(f"[DetectStage {self.stage_key}] enemy_roi 추출 실패")
                    return False

                # stage 2는 항상 저장
                self.pipeline.save_original("2", frame)
                self.pipeline.save_roi("2", ally_roi, "ally")
                self.pipeline.save_roi("2", enemy_roi, "enemy")

                lit_bars = self.checker.check(
                    ally_roi,
                    enemy_roi,
                    ["blue", "yellow", "red"]
                )

                print(f"[DetectStage {self.stage_key}] lit_bars = {lit_bars}")

                if not lit_bars:
                    self.pipeline.save_result_text(
                        "2",
                        "lit_bars=[]\nlast_info={}\n"
                    )
                    print(f"[DetectStage {self.stage_key}] 막대기 감지 안됨 -> 종료")
                    return False

                ally_detected, enemy_detected = self.pipeline.detect_picked_champions(
                    frame,
                    lit_bars,
                    stage
                )

                app_state.ally_detected_picks = ally_detected
                app_state.enemy_detected_picks = enemy_detected
                app_state.lit_bars = sorted(list(lit_bars))

                print(f"[DetectStage {self.stage_key}] ally_detected_picks = {ally_detected}")
                print(f"[DetectStage {self.stage_key}] enemy_detected_picks = {enemy_detected}")

                self.pipeline.save_result_text(
                    "2",
                    (
                        f"lit_bars={sorted(list(lit_bars))}\n"
                        f"ally_detected_picks={ally_detected}\n"
                        f"enemy_detected_picks={enemy_detected}\n"
                        f"last_info={getattr(self.checker, 'last_info', None)}\n"
                    )
                )

                matched_template_path = "turn_detected"
                matched_template_name = "turn_detected"
                matched_score = float(len(lit_bars))
                result = True

            # -------------------------
            # stage 0, 1 : TextTemplateChecker
            # -------------------------
            else:
                roi_box = stage.get("writing")
                template_paths = stage.get("template_path", [])

                roi = self.roi_extractor.extract(frame, roi_box)
                if roi is None:
                    print(f"[DetectStage {self.stage_key}] roi 추출 실패")
                    continue

                # 원본 / 잘린 이미지 항상 저장
                self.pipeline.save_original(self.stage_key, frame)
                self.pipeline.save_roi(self.stage_key, roi, "roi")

                result, template_name, score = self.checker.check(
                    roi,
                    template_paths
                )

                debug_info = getattr(self.checker, "last_debug", None)

                # 전처리 이미지 항상 저장
                if debug_info:
                    self.pipeline.save_processed(
                        self.stage_key,
                        debug_info.get("processed_roi")
                    )

                # 가장 비슷한 이미지는 참일 때만 저장
                if result and debug_info:
                    self.pipeline.save_best_match(
                        self.stage_key,
                        debug_info.get("best_template_image")
                    )

                print(f"[DetectStage {self.stage_key}] roi: {roi_box} -> {result}")
                print(f"[DetectStage {self.stage_key}] matched_template_path: {template_name}")
                print(f"[DetectStage {self.stage_key}] matched_score: {score}")

                if template_name is not None:
                    matched_template_path = template_name
                    matched_template_name = self._clean_template_name(template_name)
                    matched_score = score

            if result:
                print(f"[DetectStage {self.stage_key}] ✅ 조건 만족")
                print(f"[DetectStage {self.stage_key}] cleaned_name: {matched_template_name}")

                app_state.stage_results[self.stage_key] = {
                    "matched_template_path": matched_template_path,
                    "matched_template_name": matched_template_name,
                    "matched_score": matched_score,
                }

                if self.stage_key == "0":
                    app_state.matched_template_name = matched_template_name
                    app_state.matched_template_score = matched_score

                if self.stage_key == "2" and getattr(self.checker, "last_info", None):
                    app_state.turn_info = self.checker.last_info
                    app_state.pick_turn_team = self.checker.last_info.get("pick_turn_team")
                    app_state.pick_order = self.checker.last_info.get("pick_order")
                    app_state.is_my_turn = self.checker.last_info.get("is_my_turn", False)

                    print(f"[DetectStage {self.stage_key}] pick_turn_team = {app_state.pick_turn_team}")
                    print(f"[DetectStage {self.stage_key}] pick_order = {app_state.pick_order}")
                    print(f"[DetectStage {self.stage_key}] is_my_turn = {app_state.is_my_turn}")

                return True


class GPTStage:
    def __init__(self, stage_name="ban_gpt"):
        self.stage_name = stage_name

    def run(self, app_state, screen_source):
        print(f"[GPTStage {self.stage_name}] 시작")

        try:
            print("[GPTStage] matched_template_name =", getattr(app_state, "matched_template_name", None))
            print("[GPTStage] matched_template_score =", getattr(app_state, "matched_template_score", None))

            answer = run_ban(app_state)
            app_state.gpt_answer = answer

            print(f"[GPTStage {self.stage_name}] 답변:")
            print(answer)

            return True

        except Exception as e:
            print(f"[GPTStage {self.stage_name}] 실패:", e)
            return False


class PregamePipeline:
    def __init__(self, app_state, screen_source):
        self.app_state = app_state
        self.screen_source = screen_source

        self.original_count = 0
        self.roi_count = 0
        self.processed_count = 0
        self.best_match_count = 0
        self.result_count = 0

        base_dir = Path(__file__).resolve().parents[2]

        self.config_path = base_dir / "data" / "config.json"
        print("[PregamePipeline] config_path =", self.config_path)
        print("[PregamePipeline] config_exists =", self.config_path.exists())

        with open(self.config_path, "r", encoding="utf-8") as f:
            self.config = json.load(f)

        self.setting_path = base_dir / "data" / "setting.json"
        print("[PregamePipeline] setting_path =", self.setting_path)
        print("[PregamePipeline] setting_exists =", self.setting_path.exists())

        if self.setting_path.exists():
            try:
                with open(self.setting_path, "r", encoding="utf-8") as f:
                    setting = json.load(f)
            except Exception as e:
                print("[PregamePipeline] setting.json 로드 실패 -> 기본값 사용:", e)
                setting = {}
        else:
            setting = {}

        self.debug_enabled = setting.get("debug", True)
        print("[PregamePipeline] debug_enabled =", self.debug_enabled)

        if not hasattr(self.app_state, "stage_results"):
            self.app_state.stage_results = {}

        if not hasattr(self.app_state, "turn_info"):
            self.app_state.turn_info = {}

        if not hasattr(self.app_state, "pick_turn_team"):
            self.app_state.pick_turn_team = None

        if not hasattr(self.app_state, "pick_order"):
            self.app_state.pick_order = None

        if not hasattr(self.app_state, "is_my_turn"):
            self.app_state.is_my_turn = False

        if not hasattr(self.app_state, "matched_template_name"):
            self.app_state.matched_template_name = None

        if not hasattr(self.app_state, "matched_template_score"):
            self.app_state.matched_template_score = None

        if not hasattr(self.app_state, "gpt_answer"):
            self.app_state.gpt_answer = None

        if not hasattr(self.app_state, "ally_detected_picks"):
            self.app_state.ally_detected_picks = []

        if not hasattr(self.app_state, "enemy_detected_picks"):
            self.app_state.enemy_detected_picks = []

        if not hasattr(self.app_state, "lit_bars"):
            self.app_state.lit_bars = []

        self.app_state.debug_enabled = self.debug_enabled
        self.app_state.debug_dir = str(base_dir / "debug")

        if self.debug_enabled:
            debug_dir = Path(self.app_state.debug_dir)
            debug_dir.mkdir(parents=True, exist_ok=True)
            print("[PregamePipeline] debug 폴더 생성")
        else:
            print("[PregamePipeline] debug OFF")

        # 디버그 저장은 pipeline에서만
        self.roi_extractor = ROIExtractor()
        self.text_checker = TextTemplateChecker()
        self.stick_checker = StickChecker(debug=False, slot_count=5)
        self.champion_image_detector = ChampionImageDetector()

        self.stages = [
            DetectStage("0", self.config, self.roi_extractor, self.text_checker, self),
            GPTStage("ban_gpt"),
            DetectStage("1", self.config, self.roi_extractor, self.text_checker, self),
            DetectStage("2", self.config, self.roi_extractor, self.stick_checker, self),
        ]

    def _save_debug_image(self, sub_dir, filename, image):
        if not self.debug_enabled:
            return

        if image is None:
            return

        save_dir = Path(self.app_state.debug_dir) / sub_dir
        save_dir.mkdir(parents=True, exist_ok=True)

        save_path = save_dir / filename

        try:
            ext = save_path.suffix
            ok, buf = cv2.imencode(ext, image)

            if not ok:
                print(f"[PregamePipeline][DEBUG] imencode 실패: {save_path}")
                return

            buf.tofile(str(save_path))
            print(f"[PregamePipeline][DEBUG] 저장: {save_path}")

        except Exception as e:
            print(f"[PregamePipeline][DEBUG] 저장 오류: {e}")

    def save_original(self, stage_key, image):
        filename = f"{self.original_count:04d}.png"
        self._save_debug_image(f"{stage_key}/original", filename, image)
        self.original_count += 1

    def save_roi(self, stage_key, image, prefix="roi"):
        filename = f"{prefix}_{self.roi_count:04d}.png"
        self._save_debug_image(f"{stage_key}/roi", filename, image)
        self.roi_count += 1

    def save_processed(self, stage_key, image):
        filename = f"{self.processed_count:04d}.png"
        self._save_debug_image(f"{stage_key}/processed", filename, image)
        self.processed_count += 1

    def save_best_match(self, stage_key, image):
        filename = f"{self.best_match_count:04d}.png"
        self._save_debug_image(f"{stage_key}/best_match", filename, image)
        self.best_match_count += 1

    def save_result_text(self, stage_key, text):
        if not self.debug_enabled:
            return

        save_dir = Path(self.app_state.debug_dir) / str(stage_key) / "result"
        save_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{self.result_count:04d}.txt"
        save_path = save_dir / filename

        try:
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(text)

            print(f"[PregamePipeline][DEBUG] 결과 저장: {save_path}")
            self.result_count += 1

        except Exception as e:
            print(f"[PregamePipeline][DEBUG] 결과 저장 오류: {e}")

    def _xywh_to_xyxy_ratio(self, roi_box):
        if roi_box is None or len(roi_box) != 4:
            return None

        x, y, w, h = roi_box
        return [x, y, x + w, y + h]

    def get_selected_pick_rois(self, lit_bars, stage_config):
        ally_picks = stage_config.get("ally_picks", [])
        enemy_picks = stage_config.get("enemy_picks", [])

        if not lit_bars:
            return [], []

        min_bar = min(lit_bars)

        ally_result = []
        enemy_result = []

        # 규칙:
        # 가장 작은 불 켜진 숫자보다 앞에 있는 슬롯 전체 사용
        # 아군: 1~5
        # 적군: 6~10
        for i in range(1, min(min_bar, 6)):
            idx = i - 1
            if idx < len(ally_picks):
                ally_result.append(ally_picks[idx])

        for i in range(6, min(min_bar, 11)):
            idx = i - 6
            if idx < len(enemy_picks):
                enemy_result.append(enemy_picks[idx])

        return ally_result, enemy_result

    def detect_picked_champions(self, frame, lit_bars, stage_config):
        ally_pick_boxes, enemy_pick_boxes = self.get_selected_pick_rois(lit_bars, stage_config)

        ally_results = []
        enemy_results = []

        for i, roi_box_xywh in enumerate(ally_pick_boxes):
            roi_box_xyxy = self._xywh_to_xyxy_ratio(roi_box_xywh)
            roi = self.roi_extractor.extract(frame, roi_box_xyxy)

            self.save_roi("2", roi, f"ally_pick_{i+1}")

            champion_name = self.champion_image_detector.detect(roi)

            ally_results.append({
                "slot": i + 1,
                "roi_box": roi_box_xywh,
                "champion": champion_name,
            })

        for i, roi_box_xywh in enumerate(enemy_pick_boxes):
            roi_box_xyxy = self._xywh_to_xyxy_ratio(roi_box_xywh)
            roi = self.roi_extractor.extract(frame, roi_box_xyxy)

            self.save_roi("2", roi, f"enemy_pick_{i+1}")

            champion_name = self.champion_image_detector.detect(roi)

            enemy_results.append({
                "slot": i + 1,
                "roi_box": roi_box_xywh,
                "champion": champion_name,
            })

        return ally_results, enemy_results

    def run(self):
        print("[PregamePipeline] run 시작")

        for i, stage in enumerate(self.stages):
            print(f"[PregamePipeline] step {i} -> {stage.__class__.__name__}")

            result = stage.run(self.app_state, self.screen_source)

            if not result:
                print(f"[PregamePipeline] ❌ step {i} 실패 -> 종료")
                return False

        print("[PregamePipeline] ✅ 전체 완료")
        return True