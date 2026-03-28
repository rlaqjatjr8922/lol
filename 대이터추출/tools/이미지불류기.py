import os
import cv2
import numpy as np

# =========================
# 경로
# =========================
INPUT_DIR = r"C:\Users\gimbe\OneDrive\Desktop\lol_project\대이터추출\자료"
OUTPUT_DIR = r"C:\Users\gimbe\OneDrive\Desktop\lol_project\대이터추출\결과"
DEBUG_DIR = os.path.join(OUTPUT_DIR, "_debug")

IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp", ".bmp")

# =========================
# ROI (중앙 챔피언 목록 영역)
# 직접 조금씩 수정 가능
# =========================
ROI = (560, 130, 1390, 910)   # x1, y1, x2, y2

# =========================
# 출력 박스 크기
# =========================
BOX_SIZE = 113

# 최종 crop 중심 미세 이동
SHIFT_X = 0
SHIFT_Y = 0

# =========================
# 후보 필터
# =========================
MIN_W = 70
MIN_H = 70
MAX_W = 150
MAX_H = 150

MIN_AREA = 4500
MAX_AREA = 22000

ASPECT_MIN = 0.78
ASPECT_MAX = 1.22

IOU_THRESH = 0.30
CENTER_DIST_THRESH = 35
ROW_MERGE_Y = 45

# 기대 레이아웃
EXPECTED_COLS = 5
MIN_KEEP = 12
MAX_KEEP = 25


# =========================
# 한글 경로 지원
# =========================
def imread_korean(path):
    data = np.fromfile(path, dtype=np.uint8)
    return cv2.imdecode(data, cv2.IMREAD_COLOR)


def imwrite_korean(path, img):
    ext = os.path.splitext(path)[1].lower()
    if ext not in [".png", ".jpg", ".jpeg", ".webp", ".bmp"]:
        ext = ".png"
        path += ".png"

    ok, buf = cv2.imencode(ext, img)
    if ok:
        buf.tofile(path)


# =========================
# 유틸
# =========================
def box_area(box):
    x1, y1, x2, y2 = box
    return max(0, x2 - x1) * max(0, y2 - y1)


def box_center(box):
    x1, y1, x2, y2 = box
    return ((x1 + x2) // 2, (y1 + y2) // 2)


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
    union = box_area(box1) + box_area(box2) - inter
    return inter / union if union > 0 else 0.0


def center_dist(box1, box2):
    c1x, c1y = box_center(box1)
    c2x, c2y = box_center(box2)
    return ((c1x - c2x) ** 2 + (c1y - c2y) ** 2) ** 0.5


def clamp_box(box, w, h):
    x1, y1, x2, y2 = box

    if x1 < 0:
        x2 += -x1
        x1 = 0
    if y1 < 0:
        y2 += -y1
        y1 = 0
    if x2 > w:
        x1 -= (x2 - w)
        x2 = w
    if y2 > h:
        y1 -= (y2 - h)
        y2 = h

    if x1 < 0 or y1 < 0 or x2 > w or y2 > h:
        return None

    if (x2 - x1) != BOX_SIZE or (y2 - y1) != BOX_SIZE:
        return None

    return (x1, y1, x2, y2)


def make_113_box(cx, cy):
    half = BOX_SIZE // 2
    return (
        int(cx - half),
        int(cy - half),
        int(cx - half + BOX_SIZE),
        int(cy - half + BOX_SIZE)
    )


# =========================
# 전처리
# =========================
def preprocess_roi(roi):
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    # 적응형 threshold
    th_adapt = cv2.adaptiveThreshold(
        blur, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31, 3
    )

    # edge
    edge = cv2.Canny(blur, 60, 140)

    # 합치기
    mask = cv2.bitwise_or(th_adapt, edge)

    # 작은 글씨/잡음 제거
    mask = cv2.morphologyEx(
        mask,
        cv2.MORPH_OPEN,
        np.ones((3, 3), np.uint8),
        iterations=1
    )

    # 아이콘 네모 윤곽 연결
    mask = cv2.morphologyEx(
        mask,
        cv2.MORPH_CLOSE,
        np.ones((7, 7), np.uint8),
        iterations=2
    )

    return gray, mask


# =========================
# 후보 검출
# =========================
def find_candidate_boxes(img):
    h, w = img.shape[:2]
    rx1, ry1, rx2, ry2 = ROI

    rx1 = max(0, min(rx1, w - 1))
    ry1 = max(0, min(ry1, h - 1))
    rx2 = max(rx1 + 1, min(rx2, w))
    ry2 = max(ry1 + 1, min(ry2, h))

    roi = img[ry1:ry2, rx1:rx2]
    gray, mask = preprocess_roi(roi)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    boxes = []

    for cnt in contours:
        x, y, bw, bh = cv2.boundingRect(cnt)
        area = bw * bh

        if bw < MIN_W or bh < MIN_H:
            continue
        if bw > MAX_W or bh > MAX_H:
            continue
        if area < MIN_AREA or area > MAX_AREA:
            continue

        ratio = bw / float(bh)
        if ratio < ASPECT_MIN or ratio > ASPECT_MAX:
            continue

        # 정사각형으로 보정
        side = max(bw, bh)
        cx = x + bw / 2.0
        cy = y + bh / 2.0

        gx1 = int(rx1 + cx - side / 2)
        gy1 = int(ry1 + cy - side / 2)
        gx2 = int(gx1 + side)
        gy2 = int(gy1 + side)

        boxes.append((gx1, gy1, gx2, gy2))

    return boxes, gray, mask


# =========================
# 중복 제거
# =========================
def dedupe_boxes(boxes):
    scored = []
    for b in boxes:
        x1, y1, x2, y2 = b
        w = x2 - x1
        h = y2 - y1
        area = w * h
        ratio = min(w, h) / float(max(w, h) + 1e-6)
        score = area * ratio
        scored.append((score, b))

    scored.sort(reverse=True, key=lambda x: x[0])

    kept = []
    for _, b in scored:
        overlapped = False
        for k in kept:
            if iou(b, k) > IOU_THRESH or center_dist(b, k) < CENTER_DIST_THRESH:
                overlapped = True
                break
        if not overlapped:
            kept.append(b)

    return kept


# =========================
# 행 정렬
# =========================
def cluster_rows(boxes):
    if not boxes:
        return []

    boxes = sorted(boxes, key=lambda b: box_center(b)[1])

    rows = []
    for b in boxes:
        _, cy = box_center(b)

        placed = False
        for row in rows:
            row_cy = int(np.mean([box_center(x)[1] for x in row]))
            if abs(cy - row_cy) <= ROW_MERGE_Y:
                row.append(b)
                placed = True
                break

        if not placed:
            rows.append([b])

    # 각 row 내부는 x 기준 정렬
    for row in rows:
        row.sort(key=lambda b: box_center(b)[0])

    # row 전체는 y 기준 정렬
    rows.sort(key=lambda row: np.mean([box_center(x)[1] for x in row]))

    return rows


def select_grid_boxes(boxes):
    rows = cluster_rows(boxes)

    cleaned_rows = []
    for row in rows:
        # 너무 적은 row 제거
        if len(row) >= 2:
            cleaned_rows.append(row)

    if not cleaned_rows:
        return []

    # row 길이가 너무 크면 x 간격 보고 정리 가능하지만
    # 일단 왼쪽→오른쪽 상위 5개만 사용
    final_rows = []
    for row in cleaned_rows:
        row = sorted(row, key=lambda b: box_center(b)[0])
        if len(row) > EXPECTED_COLS:
            row = row[:EXPECTED_COLS]
        final_rows.append(row)

    # 전체 flatten
    final = []
    for row in final_rows:
        final.extend(row)

    # 최종 개수 제한
    if len(final) > MAX_KEEP:
        final = final[:MAX_KEEP]

    return final


# =========================
# crop 처리
# =========================
def process_image(img, name):
    h, w = img.shape[:2]

    candidate_boxes, gray, mask = find_candidate_boxes(img)
    candidate_boxes = dedupe_boxes(candidate_boxes)
    final_boxes = select_grid_boxes(candidate_boxes)

    saved_boxes = []
    idx = 0

    for b in final_boxes:
        cx, cy = box_center(b)
        cx += SHIFT_X
        cy += SHIFT_Y

        crop_box = make_113_box(cx, cy)
        crop_box = clamp_box(crop_box, w, h)
        if crop_box is None:
            continue

        x1, y1, x2, y2 = crop_box
        crop = img[y1:y2, x1:x2]

        if crop.shape[0] != BOX_SIZE or crop.shape[1] != BOX_SIZE:
            continue

        save_path = os.path.join(OUTPUT_DIR, f"{name}_{idx:02d}.png")
        imwrite_korean(save_path, crop)

        saved_boxes.append(crop_box)
        idx += 1

    # 디버그 이미지
    dbg = img.copy()

    # ROI
    cv2.rectangle(dbg, (ROI[0], ROI[1]), (ROI[2], ROI[3]), (255, 0, 0), 2)

    # 후보 박스
    for (x1, y1, x2, y2) in candidate_boxes:
        cv2.rectangle(dbg, (x1, y1), (x2, y2), (0, 180, 255), 1)

    # 최종 crop 박스
    for i, (x1, y1, x2, y2) in enumerate(saved_boxes):
        cv2.rectangle(dbg, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(
            dbg,
            str(i),
            (x1, max(20, y1 - 8)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 255),
            2,
            cv2.LINE_AA
        )

    imwrite_korean(os.path.join(DEBUG_DIR, f"{name}_debug.png"), dbg)
    imwrite_korean(os.path.join(DEBUG_DIR, f"{name}_mask.png"), mask)
    imwrite_korean(os.path.join(DEBUG_DIR, f"{name}_gray.png"), gray)

    return len(saved_boxes)


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(DEBUG_DIR, exist_ok=True)

    if not os.path.isdir(INPUT_DIR):
        print("❌ INPUT_DIR 없음")
        return

    files = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith(IMAGE_EXTS)]
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

        print(f"처리중: {f}")
        name = os.path.splitext(f)[0]

        count = process_image(img, name)
        print(f" -> {count}개 저장")

        total += count

    print(f"\n완료: 총 {total}개")
    print("결과 폴더:", OUTPUT_DIR)
    print("디버그 폴더:", DEBUG_DIR)


if __name__ == "__main__":
    main()