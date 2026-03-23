import os
import cv2
import numpy as np

INPUT_DIR = r"C:\Users\gimbe\OneDrive\Desktop\lol_project\대이터추출\자료"
OUTPUT_DIR = r"C:\Users\gimbe\OneDrive\Desktop\lol_project\대이터추출\결과"
DEBUG_DIR = os.path.join(OUTPUT_DIR, "_debug")

IMAGE_EXT = (".png", ".jpg", ".jpeg", ".webp")

# 아래 UI 너무 섞이면 마지막 값 더 줄여도 됨
ROI = (320, 150, 1700, 850)

BOX_SIZE = 113

# 박스 전체를 왼쪽/위로 이동
SHIFT_X = -1
SHIFT_Y = -1

IOU_THRESH = 0.22
CENTER_DIST_THRESH = 28
ROW_Y_TOL = 40


def imread_korean(path):
    data = np.fromfile(path, dtype=np.uint8)
    return cv2.imdecode(data, cv2.IMREAD_COLOR)


def imwrite_korean(path, img):
    ext = os.path.splitext(path)[1].lower()
    if ext not in [".png", ".jpg", ".jpeg", ".webp"]:
        ext = ".png"
        path += ".png"

    ok, buf = cv2.imencode(ext, img)
    if ok:
        buf.tofile(path)


def box_center(box):
    x1, y1, x2, y2 = box
    return (x1 + x2) // 2, (y1 + y2) // 2


def iou(box1, box2):
    x1, y1, x2, y2 = box1
    a1, b1, a2, b2 = box2

    ix1 = max(x1, a1)
    iy1 = max(y1, b1)
    ix2 = min(x2, a2)
    iy2 = min(y2, b2)

    if ix2 <= ix1 or iy2 <= iy1:
        return 0.0

    inter = (ix2 - ix1) * (iy2 - iy1)
    area1 = (x2 - x1) * (y2 - y1)
    area2 = (a2 - a1) * (b2 - b1)
    union = area1 + area2 - inter

    return inter / union if union > 0 else 0.0


def center_dist(box1, box2):
    c1x, c1y = box_center(box1)
    c2x, c2y = box_center(box2)
    return ((c1x - c2x) ** 2 + (c1y - c2y) ** 2) ** 0.5


def box_area(box):
    x1, y1, x2, y2 = box
    return max(0, x2 - x1) * max(0, y2 - y1)


def dedupe_boxes(boxes):
    boxes = sorted(boxes, key=box_area, reverse=True)

    kept = []
    for b in boxes:
        overlapped = False
        for k in kept:
            if iou(b, k) > IOU_THRESH or center_dist(b, k) < CENTER_DIST_THRESH:
                overlapped = True
                break
        if not overlapped:
            kept.append(b)

    return kept


def sort_boxes(boxes):
    return sorted(boxes, key=lambda b: (b[1] // ROW_Y_TOL, b[0]))


def make_113_box(cx, cy):
    half = BOX_SIZE // 2
    return (
        int(cx - half),
        int(cy - half),
        int(cx - half + BOX_SIZE),
        int(cy - half + BOX_SIZE)
    )


def clamp_box(box, w, h):
    x1, y1, x2, y2 = box

    if x1 < 0:
        x1 = 0
        x2 = BOX_SIZE
    if y1 < 0:
        y1 = 0
        y2 = BOX_SIZE
    if x2 > w:
        x2 = w
        x1 = w - BOX_SIZE
    if y2 > h:
        y2 = h
        y1 = h - BOX_SIZE

    if x1 < 0 or y1 < 0 or x2 > w or y2 > h:
        return None

    if (x2 - x1) != BOX_SIZE or (y2 - y1) != BOX_SIZE:
        return None

    return (x1, y1, x2, y2)


def preprocess(roi):
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

    # 밝은 아이콘 + 어두운 아이콘 둘 다 잡기
    _, th1 = cv2.threshold(gray, 105, 255, cv2.THRESH_BINARY)
    _, th2 = cv2.threshold(gray, 75, 255, cv2.THRESH_BINARY)
    th = cv2.bitwise_or(th1, th2)

    # 얇은 글자 줄이기
    th = cv2.morphologyEx(
        th,
        cv2.MORPH_OPEN,
        np.ones((2, 2), np.uint8),
        iterations=1
    )

    # 아이콘 내부 조각 연결 강화
    th = cv2.morphologyEx(
        th,
        cv2.MORPH_CLOSE,
        np.ones((7, 7), np.uint8),
        iterations=1
    )

    return gray, th


def find_icon_boxes(img):
    h, w = img.shape[:2]
    rx1, ry1, rx2, ry2 = ROI

    rx1 = max(0, min(rx1, w - 1))
    ry1 = max(0, min(ry1, h - 1))
    rx2 = max(rx1 + 1, min(rx2, w))
    ry2 = max(ry1 + 1, min(ry2, h))

    roi = img[ry1:ry2, rx1:rx2]
    gray, mask = preprocess(roi)

    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(mask)

    boxes = []
    debug_mask = np.zeros_like(mask)

    for i in range(1, num_labels):
        x = stats[i, cv2.CC_STAT_LEFT]
        y = stats[i, cv2.CC_STAT_TOP]
        bw = stats[i, cv2.CC_STAT_WIDTH]
        bh = stats[i, cv2.CC_STAT_HEIGHT]
        area = stats[i, cv2.CC_STAT_AREA]

        # 어두운/약한 아이콘도 살리도록 완화
        if bw < 45 or bh < 45:
            continue
        if bw > 150 or bh > 150:
            continue
        if area < 1200:
            continue

        ratio = bw / float(bh)
        if ratio < 0.72 or ratio > 1.28:
            continue

        fill = area / float(bw * bh + 1e-6)
        if fill < 0.12 or fill > 0.97:
            continue

        size = min(bw, bh)

        gx1 = rx1 + x
        gy1 = ry1 + y
        gx2 = gx1 + size
        gy2 = gy1 + size

        boxes.append((gx1, gy1, gx2, gy2))
        debug_mask[y:y + bh, x:x + bw] = 255

    boxes = dedupe_boxes(boxes)
    boxes = sort_boxes(boxes)

    return boxes, gray, mask, debug_mask


def process_image(img, name):
    h, w = img.shape[:2]

    icon_boxes, gray, mask, debug_mask = find_icon_boxes(img)

    final = []
    count = 0

    for (x1, y1, x2, y2) in icon_boxes:
        cx = (x1 + x2) // 2 + SHIFT_X
        cy = (y1 + y2) // 2 + SHIFT_Y

        box = make_113_box(cx, cy)
        box = clamp_box(box, w, h)

        if box is None:
            continue

        bx1, by1, bx2, by2 = box
        crop = img[by1:by2, bx1:bx2]

        # 검출 박스 자체가 113
        if crop.shape[0] != BOX_SIZE or crop.shape[1] != BOX_SIZE:
            continue

        save = os.path.join(OUTPUT_DIR, f"{name}_{count}.png")
        imwrite_korean(save, crop)

        final.append(box)
        count += 1

    dbg = img.copy()
    cv2.rectangle(dbg, (ROI[0], ROI[1]), (ROI[2], ROI[3]), (255, 0, 0), 2)

    # 후보 박스
    for (x1, y1, x2, y2) in icon_boxes:
        cv2.rectangle(dbg, (x1, y1), (x2, y2), (80, 180, 255), 1)

    # 최종 113 박스
    for i, (x1, y1, x2, y2) in enumerate(final):
        cv2.rectangle(dbg, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(
            dbg,
            str(i),
            (x1, max(20, y1 - 6)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 255),
            2,
            cv2.LINE_AA
        )

    imwrite_korean(os.path.join(DEBUG_DIR, f"{name}_debug.png"), dbg)
    imwrite_korean(os.path.join(DEBUG_DIR, f"{name}_mask.png"), mask)
    imwrite_korean(os.path.join(DEBUG_DIR, f"{name}_gray.png"), gray)
    imwrite_korean(os.path.join(DEBUG_DIR, f"{name}_debug_mask.png"), debug_mask)

    return count


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(DEBUG_DIR, exist_ok=True)

    if not os.path.isdir(INPUT_DIR):
        print("❌ 자료 폴더 없음")
        return

    files = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith(IMAGE_EXT)]
    if not files:
        print("❌ 이미지 없음")
        return

    total = 0

    for f in files:
        path = os.path.join(INPUT_DIR, f)
        img = imread_korean(path)

        if img is None:
            print(f"[실패] {f}")
            continue

        name = os.path.splitext(f)[0]
        print(f"처리중: {f}")

        c = process_image(img, name)
        print(f" -> {c}개")

        total += c

    print(f"\n완료: {total}개")
    print(f"디버그 폴더: {DEBUG_DIR}")


if __name__ == "__main__":
    main()