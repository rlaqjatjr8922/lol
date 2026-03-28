import os
import csv
import cv2
import numpy as np

# =========================
# 경로
# =========================
QUERY_DIR = r"C:\Users\gimbe\OneDrive\Desktop\lol_project\dataset\자료"
CANDIDATE_DIR = r"C:\Users\gimbe\OneDrive\Desktop\lol_project\dataset\픽"
OUTPUT_DIR = r"C:\Users\gimbe\OneDrive\Desktop\lol_project\dataset\결과"

PAIR_DIR = os.path.join(OUTPUT_DIR, "pairs_v2")
CSV_PATH = os.path.join(OUTPUT_DIR, "match_results_v2.csv")

IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp", ".bmp")

# =========================
# 매칭 설정
# =========================
MATCH_SIZE = 112

# 원형 안쪽만 보도록 마스크 반지름
MASK_RADIUS_RATIO = 0.42

# 아래쪽 작은 문양/테두리 영향 줄이기
BOTTOM_CUT_RATIO = 0.86

# 최종 점수 가중치
W_GRAY = 0.50
W_HIST = 0.25
W_EDGE = 0.15
W_CENTER = 0.10


# =========================
# 파일 입출력
# =========================
def is_image_file(path: str) -> bool:
    return path.lower().endswith(IMAGE_EXTS)


def list_images(root: str):
    results = []
    for base, _, files in os.walk(root):
        for name in files:
            full = os.path.join(base, name)
            if is_image_file(full):
                results.append(full)
    return sorted(results)


def imread_korean(path: str):
    try:
        data = np.fromfile(path, dtype=np.uint8)
        if data.size == 0:
            return None
        return cv2.imdecode(data, cv2.IMREAD_UNCHANGED)
    except Exception:
        return None


def imwrite_korean(path: str, img) -> bool:
    try:
        folder = os.path.dirname(path)
        if folder:
            os.makedirs(folder, exist_ok=True)

        ext = os.path.splitext(path)[1].lower()
        if ext not in [".png", ".jpg", ".jpeg", ".webp", ".bmp"]:
            ext = ".png"
            path += ".png"

        ok, buf = cv2.imencode(ext, img)
        if not ok:
            return False

        buf.tofile(path)
        return True
    except Exception:
        return False


# =========================
# 이미지 보정
# =========================
def alpha_to_bgr_and_mask(img):
    """
    img:
      - BGR
      - BGRA
      - Gray
    return:
      bgr, mask(0/255)
    """
    if img is None:
        return None, None

    if len(img.shape) == 2:
        bgr = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        mask = np.full(img.shape[:2], 255, dtype=np.uint8)
        return bgr, mask

    if img.shape[2] == 4:
        bgr = img[:, :, :3].copy()
        alpha = img[:, :, 3]
        mask = np.where(alpha > 8, 255, 0).astype(np.uint8)
        return bgr, mask

    bgr = img[:, :, :3].copy()
    mask = np.full(img.shape[:2], 255, dtype=np.uint8)
    return bgr, mask


def center_crop_square(img, mask):
    h, w = img.shape[:2]
    s = min(h, w)
    y1 = (h - s) // 2
    x1 = (w - s) // 2
    return img[y1:y1+s, x1:x1+s], mask[y1:y1+s, x1:x1+s]


def make_circle_mask(size):
    mask = np.zeros((size, size), dtype=np.uint8)
    c = size // 2
    r = int(size * MASK_RADIUS_RATIO)
    cv2.circle(mask, (c, c), r, 255, -1)

    # 아래쪽 작은 문양/테두리 영향 제거
    cut_y = int(size * BOTTOM_CUT_RATIO)
    mask[cut_y:, :] = 0
    return mask


def preprocess_icon(path: str):
    raw = imread_korean(path)
    if raw is None:
        return None

    bgr, alpha_mask = alpha_to_bgr_and_mask(raw)
    if bgr is None:
        return None

    bgr, alpha_mask = center_crop_square(bgr, alpha_mask)

    bgr = cv2.resize(bgr, (MATCH_SIZE, MATCH_SIZE), interpolation=cv2.INTER_AREA)
    alpha_mask = cv2.resize(alpha_mask, (MATCH_SIZE, MATCH_SIZE), interpolation=cv2.INTER_NEAREST)

    circle_mask = make_circle_mask(MATCH_SIZE)

    # 투명 PNG면 alpha와 원형 마스크를 둘 다 반영
    final_mask = cv2.bitwise_and(alpha_mask, circle_mask)

    # 마스크가 너무 작으면 원형 마스크만 사용
    if np.count_nonzero(final_mask) < (MATCH_SIZE * MATCH_SIZE * 0.10):
        final_mask = circle_mask

    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    edges = cv2.Canny(gray, 80, 160)

    return {
        "path": path,
        "bgr": bgr,
        "gray": gray,
        "hsv": hsv,
        "edges": edges,
        "mask": final_mask
    }


# =========================
# 특징 추출 / 유사도
# =========================
def masked_corr(img1, img2, mask):
    """
    mask가 켜진 부분만 가지고 정규화 상관계수 계산
    """
    idx = mask > 0
    a = img1[idx].astype(np.float32)
    b = img2[idx].astype(np.float32)

    if len(a) < 50:
        return -1.0

    a = a - a.mean()
    b = b - b.mean()

    da = np.linalg.norm(a)
    db = np.linalg.norm(b)

    if da < 1e-6 or db < 1e-6:
        return -1.0

    return float(np.dot(a, b) / (da * db))


def masked_hist_score(hsv1, hsv2, mask):
    """
    원형 안쪽 HSV 히스토그램 비교
    """
    hist1 = cv2.calcHist([hsv1], [0, 1], mask, [24, 16], [0, 180, 0, 256])
    hist2 = cv2.calcHist([hsv2], [0, 1], mask, [24, 16], [0, 180, 0, 256])

    if hist1 is None or hist2 is None:
        return 0.0

    hist1 = cv2.normalize(hist1, None).flatten()
    hist2 = cv2.normalize(hist2, None).flatten()

    return float(cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL))


def center_region_mask(base_mask):
    s = base_mask.shape[0]
    inner = np.zeros_like(base_mask)
    pad = int(s * 0.18)
    inner[pad:s-pad, pad:s-pad] = 255
    return cv2.bitwise_and(base_mask, inner)


def score_pair(q, c):
    # 두 이미지 공통으로 켜진 부분만 비교
    common_mask = cv2.bitwise_and(q["mask"], c["mask"])

    if np.count_nonzero(common_mask) < 400:
        return -1.0

    gray_score = masked_corr(q["gray"], c["gray"], common_mask)
    edge_score = masked_corr(q["edges"], c["edges"], common_mask)
    hist_score = masked_hist_score(q["hsv"], c["hsv"], common_mask)

    center_mask = center_region_mask(common_mask)
    center_score = masked_corr(q["gray"], c["gray"], center_mask)
    if center_score < -0.5:
        center_score = -0.5

    score = (
        gray_score * W_GRAY +
        hist_score * W_HIST +
        edge_score * W_EDGE +
        center_score * W_CENTER
    )
    return float(score)


# =========================
# 결과 이미지 생성
# =========================
def resize_keep(img, size):
    tw, th = size
    h, w = img.shape[:2]
    scale = min(tw / w, th / h)
    nw = max(1, int(round(w * scale)))
    nh = max(1, int(round(h * scale)))
    resized = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_AREA)

    canvas = np.full((th, tw, 3), 255, dtype=np.uint8)
    x = (tw - nw) // 2
    y = (th - nh) // 2
    canvas[y:y + nh, x:x + nw] = resized
    return canvas


def preview_bgr(icon):
    bgr = icon["bgr"].copy()
    mask = icon["mask"]
    out = np.full_like(bgr, 255)
    out[mask > 0] = bgr[mask > 0]
    return out


def make_pair_image(q, c, score):
    panel_size = (180, 180)
    left = resize_keep(preview_bgr(q), panel_size)
    right = resize_keep(preview_bgr(c), panel_size)

    margin = 24
    top_h = 58
    label_h = 26
    bottom = 18

    w = panel_size[0] * 2 + margin * 3
    h = top_h + label_h + panel_size[1] + bottom

    canvas = np.full((h, w, 3), 255, dtype=np.uint8)

    score_text = f"score: {score:.4f}"
    cv2.putText(canvas, score_text, (margin, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.78, (0, 0, 0), 2, cv2.LINE_AA)

    qx = margin
    mx = margin * 2 + panel_size[0]
    iy = top_h + label_h

    cv2.putText(canvas, "query", (qx, top_h + 10), cv2.FONT_HERSHEY_SIMPLEX, 0.68, (0, 0, 0), 2, cv2.LINE_AA)
    cv2.putText(canvas, "best match", (mx, top_h + 10), cv2.FONT_HERSHEY_SIMPLEX, 0.68, (0, 0, 0), 2, cv2.LINE_AA)

    canvas[iy:iy+panel_size[1], qx:qx+panel_size[0]] = left
    canvas[iy:iy+panel_size[1], mx:mx+panel_size[0]] = right

    cv2.rectangle(canvas, (qx, iy), (qx + panel_size[0], iy + panel_size[1]), (0, 0, 0), 2)
    cv2.rectangle(canvas, (mx, iy), (mx + panel_size[0], iy + panel_size[1]), (0, 0, 0), 2)

    return canvas


# =========================
# 메인
# =========================
def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(PAIR_DIR, exist_ok=True)

    query_paths = list_images(QUERY_DIR)
    cand_paths = list_images(CANDIDATE_DIR)

    if not query_paths:
        print("[오류] 자료 폴더에 이미지가 없습니다.")
        print("QUERY_DIR =", QUERY_DIR)
        return

    if not cand_paths:
        print("[오류] 픽 폴더에 이미지가 없습니다.")
        print("CANDIDATE_DIR =", CANDIDATE_DIR)
        return

    print(f"[INFO] query images: {len(query_paths)}")
    print(f"[INFO] candidate images: {len(cand_paths)}")

    # 후보 전처리 캐시
    candidate_icons = []
    for path in cand_paths:
        icon = preprocess_icon(path)
        if icon is not None:
            candidate_icons.append(icon)

    print(f"[INFO] usable candidate images: {len(candidate_icons)}")

    if not candidate_icons:
        print("[오류] 비교 가능한 후보 이미지가 없습니다.")
        return

    rows = []

    for qpath in query_paths:
        qicon = preprocess_icon(qpath)
        if qicon is None:
            print(f"[건너뜀] 읽기 실패: {qpath}")
            continue

        best_icon = None
        best_score = -999.0

        for cicon in candidate_icons:
            score = score_pair(qicon, cicon)
            if score > best_score:
                best_score = score
                best_icon = cicon

        if best_icon is None:
            print(f"[실패] 매칭 실패: {qpath}")
            continue

        qname = os.path.splitext(os.path.basename(qpath))[0]
        bname = os.path.basename(best_icon["path"])

        pair_img = make_pair_image(qicon, best_icon, best_score)
        pair_path = os.path.join(PAIR_DIR, f"{qname}__PAIR.png")
        imwrite_korean(pair_path, pair_img)

        rows.append([qpath, best_icon["path"], f"{best_score:.6f}"])
        print(f"[MATCH] {os.path.basename(qpath)} -> {bname} ({best_score:.4f})")

    with open(CSV_PATH, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["query_image", "best_match", "score"])
        writer.writerows(rows)

    print()
    print("[DONE]")
    print("PAIR_DIR =", PAIR_DIR)
    print("CSV_PATH =", CSV_PATH)


if __name__ == "__main__":
    main()
