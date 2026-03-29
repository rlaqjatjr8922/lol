import cv2
import numpy as np


# =========================
# 사용자 직접 설정
# =========================

# 아군 쪽 막대 ROI (파랑 / 노랑)
ALLY_TURN_BAR_ROI = (87, 136, 6, 730)

# 적군 쪽 막대 ROI (빨강)
ENEMY_TURN_BAR_ROI = (2248, 136, 6, 730)

# 슬롯 중심 y 좌표 5개
TURN_SLOT_CENTERS = [204, 350, 496, 642, 788]

# 내 슬롯 번호
MY_PICK_SLOT = 5

# HSV 범위
YELLOW_LOWER = (18, 100, 100)
YELLOW_UPPER = (40, 255, 255)

BLUE_LOWER = (85, 80, 80)
BLUE_UPPER = (130, 255, 255)

RED1_LOWER = (0, 100, 100)
RED1_UPPER = (10, 255, 255)

RED2_LOWER = (170, 100, 100)
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


def _mask_center_y(mask):
    ys, _ = np.where(mask > 0)
    if len(ys) == 0:
        return None, 0

    center_y = int(round(float(np.mean(ys))))
    strength = int(np.count_nonzero(mask))
    return center_y, strength


def _nearest_slot_from_y(y, slot_centers):
    if y is None:
        return None

    best_slot = None
    best_dist = 10**9

    for idx, cy in enumerate(slot_centers, start=1):
        dist = abs(y - cy)
        if dist < best_dist:
            best_dist = dist
            best_slot = idx

    return best_slot


def _open_mask(mask):
    kernel = np.ones((3, 3), np.uint8)
    return cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)


def _detect_blue_yellow_in_roi(img, roi):
    x, y, rw, rh = _clamp_roi(img, roi)
    cut = img[y:y + rh, x:x + rw]
    hsv = cv2.cvtColor(cut, cv2.COLOR_BGR2HSV)

    yellow_mask = cv2.inRange(hsv, YELLOW_LOWER, YELLOW_UPPER)
    blue_mask = cv2.inRange(hsv, BLUE_LOWER, BLUE_UPPER)

    yellow_mask = _open_mask(yellow_mask)
    blue_mask = _open_mask(blue_mask)

    yellow_roi_y, yellow_strength = _mask_center_y(yellow_mask)
    blue_roi_y, blue_strength = _mask_center_y(blue_mask)

    yellow_y = (y + yellow_roi_y) if yellow_roi_y is not None else None
    blue_y = (y + blue_roi_y) if blue_roi_y is not None else None

    return {
        "roi_box": (x, y, x + rw, y + rh),
        "yellow_y": yellow_y,
        "blue_y": blue_y,
        "yellow_strength": yellow_strength,
        "blue_strength": blue_strength,
    }


def _detect_red_in_roi(img, roi):
    x, y, rw, rh = _clamp_roi(img, roi)
    cut = img[y:y + rh, x:x + rw]
    hsv = cv2.cvtColor(cut, cv2.COLOR_BGR2HSV)

    red_mask1 = cv2.inRange(hsv, RED1_LOWER, RED1_UPPER)
    red_mask2 = cv2.inRange(hsv, RED2_LOWER, RED2_UPPER)
    red_mask = cv2.bitwise_or(red_mask1, red_mask2)
    red_mask = _open_mask(red_mask)

    red_roi_y, red_strength = _mask_center_y(red_mask)
    red_y = (y + red_roi_y) if red_roi_y is not None else None

    return {
        "roi_box": (x, y, x + rw, y + rh),
        "red_y": red_y,
        "red_strength": red_strength,
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
    ally_info = _detect_blue_yellow_in_roi(img, ALLY_TURN_BAR_ROI)
    enemy_info = _detect_red_in_roi(img, ENEMY_TURN_BAR_ROI)

    is_my_turn = ally_info["yellow_strength"] > 40

    ally_base_y = ally_info["yellow_y"] if is_my_turn else ally_info["blue_y"]
    ally_slot = _nearest_slot_from_y(ally_base_y, TURN_SLOT_CENTERS)
    enemy_slot = _nearest_slot_from_y(enemy_info["red_y"], TURN_SLOT_CENTERS)

    return {
        "blue_y": ally_info["blue_y"],
        "yellow_y": ally_info["yellow_y"],
        "red_y": enemy_info["red_y"],

        "blue_strength": ally_info["blue_strength"],
        "yellow_strength": ally_info["yellow_strength"],
        "red_strength": enemy_info["red_strength"],

        "is_my_turn": is_my_turn,

        "ally_slot": ally_slot,
        "enemy_slot": enemy_slot,
        "turn_slot": ally_slot,

        "ally_roi_box": ally_info["roi_box"],
        "enemy_roi_box": enemy_info["roi_box"],
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

    # 아군 ROI 박스
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

    # 적군 ROI 박스
    cv2.rectangle(out, (ex1, ey1), (ex2, ey2), (200, 200, 200), 2)
    cv2.putText(
        out,
        "ENEMY ROI",
        (ex1 - 90, max(20, ey1 - 8)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (200, 200, 200),
        1,
        cv2.LINE_AA,
    )

    # 슬롯 중심선
    for idx, cy in enumerate(TURN_SLOT_CENTERS, start=1):
        cv2.line(out, (ax1 - 20, cy), (ax2 + 120, cy), (180, 180, 180), 1)
        cv2.line(out, (ex1 - 120, cy), (ex2 + 20, cy), (180, 180, 180), 1)

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

    # 파랑
    if turn_info["blue_y"] is not None:
        by = turn_info["blue_y"]
        cv2.line(out, (ax1, by), (ax2 + 140, by), (255, 0, 0), 2)
        cv2.putText(
            out,
            f"BLUE y={by} s={turn_info['blue_strength']}",
            (ax1 + 10, max(20, by - 8)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 0, 0),
            1,
            cv2.LINE_AA,
        )

    # 노랑
    if turn_info["yellow_y"] is not None:
        yy = turn_info["yellow_y"]
        cv2.line(out, (ax1, yy), (ax2 + 140, yy), (0, 255, 255), 2)
        cv2.putText(
            out,
            f"YELLOW y={yy} s={turn_info['yellow_strength']}",
            (ax1 + 10, min(h - 10, yy + 18)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 255),
            1,
            cv2.LINE_AA,
        )

    # 빨강
    if turn_info["red_y"] is not None:
        ry = turn_info["red_y"]
        cv2.line(out, (ex1 - 140, ry), (ex2, ry), (0, 0, 255), 2)
        cv2.putText(
            out,
            f"RED y={ry} s={turn_info['red_strength']}",
            (max(10, ex1 - 260), min(h - 10, ry + 18)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 0, 255),
            1,
            cv2.LINE_AA,
        )

    ally_slot = turn_info["ally_slot"]
    enemy_slot = turn_info["enemy_slot"]

    label1 = f"ALLY SLOT = {ally_slot}" if ally_slot is not None else "ALLY SLOT = None"
    label2 = f"ENEMY SLOT = {enemy_slot}" if enemy_slot is not None else "ENEMY SLOT = None"

    if turn_info["is_my_turn"]:
        label1 += " (MY TURN)"
        color1 = (0, 255, 255)
    else:
        color1 = (255, 200, 0)

    cv2.putText(
        out,
        label1,
        (30, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        color1,
        2,
        cv2.LINE_AA,
    )

    cv2.putText(
        out,
        label2,
        (30, 78),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        (0, 0, 255),
        2,
        cv2.LINE_AA,
    )

    return out