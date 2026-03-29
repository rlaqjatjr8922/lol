import os
import cv2
import numpy as np

INPUT_DIR = r"C:\Users\gimbe\OneDrive\Desktop\lol_project\대이터추출\스크린샷"
OUTPUT_DIR = r"C:\Users\gimbe\OneDrive\Desktop\lol_project\대이터추출\새 폴더 (2)"

os.makedirs(OUTPUT_DIR, exist_ok=True)

IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp", ".bmp")

CENTER_GRID_RATIO = (0.31, 0.16, 0.69, 0.83)
SAVE_SIZE = (116, 116)


def imread_korean(path):
    try:
        data = np.fromfile(path, dtype=np.uint8)
        return cv2.imdecode(data, cv2.IMREAD_COLOR)
    except Exception:
        return None


def imwrite_korean(path, img):
    ext = os.path.splitext(path)[1]
    ok, buf = cv2.imencode(ext, img)
    if ok:
        buf.tofile(path)
        return True
    return False


def crop_ratio(img, ratio):
    h, w = img.shape[:2]
    x1 = int(w * ratio[0])
    y1 = int(h * ratio[1])
    x2 = int(w * ratio[2])
    y2 = int(h * ratio[3])
    return img[y1:y2, x1:x2], (x1, y1, x2, y2)


def preprocess_for_boxes(roi):
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (3, 3), 0)

    edge = cv2.Canny(blur, 80, 160)

    kernel = np.ones((3, 3), np.uint8)
    edge = cv2.dilate(edge, kernel, iterations=1)

    return gray, edge


def is_good_box(x, y, w, h, roi_w, roi_h):
    if w < roi_w * 0.06 or h < roi_h * 0.08:
        return False

    if w > roi_w * 0.25 or h > roi_h * 0.30:
        return False

    ratio = w / float(h)
    if ratio < 0.75 or ratio > 1.25:
        return False

    return True


def iou(box1, box2):
    x1, y1, w1, h1 = box1
    x2, y2, w2, h2 = box2

    xa = max(x1, x2)
    ya = max(y1, y2)
    xb = min(x1 + w1, x2 + w2)
    yb = min(y1 + h1, y2 + h2)

    inter_w = max(0, xb - xa)
    inter_h = max(0, yb - ya)
    inter = inter_w * inter_h

    area1 = w1 * h1
    area2 = w2 * h2
    union = area1 + area2 - inter

    if union == 0:
        return 0.0
    return inter / union


def remove_duplicates(boxes):
    boxes = sorted(boxes, key=lambda b: b[2] * b[3], reverse=True)
    kept = []

    for b in boxes:
        duplicated = False
        for k in kept:
            if iou(b, k) > 0.4:
                duplicated = True
                break
        if not duplicated:
            kept.append(b)

    return kept


def make_square_crop(img, x, y, w, h, pad=-0.06):
    size = int(max(w, h) * (1.0 + pad))

    cx = x + w // 2
    cy = y + h // 2

    x1 = cx - size // 2
    y1 = cy - size // 2
    x2 = x1 + size
    y2 = y1 + size

    x1 = max(0, x1)
    y1 = max(0, y1)
    x2 = min(img.shape[1], x2)
    y2 = min(img.shape[0], y2)

    return img[y1:y2, x1:x2]


def sort_boxes_reading_order(boxes):
    boxes = sorted(boxes, key=lambda b: (b[1], b[0]))

    rows = []
    for box in boxes:
        x, y, w, h = box
        cy = y + h / 2

        placed = False
        for row in rows:
            row_y = np.mean([b[1] + b[3] / 2 for b in row])
            if abs(cy - row_y) < h * 0.5:
                row.append(box)
                placed = True
                break

        if not placed:
            rows.append([box])

    for row in rows:
        row.sort(key=lambda b: b[0])

    rows.sort(key=lambda row: np.mean([b[1] + b[3] / 2 for b in row]))

    ordered = []
    for row in rows:
        ordered.extend(row)

    return ordered


def process_one_image(img_path, start_index):
    img = imread_korean(img_path)
    if img is None:
        print(f"[실패] 이미지 로드 실패: {img_path}")
        return start_index

    roi, _ = crop_ratio(img, CENTER_GRID_RATIO)
    roi_h, roi_w = roi.shape[:2]

    _, edge = preprocess_for_boxes(roi)
    contours, _ = cv2.findContours(edge, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    boxes = []
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        if is_good_box(x, y, w, h, roi_w, roi_h):
            boxes.append((x, y, w, h))

    boxes = remove_duplicates(boxes)
    boxes = sort_boxes_reading_order(boxes)

    save_index = start_index

    for (x, y, w, h) in boxes:
        icon = make_square_crop(roi, x, y, w, h, pad=-0.06)
        if icon.size == 0:
            continue

        icon = cv2.resize(icon, SAVE_SIZE, interpolation=cv2.INTER_AREA)

        out_path = os.path.join(OUTPUT_DIR, f"자름이미지{save_index}.png")
        imwrite_korean(out_path, icon)
        save_index += 1

    print(f"[완료] {os.path.basename(img_path)} / 저장 {save_index - start_index}개")
    return save_index


def main():
    if not os.path.exists(INPUT_DIR):
        print("[실패] 입력 폴더 없음:", INPUT_DIR)
        return

    files = [
        f for f in os.listdir(INPUT_DIR)
        if f.lower().endswith(IMAGE_EXTS)
    ]
    files.sort()

    if not files:
        print("[실패] 이미지 없음")
        return

    save_index = 1
    for file_name in files:
        img_path = os.path.join(INPUT_DIR, file_name)
        save_index = process_one_image(img_path, save_index)

    print("전부 완료")


if __name__ == "__main__":
    main()