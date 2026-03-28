import cv2
import numpy as np

from config.paths import CHAMPION_CANONICAL_DIR
from src.utils.image_io import list_images, read_image

MATCH_SIZE = 112
MASK_RADIUS_RATIO = 0.42
BOTTOM_CUT_RATIO = 0.86

W_GRAY = 0.50
W_HIST = 0.25
W_EDGE = 0.15
W_CENTER = 0.10

MATCH_THRESHOLD = 0.45


def alpha_to_bgr_and_mask(img):
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
    return img[y1:y1 + s, x1:x1 + s], mask[y1:y1 + s, x1:x1 + s]


def make_circle_mask(size):
    mask = np.zeros((size, size), dtype=np.uint8)
    c = size // 2
    r = int(size * MASK_RADIUS_RATIO)
    cv2.circle(mask, (c, c), r, 255, -1)

    cut_y = int(size * BOTTOM_CUT_RATIO)
    mask[cut_y:, :] = 0
    return mask


def preprocess_icon_from_image(img):
    if img is None:
        return None

    bgr, alpha_mask = alpha_to_bgr_and_mask(img)
    if bgr is None:
        return None

    bgr, alpha_mask = center_crop_square(bgr, alpha_mask)

    bgr = cv2.resize(bgr, (MATCH_SIZE, MATCH_SIZE), interpolation=cv2.INTER_AREA)
    alpha_mask = cv2.resize(alpha_mask, (MATCH_SIZE, MATCH_SIZE), interpolation=cv2.INTER_NEAREST)

    circle_mask = make_circle_mask(MATCH_SIZE)
    final_mask = cv2.bitwise_and(alpha_mask, circle_mask)

    if np.count_nonzero(final_mask) < (MATCH_SIZE * MATCH_SIZE * 0.10):
        final_mask = circle_mask

    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    edges = cv2.Canny(gray, 80, 160)

    return {
        "bgr": bgr,
        "gray": gray,
        "hsv": hsv,
        "edges": edges,
        "mask": final_mask,
    }


def masked_corr(img1, img2, mask):
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
    inner[pad:s - pad, pad:s - pad] = 255
    return cv2.bitwise_and(base_mask, inner)


def score_pair(q, c):
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


def match_champion(query_img):
    qicon = preprocess_icon_from_image(query_img)
    if qicon is None:
        return "Unknown", 0.0, None, None

    templates = list_images(CHAMPION_CANONICAL_DIR)
    if not templates:
        return "Unknown", 0.0, None, None

    best_name = "Unknown"
    best_score = -999.0
    best_raw = None
    best_path = None

    for template_path in templates:
        raw = read_image(template_path)
        cicon = preprocess_icon_from_image(raw)
        if cicon is None:
            continue

        score = score_pair(qicon, cicon)
        if score > best_score:
            best_score = score
            best_name = template_path.stem
            best_raw = raw
            best_path = template_path

    if best_score < MATCH_THRESHOLD:
        return "Unknown", best_score, best_raw, best_path

    return best_name, best_score, best_raw, best_path