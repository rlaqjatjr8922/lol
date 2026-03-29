import cv2
import numpy as np

from config.paths import ROLE_TEMPLATE_DIR
from src.utils.image_io import list_images, read_image

ROLE_MATCH_SIZE = 112
ROLE_THRESHOLD = 0.45


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
    return img[y1:y1+s, x1:x1+s], mask[y1:y1+s, x1:x1+s]


def preprocess_role_icon(img):
    if img is None:
        return None

    bgr, alpha_mask = alpha_to_bgr_and_mask(img)
    if bgr is None:
        return None

    bgr, alpha_mask = center_crop_square(bgr, alpha_mask)
    bgr = cv2.resize(bgr, (ROLE_MATCH_SIZE, ROLE_MATCH_SIZE), interpolation=cv2.INTER_AREA)
    alpha_mask = cv2.resize(alpha_mask, (ROLE_MATCH_SIZE, ROLE_MATCH_SIZE), interpolation=cv2.INTER_NEAREST)

    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 80, 160)

    # 원형 마스크
    mask = np.zeros((ROLE_MATCH_SIZE, ROLE_MATCH_SIZE), dtype=np.uint8)
    c = ROLE_MATCH_SIZE // 2
    r = int(ROLE_MATCH_SIZE * 0.42)
    cv2.circle(mask, (c, c), r, 255, -1)

    final_mask = cv2.bitwise_and(mask, alpha_mask)

    if np.count_nonzero(final_mask) < (ROLE_MATCH_SIZE * ROLE_MATCH_SIZE * 0.10):
        final_mask = mask

    return {
        "bgr": bgr,
        "gray": gray,
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


def score_pair(q, c):
    common_mask = cv2.bitwise_and(q["mask"], c["mask"])

    if np.count_nonzero(common_mask) < 300:
        return -1.0

    gray_score = masked_corr(q["gray"], c["gray"], common_mask)
    edge_score = masked_corr(q["edges"], c["edges"], common_mask)

    score = gray_score * 0.65 + edge_score * 0.35
    return float(score)


def is_role_icon(img):
    """
    단색/저디테일이면 역할 아이콘일 가능성이 높음
    """
    if img is None:
        return False

    if len(img.shape) == 3 and img.shape[2] == 4:
        bgr = img[:, :, :3]
    elif len(img.shape) == 2:
        bgr = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    else:
        bgr = img

    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    std = float(np.std(gray))

    edges = cv2.Canny(gray, 80, 160)
    edge_ratio = float(np.count_nonzero(edges)) / float(edges.size)

    # 역할 아이콘은 대개 단색 + 엣지 적당
    if std < 28 and edge_ratio < 0.18:
        return True

    return False


def match_role(query_img):
    qicon = preprocess_role_icon(query_img)
    if qicon is None:
        return "UnknownRole", 0.0, None, None

    templates = list_images(ROLE_TEMPLATE_DIR)
    if not templates:
        return "UnknownRole", 0.0, None, None

    best_name = "UnknownRole"
    best_score = -999.0
    best_raw = None
    best_path = None

    for template_path in templates:
        raw = read_image(template_path)
        cicon = preprocess_role_icon(raw)
        if cicon is None:
            continue

        score = score_pair(qicon, cicon)
        if score > best_score:
            best_score = score
            best_name = template_path.stem
            best_raw = raw
            best_path = template_path

    if best_score < ROLE_THRESHOLD:
        return "UnknownRole", best_score, best_raw, best_path

    return best_name, best_score, best_raw, best_path