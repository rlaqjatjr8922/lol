import cv2
import numpy as np

# =========================
# 사용자 직접 설정
# =========================

# 아군 막대 ROI (파랑 / 노랑)
ALLY_TURN_BAR_ROI = (87, 136, 6, 730)

# 적군 막대 ROI (빨강)
ENEMY_TURN_BAR_ROI = (2248, 136, 6, 730)

# 슬롯 중심 y 좌표 5개 (디버그용)
TURN_SLOT_CENTERS = [204, 350, 496, 642, 788]

# 내 슬롯 번호
MY_PICK_SLOT = 5

# 세로를 5칸으로 나눔
SLOT_COUNT = 5

# 각 칸 안에서 실제 색을 읽을 내부 영역 비율
INNER_TOP_RATIO = 0.06
INNER_BOTTOM_RATIO = 0.94

# "90% 이상 꽉 찼을 때만" 활성 슬롯으로 인정
COLOR_RATIO_THRESHOLD = 0.90

# HSV 범위
# 노랑: #FFD44A 근처
YELLOW_LOWER = (18, 90, 90)
YELLOW_UPPER = (40, 255, 255)

# 파랑: #24BFFF 근처
BLUE_LOWER = (85, 80, 80)
BLUE_UPPER = (130, 255, 255)

# 빨강
RED1_LOWER = (0, 140, 140)
RED1_UPPER = (8, 255, 255)
RED2_LOWER = (172, 140, 140)
RED2_UPPER = (179, 255, 255)


# =========================
# 내부 유틸
# =========================

def _clamp_roi(img, roi):
    h, w = img.shape[:2]
    x, y, rw, rh = roi

    x = max(0, min(w - 1, x))
    y = max(0, min(h - 1, y))
    rw = max(1, min(w - x, rw))
    rh = max(1, min(h - y, rh))
    return x, y, rw, rh


def _open_mask(mask):
    kernel = np.ones((3, 3), np.uint8)
    return cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)


def _build_slot_ranges(y, rh, slot_count=SLOT_COUNT):
    """
    ROI 높이를 slot_count개로 균등 분할.
    return: [(slot_idx, abs_y1, abs_y2, abs_center_y), ...]
    """
    ranges = []
    step = rh / float(slot_count)

    for i in range(slot_count):
        raw_y1 = y + int(round(i * step))
        raw_y2 = y + int(round((i + 1) * step)) - 1

        if i == slot_count - 1:
            raw_y2 = y + rh - 1

        seg_h = max(1, raw_y2 - raw_y1 + 1)

        inner_y1 = raw_y1 + int(round(seg_h * INNER_TOP_RATIO))
        inner_y2 = raw_y1 + int(round(seg_h * INNER_BOTTOM_RATIO)) - 1

        inner_y1 = max(raw_y1, min(raw_y2, inner_y1))
        inner_y2 = max(inner_y1, min(raw_y2, inner_y2))

        center_y = (raw_y1 + raw_y2) // 2
        ranges.append((i + 1, inner_y1, inner_y2, center_y))

    return ranges


def _calc_mask_ratio(mask):
    total = mask.size
    if total <= 0:
        return 0.0
    return float(np.count_nonzero(mask)) / float(total)


def _segment_color_presence(img, roi, hsv_ranges):
    """
    ROI를 5칸으로 나눠서 각 칸에 색이 90% 이상 찼는지 검사.
    hsv_ranges: [(lower, upper), ...]
    """
    x, y, rw, rh = _clamp_roi(img, roi)
    cut = img[y:y + rh, x:x + rw]
    hsv = cv2.cvtColor(cut, cv2.COLOR_BGR2HSV)

    slot_ranges = _build_slot_ranges(y, rh, SLOT_COUNT)

    active_slots = []
    slot_ratios = {}

    for slot_idx, abs_y1, abs_y2, _center_y in slot_ranges:
        rel_y1 = abs_y1 - y
        rel_y2 = abs_y2 - y

        patch = hsv[rel_y1:rel_y2 + 1, :]
        if patch.size == 0:
            slot_ratios[slot_idx] = 0.0
            continue

        merged_mask = None
        for lower, upper in hsv_ranges:
            m = cv2.inRange(patch, lower, upper)
            merged_mask = m if merged_mask is None else cv2.bitwise_or(merged_mask, m)

        merged_mask = _open_mask(merged_mask)
        ratio = _calc_mask_ratio(merged_mask)
        slot_ratios[slot_idx] = ratio

        if ratio >= COLOR_RATIO_THRESHOLD:
            active_slots.append(slot_idx)

    return {
        "roi_box": (x, y, x + rw, y + rh),
        "slot_ranges": slot_ranges,
        "active_slots": active_slots,
        "slot_ratios": slot_ratios,
    }


def _pick_primary_slot(active_slots, slot_ratios):
    """
    여러 칸이 활성이라면 ratio가 가장 큰 칸을 대표 슬롯으로 사용.
    """
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


def _slot_to_center_y(slot_idx):
    if slot_idx is None:
        return None
    if 1 <= slot_idx <= len(TURN_SLOT_CENTERS):
        return TURN_SLOT_CENTERS[slot_idx - 1]
    return None


def normalize_slots(slots):
    return tuple(sorted(set(slots)))


def get_pattern_a_stage(slots):
    """
    패턴 A:
      (1,2) -> 0
      (3,4) -> 1
      (5,)  -> 2
      ()    -> 3
    """
    slots = normalize_slots(slots)

    if slots == (1, 2):
        return 0
    if slots == (3, 4):
        return 1
    if slots == (5,):
        return 2
    if slots == ():
        return 3
    return None


def get_pattern_b_stage(slots):
    """
    패턴 B:
      (1,)   -> 0
      (2,3)  -> 1
      (4,5)  -> 2
      ()     -> 3
    """
    slots = normalize_slots(slots)

    if slots == (1,):
        return 0
    if slots == (2, 3):
        return 1
    if slots == (4, 5):
        return 2
    if slots == ():
        return 3
    return None


def detect_team_pattern(slots):
    """
    return:
      ("A", stage) / ("B", stage) / (None, stage_or_None)

    () 는 A/B 둘 다 가능하므로 단독으로는 패턴 확정 불가
    """
    slots = normalize_slots(slots)
    a_stage = get_pattern_a_stage(slots)
    b_stage = get_pattern_b_stage(slots)

    if slots == ():
        return (None, 3)

    if a_stage is not None and b_stage is None:
        return ("A", a_stage)

    if b_stage is not None and a_stage is None:
        return ("B", b_stage)

    return (None, None)


def infer_patterns(ally_slots, enemy_slots):
    ally_slots = normalize_slots(ally_slots)
    enemy_slots = normalize_slots(enemy_slots)

    ally_pattern, ally_stage = detect_team_pattern(ally_slots)
    enemy_pattern, enemy_stage = detect_team_pattern(enemy_slots)

    # 한쪽이 확실하면 반대쪽은 반대 패턴으로 추론
    if ally_pattern == "A" and enemy_pattern is None:
        enemy_pattern = "B"
        enemy_stage = get_pattern_b_stage(enemy_slots)
    elif ally_pattern == "B" and enemy_pattern is None:
        enemy_pattern = "A"
        enemy_stage = get_pattern_a_stage(enemy_slots)

    if enemy_pattern == "A" and ally_pattern is None:
        ally_pattern = "B"
        ally_stage = get_pattern_b_stage(ally_slots)
    elif enemy_pattern == "B" and ally_pattern is None:
        ally_pattern = "A"
        ally_stage = get_pattern_a_stage(ally_slots)

    return {
        "ally_pattern": ally_pattern,
        "ally_stage": ally_stage,
        "enemy_pattern": enemy_pattern,
        "enemy_stage": enemy_stage,
    }


def detect_pick_turn_from_patterns(ally_slots, enemy_slots):
    """
    규칙:
    패턴 순서는 항상 B -> A -> B -> A -> B -> A

    따라서
    - B단계 == A단계     -> 패턴 B 쪽 차례
    - B단계 == A단계 + 1 -> 패턴 A 쪽 차례
    """
    info = infer_patterns(ally_slots, enemy_slots)

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
# ROI crop
# =========================

def crop_ally_turn_roi(img):
    x, y, rw, rh = _clamp_roi(img, ALLY_TURN_BAR_ROI)
    return img[y:y + rh, x:x + rw].copy()


def crop_enemy_turn_roi(img):
    x, y, rw, rh = _clamp_roi(img, ENEMY_TURN_BAR_ROI)
    return img[y:y + rh, x:x + rw].copy()


# =========================
# 메인 감지
# =========================

def detect_turn_slot(img):
    ally_blue = _segment_color_presence(
        img,
        ALLY_TURN_BAR_ROI,
        [(BLUE_LOWER, BLUE_UPPER)],
    )

    ally_yellow = _segment_color_presence(
        img,
        ALLY_TURN_BAR_ROI,
        [(YELLOW_LOWER, YELLOW_UPPER)],
    )

    enemy_red = _segment_color_presence(
        img,
        ENEMY_TURN_BAR_ROI,
        [(RED1_LOWER, RED1_UPPER), (RED2_LOWER, RED2_UPPER)],
    )

    blue_slots = ally_blue["active_slots"]
    yellow_slots = ally_yellow["active_slots"]
    red_slots = enemy_red["active_slots"]

    ally_active_slots = sorted(set(blue_slots + yellow_slots))
    enemy_active_slots = sorted(set(red_slots))

    pick_info = detect_pick_turn_from_patterns(
        ally_active_slots,
        enemy_active_slots,
    )

    blue_slot = _pick_primary_slot(blue_slots, ally_blue["slot_ratios"])
    yellow_slot = _pick_primary_slot(yellow_slots, ally_yellow["slot_ratios"])
    enemy_slot = _pick_primary_slot(red_slots, enemy_red["slot_ratios"])

    # "내 차례"는 노랑이 잡혔을 때로 유지
    is_my_turn = len(yellow_slots) > 0

    # 기존 호환용 값
    ally_slot = yellow_slot if is_my_turn else blue_slot

    blue_y = _slot_to_center_y(blue_slot)
    yellow_y = _slot_to_center_y(yellow_slot)
    red_y = _slot_to_center_y(enemy_slot)

    return {
        "blue_y": blue_y,
        "yellow_y": yellow_y,
        "red_y": red_y,

        "blue_strength": ally_blue["slot_ratios"].get(blue_slot, 0.0) if blue_slot else 0.0,
        "yellow_strength": ally_yellow["slot_ratios"].get(yellow_slot, 0.0) if yellow_slot else 0.0,
        "red_strength": enemy_red["slot_ratios"].get(enemy_slot, 0.0) if enemy_slot else 0.0,

        "is_my_turn": is_my_turn,
        "ally_slot": ally_slot,
        "enemy_slot": enemy_slot,
        "turn_slot": ally_slot,

        "ally_roi_box": ally_blue["roi_box"],
        "enemy_roi_box": enemy_red["roi_box"],

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
    }


def is_my_turn_soon(turn_slot, my_slot=MY_PICK_SLOT):
    if turn_slot is None:
        return False, False

    is_now = (turn_slot == my_slot)
    is_next = (turn_slot + 1 == my_slot)
    return is_now, is_next


# =========================
# 디버그 이미지
# =========================

def draw_turn_debug(img, turn_info):
    out = img.copy()
    h, _ = out.shape[:2]

    ax1, ay1, ax2, ay2 = turn_info["ally_roi_box"]
    ex1, ey1, ex2, ey2 = turn_info["enemy_roi_box"]

    # ROI 박스
    cv2.rectangle(out, (ax1, ay1), (ax2, ay2), (255, 255, 255), 2)
    cv2.putText(
        out,
        "ALLY ROI",
        (ax1 + 8, max(20, ay1 - 8)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (255, 255, 255),
        1,
        cv2.LINE_AA,
    )

    cv2.rectangle(out, (ex1, ey1), (ex2, ey2), (200, 200, 200), 2)
    cv2.putText(
        out,
        "ENEMY ROI",
        (ex1 - 100, max(20, ey1 - 8)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (200, 200, 200),
        1,
        cv2.LINE_AA,
    )

    # 슬롯 중심선
    for idx, _abs_y1, _abs_y2, cy in turn_info["ally_slot_ranges"]:
        cv2.line(out, (ax1 - 20, cy), (ax2 + 160, cy), (180, 180, 180), 1)
        cv2.putText(
            out,
            f"S{idx}",
            (ax2 + 8, cy + 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )

    for idx, _abs_y1, _abs_y2, cy in turn_info["enemy_slot_ranges"]:
        cv2.line(out, (ex1 - 160, cy), (ex2 + 20, cy), (180, 180, 180), 1)
        cv2.putText(
            out,
            f"S{idx}",
            (ex1 - 35, cy + 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )

    # 파랑 활성 슬롯
    for s in turn_info["blue_slots"]:
        cy = _slot_to_center_y(s)
        if cy is None:
            continue
        ratio = turn_info["blue_slot_ratios"].get(s, 0.0)
        cv2.line(out, (ax1, cy), (ax2 + 150, cy), (255, 0, 0), 2)
        cv2.putText(
            out,
            f"BLUE S{s} r={ratio:.2f}",
            (ax1 + 12, max(20, cy - 8)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.48,
            (255, 0, 0),
            1,
            cv2.LINE_AA,
        )

    # 노랑 활성 슬롯
    for s in turn_info["yellow_slots"]:
        cy = _slot_to_center_y(s)
        if cy is None:
            continue
        ratio = turn_info["yellow_slot_ratios"].get(s, 0.0)
        cv2.line(out, (ax1, cy), (ax2 + 150, cy), (0, 255, 255), 2)
        cv2.putText(
            out,
            f"YELLOW S{s} r={ratio:.2f}",
            (ax1 + 12, min(h - 10, cy + 18)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.48,
            (0, 255, 255),
            1,
            cv2.LINE_AA,
        )

    # 빨강 활성 슬롯
    for s in turn_info["red_slots"]:
        cy = _slot_to_center_y(s)
        if cy is None:
            continue
        ratio = turn_info["red_slot_ratios"].get(s, 0.0)
        cv2.line(out, (ex1 - 150, cy), (ex2, cy), (0, 0, 255), 2)
        cv2.putText(
            out,
            f"RED S{s} r={ratio:.2f}",
            (max(10, ex1 - 270), min(h - 10, cy + 18)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.48,
            (0, 0, 255),
            1,
            cv2.LINE_AA,
        )

    label1 = f"ALLY ACTIVE = {turn_info['ally_active_slots']}"
    label2 = f"ENEMY ACTIVE = {turn_info['enemy_active_slots']}"
    label3 = f"ALLY PATTERN={turn_info['ally_pattern']} STAGE={turn_info['ally_stage']}"
    label4 = f"ENEMY PATTERN={turn_info['enemy_pattern']} STAGE={turn_info['enemy_stage']}"
    label5 = f"PICK TURN = {turn_info['pick_turn_team']}"

    color5 = (255, 255, 255)
    if turn_info["is_ally_pick_turn"]:
        color5 = (0, 255, 255)
    elif turn_info["is_enemy_pick_turn"]:
        color5 = (0, 0, 255)

    cv2.putText(out, label1, (30, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(out, label2, (30, 72), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(out, label3, (30, 104), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(out, label4, (30, 136), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(out, label5, (30, 168), cv2.FONT_HERSHEY_SIMPLEX, 0.85, color5, 2, cv2.LINE_AA)

    if turn_info["is_my_turn"]:
        cv2.putText(
            out,
            "MY TURN (YELLOW DETECTED)",
            (30, 200),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.75,
            (0, 255, 255),
            2,
            cv2.LINE_AA,
        )

    return out