import cv2
import numpy as np

# 기준 해상도
BASE_W = 2048
BASE_H = 945

# 예시 좌표
ALLY_LIGHTS = [
    (620, 120, 20, 20),
    (620, 180, 20, 20),
    (620, 240, 20, 20),
    (620, 300, 20, 20),
    (620, 360, 20, 20),
]

ENEMY_LIGHTS = [
    (1408, 120, 20, 20),
    (1408, 180, 20, 20),
    (1408, 240, 20, 20),
    (1408, 300, 20, 20),
    (1408, 360, 20, 20),
]


def scale_box(box, w, h):
    x, y, bw, bh = box
    sx = w / BASE_W
    sy = h / BASE_H
    return (
        int(round(x * sx)),
        int(round(y * sy)),
        int(round(bw * sx)),
        int(round(bh * sy)),
    )


def safe_crop(img, box):
    x, y, w, h = box
    ih, iw = img.shape[:2]

    x1 = max(0, x)
    y1 = max(0, y)
    x2 = min(iw, x + w)
    y2 = min(ih, y + h)

    if x1 >= x2 or y1 >= y2:
        return None

    return img[y1:y2, x1:x2].copy()


def yellow_score(crop):
    if crop is None:
        return 0.0

    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
    lower = np.array([15, 80, 80], dtype=np.uint8)
    upper = np.array([45, 255, 255], dtype=np.uint8)

    mask = cv2.inRange(hsv, lower, upper)
    return float(mask.mean())


def detect_active_slots(img, boxes, threshold=150):
    h, w = img.shape[:2]
    result = []

    for box in boxes:
        scaled = scale_box(box, w, h)
        crop = safe_crop(img, scaled)
        score = yellow_score(crop)
        result.append(score > threshold)

    return result


def detect_turn_slot(img):
    ally_pattern = detect_active_slots(img, ALLY_LIGHTS)
    enemy_pattern = detect_active_slots(img, ENEMY_LIGHTS)

    ally_active_slots = sum(ally_pattern)
    enemy_active_slots = sum(enemy_pattern)

    pick_turn_team = None
    if ally_active_slots > enemy_active_slots:
        pick_turn_team = "ally"
    elif enemy_active_slots > ally_active_slots:
        pick_turn_team = "enemy"

    is_my_turn = pick_turn_team == "ally"

    return {
        "ally_active_slots": ally_active_slots,
        "enemy_active_slots": enemy_active_slots,
        "ally_pattern": ally_pattern,
        "enemy_pattern": enemy_pattern,
        "pick_turn_team": pick_turn_team,
        "is_my_turn": is_my_turn,
        "is_ally_pick_turn": pick_turn_team == "ally",
    }


def draw_turn_debug(img, turn_info):
    out = img.copy()
    h, w = img.shape[:2]

    for box, active in zip(ALLY_LIGHTS, turn_info["ally_pattern"]):
        x, y, bw, bh = scale_box(box, w, h)
        color = (0, 255, 0) if active else (0, 0, 255)
        cv2.rectangle(out, (x, y), (x + bw, y + bh), color, 2)

    for box, active in zip(ENEMY_LIGHTS, turn_info["enemy_pattern"]):
        x, y, bw, bh = scale_box(box, w, h)
        color = (255, 255, 0) if active else (255, 0, 0)
        cv2.rectangle(out, (x, y), (x + bw, y + bh), color, 2)

    text = (
        f"ally={turn_info['ally_active_slots']} "
        f"enemy={turn_info['enemy_active_slots']} "
        f"turn={turn_info['pick_turn_team']} "
        f"my_turn={turn_info['is_my_turn']}"
    )
    cv2.putText(out, text, (30, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 2)

    return out