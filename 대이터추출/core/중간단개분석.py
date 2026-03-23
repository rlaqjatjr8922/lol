import os
import cv2
import numpy as np

BASE_DIR = r"C:\Users\gimbe\OneDrive\Desktop\lol_project\대이터추출"
INPUT_DIR = os.path.join(BASE_DIR, "자료")
OUTPUT_DIR = os.path.join(BASE_DIR, "결과")

TOP_DB_DIR = os.path.join(BASE_DIR, "중간탬")
BOTTOM_DB_DIR = os.path.join(BASE_DIR, "기본템")

RESULT_TXT_PATH = os.path.join(OUTPUT_DIR, "중간단계_구조결과.txt")
IMAGE_EXT = (".png", ".jpg", ".jpeg", ".webp")

BOX_SIZE = 90
MATCH_SIZE = 90

# 슬롯 좌표
TOP_RECT = (1981, 457)
BOTTOM_SINGLE_RECT = (1981, 601)
BOTTOM_LEFT_RECT = (1871, 601)
BOTTOM_RIGHT_RECT = (2093, 601)

# 슬롯 존재 판정
MEAN_THRESHOLD = 20
STD_THRESHOLD = 10
EDGE_THRESHOLD = 60

# 매칭 실패 기준
MATCH_FAIL_SCORE = 50


def imread_korean(path):
    data = np.fromfile(path, dtype=np.uint8)
    return cv2.imdecode(data, cv2.IMREAD_COLOR)


def imwrite_korean(path, img):
    ok, buf = cv2.imencode(".png", img)
    if ok:
        buf.tofile(path)


def crop_by_topleft(img, x1, y1, size):
    h, w = img.shape[:2]
    x2 = x1 + size
    y2 = y1 + size

    src_x1 = max(0, x1)
    src_y1 = max(0, y1)
    src_x2 = min(w, x2)
    src_y2 = min(h, y2)

    crop = img[src_y1:src_y2, src_x1:src_x2]

    if crop.shape[0] == size and crop.shape[1] == size:
        return crop

    canvas = np.zeros((size, size, 3), dtype=np.uint8)

    dst_x1 = src_x1 - x1
    dst_y1 = src_y1 - y1
    dst_x2 = dst_x1 + (src_x2 - src_x1)
    dst_y2 = dst_y1 + (src_y2 - src_y1)

    canvas[dst_y1:dst_y2, dst_x1:dst_x2] = crop
    return canvas


def get_center_crop(img, ratio=0.56):
    h, w = img.shape[:2]
    cw = int(w * ratio)
    ch = int(h * ratio)

    x1 = (w - cw) // 2
    y1 = (h - ch) // 2
    x2 = x1 + cw
    y2 = y1 + ch

    return img[y1:y2, x1:x2]


def preprocess_for_match(img, size=MATCH_SIZE):
    if img is None:
        return None
    return cv2.resize(img, (size, size), interpolation=cv2.INTER_AREA)


def slot_has_item(crop, name=""):
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    mean_val = float(np.mean(gray))
    std_val = float(np.std(gray))
    edges = cv2.Canny(gray, 80, 160)
    edge_count = int(np.count_nonzero(edges))

    result = (
        mean_val > MEAN_THRESHOLD
        and std_val > STD_THRESHOLD
        and edge_count > EDGE_THRESHOLD
    )

    print(
        f"{name:<14} "
        f"mean={mean_val:6.2f} "
        f"std={std_val:6.2f} "
        f"edge={edge_count:4d} "
        f"-> {result}"
    )
    return result


def detect_structure(img):
    top_crop = crop_by_topleft(img, *TOP_RECT, BOX_SIZE)
    single_crop = crop_by_topleft(img, *BOTTOM_SINGLE_RECT, BOX_SIZE)
    left_crop = crop_by_topleft(img, *BOTTOM_LEFT_RECT, BOX_SIZE)
    right_crop = crop_by_topleft(img, *BOTTOM_RIGHT_RECT, BOX_SIZE)

    has_top = slot_has_item(top_crop, "top")
    has_single = slot_has_item(single_crop, "bottom_single")
    has_left = slot_has_item(left_crop, "bottom_left")
    has_right = slot_has_item(right_crop, "bottom_right")

    print(f"top={has_top}, single={has_single}, left={has_left}, right={has_right}")

    if has_top and (has_left or has_right):
        return "3"
    if has_top and has_single:
        return "2"
    if has_top:
        return "1"
    return "0"


def get_rects_by_mode(mode):
    if mode == "1":
        return [("top", TOP_RECT)]

    if mode == "2":
        return [
            ("top", TOP_RECT),
            ("bottom_single", BOTTOM_SINGLE_RECT),
        ]

    if mode == "3":
        return [
            ("top", TOP_RECT),
            ("bottom_left", BOTTOM_LEFT_RECT),
            ("bottom_right", BOTTOM_RIGHT_RECT),
        ]

    return []


def draw_debug(img, rects, detected_mode, labels=None):
    debug = img.copy()

    for i, (name, (x1, y1)) in enumerate(rects):
        x2 = x1 + BOX_SIZE
        y2 = y1 + BOX_SIZE

        cv2.rectangle(debug, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.circle(debug, (x1, y1), 4, (0, 0, 255), -1)

        text = f"{name} ({x1},{y1})"
        if labels and i < len(labels):
            text = f"{name}:{labels[i]}"

        cv2.putText(
            debug,
            text,
            (x1, max(20, y1 - 8)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (255, 255, 255),
            1,
            cv2.LINE_AA
        )

    cv2.putText(
        debug,
        f"detected_mode = {detected_mode}",
        (30, 50),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.0,
        (0, 255, 255),
        2,
        cv2.LINE_AA
    )

    return debug


def load_database_from_folder(folder):
    db = []

    if not os.path.isdir(folder):
        return db

    for file in os.listdir(folder):
        if not file.lower().endswith(IMAGE_EXT):
            continue

        path = os.path.join(folder, file)
        img = imread_korean(path)
        if img is None:
            continue

        img = preprocess_for_match(img, MATCH_SIZE)
        name = os.path.splitext(file)[0]

        db.append({
            "name": name,
            "img": img,
        })

    return db


def calc_score(img1, img2):
    img1 = preprocess_for_match(img1, MATCH_SIZE)
    img2 = preprocess_for_match(img2, MATCH_SIZE)

    diff_rgb = cv2.absdiff(img1, img2)
    score_rgb = float(np.mean(diff_rgb))

    gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
    diff_gray = cv2.absdiff(gray1, gray2)
    score_gray = float(np.mean(diff_gray))

    edge1 = cv2.Canny(gray1, 80, 160)
    edge2 = cv2.Canny(gray2, 80, 160)
    diff_edge = cv2.absdiff(edge1, edge2)
    score_edge = float(np.mean(diff_edge)) / 8.0

    center1 = get_center_crop(img1, 0.56)
    center2 = get_center_crop(img2, 0.56)
    diff_center = cv2.absdiff(center1, center2)
    score_center = float(np.mean(diff_center))

    total = (
        score_rgb * 0.33
        + score_gray * 0.27
        + score_edge * 0.15
        + score_center * 0.25
    )
    return total


def match_one(query_img, db):
    query_img = preprocess_for_match(query_img, MATCH_SIZE)

    best = None
    best_score = 1e18

    for item in db:
        score = calc_score(query_img, item["img"])
        if score < best_score:
            best_score = score
            best = item

    if best is None:
        return None, best_score

    if best_score > MATCH_FAIL_SCORE:
        return None, best_score

    return best, best_score


def build_result_string(mode, matched_map):
    top_name = matched_map.get("top", "")

    if not top_name or top_name == "매칭실패":
        return "매칭실패"

    materials = []

    if mode == "2":
        bottom_single = matched_map.get("bottom_single", "")
        if bottom_single and bottom_single != "매칭실패":
            materials.append(bottom_single)

    elif mode == "3":
        bottom_left = matched_map.get("bottom_left", "")
        bottom_right = matched_map.get("bottom_right", "")

        if bottom_left and bottom_left != "매칭실패":
            materials.append(bottom_left)
        if bottom_right and bottom_right != "매칭실패":
            materials.append(bottom_right)

    return f"{top_name}{{{','.join(materials)}}}"


def process_image(img, base_name, top_db, bottom_db):
    detected_mode = detect_structure(img)
    print(f"자동 판별 구조: {detected_mode}")

    rects = get_rects_by_mode(detected_mode)

    if not rects:
        debug = draw_debug(img, rects, detected_mode, [])
        debug_path = os.path.join(OUTPUT_DIR, f"{base_name}_debug.png")
        imwrite_korean(debug_path, debug)
        print("❌ 구조 없음")
        return 0, "매칭실패"

    matched_map = {}
    debug_labels = []

    for name, (x1, y1) in rects:
        crop = crop_by_topleft(img, x1, y1, BOX_SIZE)

        crop_path = os.path.join(OUTPUT_DIR, f"{base_name}_{name}.png")
        imwrite_korean(crop_path, crop)

        if name == "top":
            best, score = match_one(crop, top_db)
        else:
            best, score = match_one(crop, bottom_db)

        if best is None:
            item_name = "매칭실패"
            print(f"{name:<14} -> 매칭실패 (score={score:.2f})")
        else:
            item_name = best["name"]
            print(f"{name:<14} -> {item_name} (score={score:.2f})")

        matched_map[name] = item_name
        debug_labels.append(item_name)

    result_text = build_result_string(detected_mode, matched_map)

    debug = draw_debug(img, rects, detected_mode, debug_labels)
    debug_path = os.path.join(OUTPUT_DIR, f"{base_name}_debug.png")
    imwrite_korean(debug_path, debug)

    return len(rects), result_text


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if not os.path.isdir(INPUT_DIR):
        print("❌ 자료 폴더 없음")
        return

    top_db = load_database_from_folder(TOP_DB_DIR)
    bottom_db = load_database_from_folder(BOTTOM_DB_DIR)

    if not top_db:
        print("❌ 중간탬 DB 이미지 없음")
        return

    if not bottom_db:
        print("❌ 기본템 DB 이미지 없음")
        return

    print(f"중간탬 DB 로드 완료: {len(top_db)}개")
    print(f"기본템 DB 로드 완료: {len(bottom_db)}개")

    files = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith(IMAGE_EXT)]
    files.sort()

    if not files:
        print("❌ 이미지 없음")
        return

    total_imgs = 0
    total_crops = 0
    all_lines = []

    for file in files:
        path = os.path.join(INPUT_DIR, file)
        img = imread_korean(path)

        print(f"\n처리 중: {file}")

        if img is None:
            print("❌ 이미지 읽기 실패")
            continue

        base_name = os.path.splitext(file)[0]
        count, result_text = process_image(img, base_name, top_db, bottom_db)

        total_imgs += 1
        total_crops += count
        all_lines.append(result_text)

        print(f"-> 저장 개수: {count}")
        print(f"-> 결과: {result_text}")

    with open(RESULT_TXT_PATH, "w", encoding="utf-8-sig") as f:
        f.write("\n".join(all_lines))

    print("\n완료")
    print(f"처리 이미지 수: {total_imgs}")
    print(f"총 크롭 저장 수: {total_crops}")
    print(f"결과 폴더: {OUTPUT_DIR}")
    print(f"결과 텍스트: {RESULT_TXT_PATH}")


if __name__ == "__main__":
    main()