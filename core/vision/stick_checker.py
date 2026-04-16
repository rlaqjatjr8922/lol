import cv2
import numpy as np


class StickChecker:
    def __init__(self):
        self.last_debug = None
        self.last_info = None

    def _init_debug(self):
        self.last_debug = {
            "ally_slot_results": [],
            "enemy_slot_results": [],
            "summary": {},
        }

    def _get_hsv_ranges(self, stage_config):
        default_ranges = {
            "blue": [
                ((90, 80, 80), (130, 255, 255)),
            ],
            "yellow": [
                ((15, 80, 80), (40, 255, 255)),
            ],
            "red": [
                ((0, 80, 80), (10, 255, 255)),
                ((170, 80, 80), (180, 255, 255)),
            ],
        }
        return stage_config.get("hsv_ranges", default_ranges)

    def _get_color_thresholds(self, stage_config):
        default_thresholds = {
            "blue": 0.08,
            "yellow": 0.08,
            "red": 0.08,
        }
        return stage_config.get("color_thresholds", default_thresholds)

    def _get_slot_count(self, stage_config):
        return int(stage_config.get("slot_count", 5))

    def _get_slot_crop_ratio(self, stage_config):
        """
        각 슬롯 안에서 실제 검사할 가로 비율.
        너무 넓게 보면 슬롯 경계가 섞일 수 있어서 중앙 부분만 사용.
        """
        return float(stage_config.get("slot_crop_ratio", 0.72))

    def _get_vertical_crop_ratio(self, stage_config):
        """
        상하 여백 제거용 비율.
        """
        return float(stage_config.get("vertical_crop_ratio", 0.80))

    def _build_mask(self, hsv_img, color_name, hsv_ranges):
        mask = None
        for lower, upper in hsv_ranges.get(color_name, []):
            lower_np = np.array(lower, dtype=np.uint8)
            upper_np = np.array(upper, dtype=np.uint8)
            partial = cv2.inRange(hsv_img, lower_np, upper_np)
            if mask is None:
                mask = partial
            else:
                mask = cv2.bitwise_or(mask, partial)

        if mask is None:
            mask = np.zeros(hsv_img.shape[:2], dtype=np.uint8)

        return mask

    def _clean_mask(self, mask):
        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        return mask

    def _split_slots(self, roi, slot_count, slot_crop_ratio, vertical_crop_ratio):
        h, w = roi.shape[:2]
        slot_width = w / slot_count
        slot_imgs = []

        y_margin = int((1.0 - vertical_crop_ratio) * h / 2.0)
        y1 = max(0, y_margin)
        y2 = min(h, h - y_margin)

        for i in range(slot_count):
            x1_full = int(round(i * slot_width))
            x2_full = int(round((i + 1) * slot_width))

            full_width = max(1, x2_full - x1_full)
            inner_width = max(1, int(round(full_width * slot_crop_ratio)))
            x_margin = max(0, (full_width - inner_width) // 2)

            x1 = min(w, max(0, x1_full + x_margin))
            x2 = min(w, max(x1 + 1, x2_full - x_margin))

            slot_img = roi[y1:y2, x1:x2].copy()
            slot_imgs.append((i + 1, slot_img, (x1, y1, x2, y2)))

        return slot_imgs

    def _calc_slot_ratio(self, slot_img, color_name, hsv_ranges):
        if slot_img is None or slot_img.size == 0:
            return 0.0, None

        hsv = cv2.cvtColor(slot_img, cv2.COLOR_BGR2HSV)
        mask = self._build_mask(hsv, color_name, hsv_ranges)
        mask = self._clean_mask(mask)

        total_pixels = mask.shape[0] * mask.shape[1]
        if total_pixels <= 0:
            return 0.0, mask

        lit_pixels = int(np.count_nonzero(mask))
        ratio = lit_pixels / float(total_pixels)
        return ratio, mask

    def _detect_slots_for_color(self, roi, side_name, color_name, stage_config):
        hsv_ranges = self._get_hsv_ranges(stage_config)
        thresholds = self._get_color_thresholds(stage_config)
        slot_count = self._get_slot_count(stage_config)
        slot_crop_ratio = self._get_slot_crop_ratio(stage_config)
        vertical_crop_ratio = self._get_vertical_crop_ratio(stage_config)

        threshold = float(thresholds.get(color_name, 0.08))
        slots = []
        slot_ratios = {}

        split_slots = self._split_slots(
            roi,
            slot_count=slot_count,
            slot_crop_ratio=slot_crop_ratio,
            vertical_crop_ratio=vertical_crop_ratio,
        )

        for slot_no, slot_img, rect in split_slots:
            ratio, mask = self._calc_slot_ratio(slot_img, color_name, hsv_ranges)
            slot_ratios[slot_no] = ratio

            is_active = ratio >= threshold
            if is_active:
                slots.append(slot_no)

            debug_item = {
                "side": side_name,
                "color": color_name,
                "slot": slot_no,
                "ratio": ratio,
                "threshold": threshold,
                "active": is_active,
                "rect": rect,
            }

            if side_name == "ally":
                self.last_debug["ally_slot_results"].append(debug_item)
            else:
                self.last_debug["enemy_slot_results"].append(debug_item)

        return slots, slot_ratios

    def _infer_turn_info(self, blue_slots, yellow_slots, red_slots, ally_active_slots, enemy_active_slots):
        """
        현재 구조 기준:
        - ally 쪽 yellow 있으면 내 차례
        - yellow 없고 red/blue만 있으면 enemy 또는 team 추정은 제한적
        - 최소한 ally/enemy 여부는 추정하고, is_my_turn은 yellow 기준으로 확정
        """
        pick_turn_team = None
        is_my_turn = False

        if yellow_slots:
            pick_turn_team = "ally"
            is_my_turn = True
            return pick_turn_team, is_my_turn

        # ally 쪽에 불은 있는데 yellow는 없으면
        # 우리 팀 차례일 수도 있고 적 차례일 수도 있음.
        # 현재 파이프라인용 최소 추정:
        # 적 쪽 red 진행이 더 많거나 같으면 enemy 쪽 진행 중으로 봄.
        if len(enemy_active_slots) >= len(ally_active_slots) and len(enemy_active_slots) > 0:
            pick_turn_team = "enemy"
            is_my_turn = False
            return pick_turn_team, is_my_turn

        if len(ally_active_slots) > 0:
            pick_turn_team = "ally"
            is_my_turn = False
            return pick_turn_team, is_my_turn

        return None, False

    def _build_pick_order(self, ally_active_slots, enemy_active_slots):
        """
        단순 진행 순서 정보.
        현재 화면만으로 완전한 밴픽 로그를 복원하는 건 한계가 있어서
        활성 슬롯 번호 기준으로 가볍게 정리.
        """
        order = []

        for slot in ally_active_slots:
            order.append(("ally", slot))

        for slot in enemy_active_slots:
            order.append(("enemy", slot))

        order.sort(key=lambda x: x[1])
        return order

    def check(self, ally_roi, enemy_roi, colors=None, stage_config=None):
        if stage_config is None:
            stage_config = {}
        if colors is None:
            colors = ["blue", "yellow", "red"]

        self._init_debug()
        self.last_info = None

        if ally_roi is None or enemy_roi is None:
            self.last_info = {}
            return []

        blue_slots, blue_slot_ratios = [], {}
        yellow_slots, yellow_slot_ratios = [], {}
        red_slots, red_slot_ratios = [], {}

        if "blue" in colors:
            blue_slots, blue_slot_ratios = self._detect_slots_for_color(
                ally_roi,
                side_name="ally",
                color_name="blue",
                stage_config=stage_config,
            )

        if "yellow" in colors:
            yellow_slots, yellow_slot_ratios = self._detect_slots_for_color(
                ally_roi,
                side_name="ally",
                color_name="yellow",
                stage_config=stage_config,
            )

        if "red" in colors:
            red_slots, red_slot_ratios = self._detect_slots_for_color(
                enemy_roi,
                side_name="enemy",
                color_name="red",
                stage_config=stage_config,
            )

        # ally 활성 슬롯은 blue + yellow 합집합
        ally_active_slots = sorted(set(blue_slots) | set(yellow_slots))
        enemy_active_slots = sorted(set(red_slots))

        pick_turn_team, is_my_turn = self._infer_turn_info(
            blue_slots=blue_slots,
            yellow_slots=yellow_slots,
            red_slots=red_slots,
            ally_active_slots=ally_active_slots,
            enemy_active_slots=enemy_active_slots,
        )

        pick_order = self._build_pick_order(
            ally_active_slots=ally_active_slots,
            enemy_active_slots=enemy_active_slots,
        )

        self.last_info = {
            "blue_slots": blue_slots,
            "yellow_slots": yellow_slots,
            "red_slots": red_slots,
            "blue_slot_ratios": blue_slot_ratios,
            "yellow_slot_ratios": yellow_slot_ratios,
            "red_slot_ratios": red_slot_ratios,
            "pick_turn_team": pick_turn_team,   # "ally" / "enemy" / None
            "is_my_turn": is_my_turn,           # True / False
            "ally_active_slots": ally_active_slots,
            "enemy_active_slots": enemy_active_slots,
            "pick_order": pick_order,
        }

        self.last_debug["summary"] = self.last_info.copy()

        # StickStage에서 raw_lit_bars 출력용으로 쓸 수 있게 단순 리스트 반환
        # (slot_index_0_based, color, ratio)
        raw_lit_bars = []

        for slot in blue_slots:
            raw_lit_bars.append((slot - 1, "blue", blue_slot_ratios.get(slot, 0.0)))

        for slot in yellow_slots:
            raw_lit_bars.append((slot - 1, "yellow", yellow_slot_ratios.get(slot, 0.0)))

        for slot in red_slots:
            raw_lit_bars.append((slot - 1, "red", red_slot_ratios.get(slot, 0.0)))

        raw_lit_bars.sort(key=lambda x: (x[0], x[1]))
        return raw_lit_bars