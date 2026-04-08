import os
from pathlib import Path

import cv2
import numpy as np


class StickChecker:
    def __init__(self, debug=False, slot_count=5):
        self.debug = debug
        self.slot_count = slot_count
        self.last_info = {}

        self.turn_slot_centers = [1, 2, 3, 4, 5]

        self.inner_top_ratio = 0.06
        self.inner_bottom_ratio = 0.94
        self.color_ratio_threshold = 0.90

        self.my_pick_slot = 5
        self.ally_hsv_ranges = None
        self.enemy_hsv_ranges = None

        self.debug_dir = None
        if self.debug:
            base_dir = Path(__file__).resolve().parents[2]
            self.debug_dir = base_dir / "debug" / "stick"
            self.debug_dir.mkdir(parents=True, exist_ok=True)

    # =========================
    # 내부 유틸
    # =========================

    def _open_mask(self, mask):
        kernel = np.ones((3, 3), np.uint8)
        return cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

    def _calc_mask_ratio(self, mask):
        total = mask.size
        if total <= 0:
            return 0.0
        return float(np.count_nonzero(mask)) / float(total)

    def _build_slot_ranges(self, height, slot_count):
        """
        잘린 ROI 이미지의 높이를 slot_count개로 균등 분할.
        return: [(slot_idx, y1, y2, center_y), ...]
        """
        ranges = []
        step = height / float(slot_count)

        for i in range(slot_count):
            raw_y1 = int(round(i * step))
            raw_y2 = int(round((i + 1) * step)) - 1

            if i == slot_count - 1:
                raw_y2 = height - 1

            seg_h = max(1, raw_y2 - raw_y1 + 1)

            inner_y1 = raw_y1 + int(round(seg_h * self.inner_top_ratio))
            inner_y2 = raw_y1 + int(round(seg_h * self.inner_bottom_ratio)) - 1

            inner_y1 = max(raw_y1, min(raw_y2, inner_y1))
            inner_y2 = max(inner_y1, min(raw_y2, inner_y2))

            center_y = (raw_y1 + raw_y2) // 2
            ranges.append((i + 1, inner_y1, inner_y2, center_y))

        return ranges

    def _pick_primary_slot(self, active_slots, slot_ratios):
        if not active_slots:
            return None

        best_slot = None
        best_ratio = -1.0

        for s in active_slots:
            r = slot_ratios.get(s, 0.0)
            if r > best_ratio:
                best_ratio = r
                best_slot = s

        return best_slot

    def _slot_to_center_y(self, slot_idx):
        if slot_idx is None:
            return None
        if 1 <= slot_idx <= len(self.turn_slot_centers):
            return self.turn_slot_centers[slot_idx - 1]
        return None

    def normalize_slots(self, slots):
        return tuple(sorted(set(slots)))

    # =========================
    # 패턴 판단
    # =========================

    def get_pattern_a_stage(self, slots):
        """
        패턴 A:
          (1,2) -> 0
          (3,4) -> 1
          (5,)  -> 2
          ()    -> 3
        """
        slots = self.normalize_slots(slots)

        if slots == (1, 2):
            return 0
        if slots == (3, 4):
            return 1
        if slots == (5,):
            return 2
        if slots == ():
            return 3
        return None

    def get_pattern_b_stage(self, slots):
        """
        패턴 B:
          (1,)   -> 0
          (2,3)  -> 1
          (4,5)  -> 2
          ()     -> 3
        """
        slots = self.normalize_slots(slots)

        if slots == (1,):
            return 0
        if slots == (2, 3):
            return 1
        if slots == (4, 5):
            return 2
        if slots == ():
            return 3
        return None

    def detect_team_pattern(self, slots):
        """
        return:
          ("A", stage) / ("B", stage) / (None, stage_or_None)

        () 는 A/B 둘 다 가능하므로 단독으로는 패턴 확정 불가
        """
        slots = self.normalize_slots(slots)
        a_stage = self.get_pattern_a_stage(slots)
        b_stage = self.get_pattern_b_stage(slots)

        if slots == ():
            return (None, 3)

        if a_stage is not None and b_stage is None:
            return ("A", a_stage)

        if b_stage is not None and a_stage is None:
            return ("B", b_stage)

        return (None, None)

    def infer_patterns(self, ally_slots, enemy_slots):
        ally_slots = self.normalize_slots(ally_slots)
        enemy_slots = self.normalize_slots(enemy_slots)

        ally_pattern, ally_stage = self.detect_team_pattern(ally_slots)
        enemy_pattern, enemy_stage = self.detect_team_pattern(enemy_slots)

        if ally_pattern == "A" and enemy_pattern is None:
            enemy_pattern = "B"
            enemy_stage = self.get_pattern_b_stage(enemy_slots)
        elif ally_pattern == "B" and enemy_pattern is None:
            enemy_pattern = "A"
            enemy_stage = self.get_pattern_a_stage(enemy_slots)

        if enemy_pattern == "A" and ally_pattern is None:
            ally_pattern = "B"
            ally_stage = self.get_pattern_b_stage(ally_slots)
        elif enemy_pattern == "B" and ally_pattern is None:
            ally_pattern = "A"
            ally_stage = self.get_pattern_a_stage(ally_slots)

        return {
            "ally_pattern": ally_pattern,
            "ally_stage": ally_stage,
            "enemy_pattern": enemy_pattern,
            "enemy_stage": enemy_stage,
        }

    def detect_pick_turn_from_patterns(self, ally_slots, enemy_slots):
        """
        규칙:
        패턴 순서는 항상 B -> A -> B -> A -> B -> A

        따라서
        - B단계 == A단계     -> 패턴 B 쪽 차례
        - B단계 == A단계 + 1 -> 패턴 A 쪽 차례
        """
        info = self.infer_patterns(ally_slots, enemy_slots)

        ally_pattern = info["ally_pattern"]
        ally_stage = info["ally_stage"]
        enemy_pattern = info["enemy_pattern"]
        enemy_stage = info["enemy_stage"]

        if ally_pattern is None or enemy_pattern is None:
            return {
                **info,
                "pick_turn_team": None,
                "is_ally_pick_turn": False,
                "is_enemy_pick_turn": False,
            }

        if ally_pattern == "A":
            a_stage = ally_stage
            b_stage = enemy_stage
            a_owner = "ally"
            b_owner = "enemy"
        else:
            a_stage = enemy_stage
            b_stage = ally_stage
            a_owner = "enemy"
            b_owner = "ally"

        pick_turn_team = None

        if b_stage == a_stage:
            pick_turn_team = b_owner
        elif b_stage == a_stage + 1:
            pick_turn_team = a_owner

        return {
            **info,
            "pick_turn_team": pick_turn_team,
            "is_ally_pick_turn": pick_turn_team == "ally",
            "is_enemy_pick_turn": pick_turn_team == "enemy",
        }

    # =========================
    # 색 파싱
    # =========================

    def _parse_hsv_ranges(self, hsv_range_list):
        if not hsv_range_list:
            return []

        parsed = []
        for rng in hsv_range_list:
            if not isinstance(rng, (list, tuple)) or len(rng) != 2:
                continue
            lower, upper = rng
            parsed.append(
                (
                    np.array(lower, dtype=np.uint8),
                    np.array(upper, dtype=np.uint8),
                )
            )

        return parsed

    def _resolve_color_ranges(self, colors, ally_hsv_ranges=None, enemy_hsv_ranges=None):
        """
        config의 colors를 받아 HSV 범위 dict로 변환
        기대 예시:
        ["blue", "yellow", "red"]
        """
        result = {}
        parsed_ally = self._parse_hsv_ranges(ally_hsv_ranges)
        parsed_enemy = self._parse_hsv_ranges(enemy_hsv_ranges)

        for c in colors:
            name = str(c).strip().lower()

            if name == "yellow":
                if len(parsed_ally) >= 1:
                    result["yellow"] = [parsed_ally[0]]
                else:
                    result["yellow"] = [
                        (np.array((18, 90, 90), dtype=np.uint8), np.array((40, 255, 255), dtype=np.uint8)),
                    ]
            elif name == "blue":
                if len(parsed_ally) >= 2:
                    result["blue"] = [parsed_ally[1]]
                elif len(parsed_ally) == 1:
                    result["blue"] = [parsed_ally[0]]
                else:
                    result["blue"] = [
                        (np.array((85, 80, 80), dtype=np.uint8), np.array((130, 255, 255), dtype=np.uint8)),
                    ]
            elif name == "red":
                if parsed_enemy:
                    result["red"] = parsed_enemy
                else:
                    result["red"] = [
                        (np.array((0, 140, 140), dtype=np.uint8), np.array((8, 255, 255), dtype=np.uint8)),
                        (np.array((172, 140, 140), dtype=np.uint8), np.array((179, 255, 255), dtype=np.uint8)),
                    ]

        if "blue" not in result:
            result["blue"] = [
                (np.array((85, 80, 80), dtype=np.uint8), np.array((130, 255, 255), dtype=np.uint8)),
            ]
        if "yellow" not in result:
            result["yellow"] = [
                (np.array((18, 90, 90), dtype=np.uint8), np.array((40, 255, 255), dtype=np.uint8)),
            ]
        if "red" not in result:
            result["red"] = [
                (np.array((0, 140, 140), dtype=np.uint8), np.array((8, 255, 255), dtype=np.uint8)),
                (np.array((172, 140, 140), dtype=np.uint8), np.array((179, 255, 255), dtype=np.uint8)),
            ]

        return result

    def _segment_color_presence(self, roi_img, hsv_ranges):
        """
        잘린 ROI 이미지를 self.slot_count 칸으로 나눠서
        각 칸에 색이 threshold 이상 차는지 검사
        """
        if roi_img is None or roi_img.size == 0:
            return {
                "slot_ranges": [],
                "active_slots": [],
                "slot_ratios": {},
            }

        h, _w = roi_img.shape[:2]
        hsv = cv2.cvtColor(roi_img, cv2.COLOR_BGR2HSV)

        slot_ranges = self._build_slot_ranges(h, self.slot_count)

        active_slots = []
        slot_ratios = {}

        for slot_idx, y1, y2, _center_y in slot_ranges:
            patch = hsv[y1:y2 + 1, :]
            if patch.size == 0:
                slot_ratios[slot_idx] = 0.0
                continue

            merged_mask = None
            for lower, upper in hsv_ranges:
                m = cv2.inRange(patch, lower, upper)
                merged_mask = m if merged_mask is None else cv2.bitwise_or(merged_mask, m)

            if merged_mask is None:
                slot_ratios[slot_idx] = 0.0
                continue

            merged_mask = self._open_mask(merged_mask)
            ratio = self._calc_mask_ratio(merged_mask)
            slot_ratios[slot_idx] = ratio

            if ratio >= self.color_ratio_threshold:
                active_slots.append(slot_idx)

        return {
            "slot_ranges": slot_ranges,
            "active_slots": active_slots,
            "slot_ratios": slot_ratios,
        }

    # =========================
    # pick_order 계산
    # =========================

    def _calc_pick_order(self, ally_slot, enemy_slot, pick_turn_team, is_my_turn):
        """
        일단 안전하게:
        - 내 턴이면 ally_slot 사용
        - 적 턴이면 enemy_slot 사용
        - 둘 다 없으면 None
        """
        if is_my_turn:
            if ally_slot is not None:
                return ally_slot
            if self.my_pick_slot is not None:
                return self.my_pick_slot

        if pick_turn_team == "ally":
            if ally_slot is not None:
                return ally_slot
            if self.my_pick_slot is not None:
                return self.my_pick_slot

        if pick_turn_team == "enemy" and enemy_slot is not None:
            return enemy_slot

        return ally_slot if ally_slot is not None else enemy_slot

    # =========================
    # 디버그
    # =========================

    def _save_debug_image(self, name, img):
        if not self.debug or self.debug_dir is None or img is None:
            return

        path = self.debug_dir / name
        cv2.imwrite(str(path), img)

    def _draw_debug_roi(self, roi_img, title, info, side="ally"):
        if roi_img is None or roi_img.size == 0:
            return None

        out = roi_img.copy()
        h, w = out.shape[:2]

        for idx, _y1, _y2, cy in info["slot_ranges"]:
            cv2.line(out, (0, cy), (w - 1, cy), (180, 180, 180), 1)
            cv2.putText(
                out,
                f"S{idx}",
                (max(0, w - 45), min(h - 5, cy + 5)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                (255, 255, 255),
                1,
                cv2.LINE_AA,
            )

        color = (255, 255, 255)
        ratios = info["slot_ratios"]

        for s in info["active_slots"]:
            for idx, _y1, _y2, cy in info["slot_ranges"]:
                if idx == s:
                    if side == "ally_blue":
                        color = (255, 0, 0)
                    elif side == "ally_yellow":
                        color = (0, 255, 255)
                    elif side == "enemy_red":
                        color = (0, 0, 255)

                    ratio = ratios.get(s, 0.0)
                    cv2.line(out, (0, cy), (w - 1, cy), color, 2)
                    cv2.putText(
                        out,
                        f"{title} S{s} r={ratio:.2f}",
                        (5, max(15, cy - 6)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.42,
                        color,
                        1,
                        cv2.LINE_AA,
                    )
                    break

        return out

    # =========================
    # 메인 check
    # =========================

    def check(self, ally_roi, enemy_roi, colors, stage_config=None):
        """
        반환:
            불 들어온 막대기 번호 set
            예: {1, 2, 8}

        규칙:
            아군 1~5
            적군 6~10
        """
        if ally_roi is None or enemy_roi is None:
            self.last_info = {}
            return set()

        if stage_config is not None:
            self.slot_count = stage_config.get("slot_count", self.slot_count)
            self.my_pick_slot = stage_config.get("my_pick_slot", self.my_pick_slot)
            self.color_ratio_threshold = stage_config.get("color_ratio_threshold", self.color_ratio_threshold)
            self.inner_top_ratio = stage_config.get("inner_top_ratio", self.inner_top_ratio)
            self.inner_bottom_ratio = stage_config.get("inner_bottom_ratio", self.inner_bottom_ratio)
            ally_hsv_ranges = stage_config.get("ally_hsv_ranges")
            enemy_hsv_ranges = stage_config.get("enemy_hsv_ranges")
        else:
            ally_hsv_ranges = None
            enemy_hsv_ranges = None

        color_ranges = self._resolve_color_ranges(colors, ally_hsv_ranges, enemy_hsv_ranges)

        ally_blue = self._segment_color_presence(
            ally_roi,
            color_ranges["blue"],
        )

        ally_yellow = self._segment_color_presence(
            ally_roi,
            color_ranges["yellow"],
        )

        enemy_red = self._segment_color_presence(
            enemy_roi,
            color_ranges["red"],
        )

        blue_slots = ally_blue["active_slots"]
        yellow_slots = ally_yellow["active_slots"]
        red_slots = enemy_red["active_slots"]

        ally_active_slots = sorted(set(blue_slots + yellow_slots))
        enemy_active_slots = sorted(set(red_slots))

        pick_info = self.detect_pick_turn_from_patterns(
            ally_active_slots,
            enemy_active_slots,
        )

        blue_slot = self._pick_primary_slot(blue_slots, ally_blue["slot_ratios"])
        yellow_slot = self._pick_primary_slot(yellow_slots, ally_yellow["slot_ratios"])
        enemy_slot = self._pick_primary_slot(red_slots, enemy_red["slot_ratios"])

        is_my_turn = len(yellow_slots) > 0
        ally_slot = yellow_slot if is_my_turn else blue_slot

        pick_order = self._calc_pick_order(
            ally_slot=ally_slot,
            enemy_slot=enemy_slot,
            pick_turn_team=pick_info["pick_turn_team"],
            is_my_turn=is_my_turn,
        )

        self.last_info = {
            "blue_y": self._slot_to_center_y(blue_slot),
            "yellow_y": self._slot_to_center_y(yellow_slot),
            "red_y": self._slot_to_center_y(enemy_slot),

            "blue_strength": ally_blue["slot_ratios"].get(blue_slot, 0.0) if blue_slot else 0.0,
            "yellow_strength": ally_yellow["slot_ratios"].get(yellow_slot, 0.0) if yellow_slot else 0.0,
            "red_strength": enemy_red["slot_ratios"].get(enemy_slot, 0.0) if enemy_slot else 0.0,

            "is_my_turn": is_my_turn,
            "ally_slot": ally_slot,
            "enemy_slot": enemy_slot,
            "turn_slot": ally_slot,

            "blue_slots": blue_slots,
            "yellow_slots": yellow_slots,
            "red_slots": red_slots,

            "blue_slot_ratios": ally_blue["slot_ratios"],
            "yellow_slot_ratios": ally_yellow["slot_ratios"],
            "red_slot_ratios": enemy_red["slot_ratios"],

            "ally_slot_ranges": ally_blue["slot_ranges"],
            "enemy_slot_ranges": enemy_red["slot_ranges"],

            "ally_active_slots": ally_active_slots,
            "enemy_active_slots": enemy_active_slots,

            "ally_pattern": pick_info["ally_pattern"],
            "enemy_pattern": pick_info["enemy_pattern"],
            "ally_stage": pick_info["ally_stage"],
            "enemy_stage": pick_info["enemy_stage"],

            "pick_turn_team": pick_info["pick_turn_team"],
            "is_ally_pick_turn": pick_info["is_ally_pick_turn"],
            "is_enemy_pick_turn": pick_info["is_enemy_pick_turn"],

            "pick_order": pick_order,
        }

        if self.debug:
            self._save_debug_image("ally_roi.png", ally_roi)
            self._save_debug_image("enemy_roi.png", enemy_roi)

            ally_blue_dbg = self._draw_debug_roi(ally_roi, "BLUE", ally_blue, side="ally_blue")
            ally_yellow_dbg = self._draw_debug_roi(ally_roi, "YELLOW", ally_yellow, side="ally_yellow")
            enemy_red_dbg = self._draw_debug_roi(enemy_roi, "RED", enemy_red, side="enemy_red")

            self._save_debug_image("ally_blue_debug.png", ally_blue_dbg)
            self._save_debug_image("ally_yellow_debug.png", ally_yellow_dbg)
            self._save_debug_image("enemy_red_debug.png", enemy_red_dbg)

            print("[StickChecker] blue_slots =", blue_slots)
            print("[StickChecker] yellow_slots =", yellow_slots)
            print("[StickChecker] red_slots =", red_slots)
            print("[StickChecker] ally_active_slots =", ally_active_slots)
            print("[StickChecker] enemy_active_slots =", enemy_active_slots)
            print("[StickChecker] ally_pattern =", pick_info["ally_pattern"])
            print("[StickChecker] enemy_pattern =", pick_info["enemy_pattern"])
            print("[StickChecker] ally_stage =", pick_info["ally_stage"])
            print("[StickChecker] enemy_stage =", pick_info["enemy_stage"])
            print("[StickChecker] pick_turn_team =", pick_info["pick_turn_team"])
            print("[StickChecker] pick_order =", pick_order)
            print("[StickChecker] is_my_turn =", is_my_turn)

        lit_bars = set()

        # 아군: 1~5
        for slot in ally_active_slots:
            lit_bars.add(slot)

        # 적군: 6~10
        for slot in enemy_active_slots:
            lit_bars.add(slot + 5)

        return lit_bars