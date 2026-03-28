import cv2
import numpy as np
from pathlib import Path

from src.utils.file_utils import ensure_dir
from src.utils.image_io import save_image


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
    canvas[y:y+nh, x:x+nw] = resized
    return canvas


def bgra_to_preview(img):
    if img is None:
        return None

    if len(img.shape) == 2:
        return cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

    if img.shape[2] == 4:
        bgr = img[:, :, :3].copy()
        alpha = img[:, :, 3]
        out = np.full_like(bgr, 255)
        out[alpha > 0] = bgr[alpha > 0]
        return out

    return img.copy()


def make_pair_image(query_img, cand_img, score, query_name, cand_name):
    q = bgra_to_preview(query_img)
    c = bgra_to_preview(cand_img)

    panel_size = (180, 180)
    left = resize_keep(q, panel_size)
    right = resize_keep(c, panel_size)

    margin = 24
    top_h = 72
    bottom = 20

    w = panel_size[0] * 2 + margin * 3
    h = top_h + panel_size[1] + bottom

    canvas = np.full((h, w, 3), 255, dtype=np.uint8)

    cv2.putText(canvas, f"score: {score:.4f}", (margin, 28),
                cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 0), 2, cv2.LINE_AA)

    cv2.putText(canvas, query_name, (margin, 58),
                cv2.FONT_HERSHEY_SIMPLEX, 0.52, (0, 0, 0), 1, cv2.LINE_AA)

    cv2.putText(canvas, cand_name, (margin * 2 + panel_size[0], 58),
                cv2.FONT_HERSHEY_SIMPLEX, 0.52, (0, 0, 0), 1, cv2.LINE_AA)

    y = top_h
    x1 = margin
    x2 = margin * 2 + panel_size[0]

    canvas[y:y+panel_size[1], x1:x1+panel_size[0]] = left
    canvas[y:y+panel_size[1], x2:x2+panel_size[0]] = right

    cv2.rectangle(canvas, (x1, y), (x1 + panel_size[0], y + panel_size[1]), (0, 0, 0), 2)
    cv2.rectangle(canvas, (x2, y), (x2 + panel_size[0], y + panel_size[1]), (0, 0, 0), 2)

    return canvas


def save_pair_debug(output_path: Path, query_img, cand_img, score, query_name, cand_name):
    ensure_dir(output_path.parent)
    pair = make_pair_image(query_img, cand_img, score, query_name, cand_name)
    save_image(output_path, pair)