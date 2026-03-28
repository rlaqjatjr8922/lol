import cv2
import numpy as np

from config.roi_config import ROI_CONFIG, USE_SCALED_ROI, BASE_W, BASE_H
from config.paths import ALLY_PICKS_DIR, ENEMY_PICKS_DIR, DEBUG_PREVIEW_DIR
from src.utils.file_utils import ensure_dir
from src.utils.image_io import save_image


def scale_roi(roi, img_shape):
    ih, iw = img_shape[:2]
    sx = iw / float(BASE_W)
    sy = ih / float(BASE_H)
    x, y, w, h = roi
    return (
        int(round(x * sx)),
        int(round(y * sy)),
        max(1, int(round(w * sx))),
        max(1, int(round(h * sy))),
    )


def scaled_roi_config(img):
    return {key: [scale_roi(roi, img.shape) for roi in rois] for key, rois in ROI_CONFIG.items()}


def crop_roi(img, roi):
    x, y, w, h = roi
    ih, iw = img.shape[:2]
    x = max(0, min(iw - 1, x))
    y = max(0, min(ih - 1, y))
    w = max(1, min(iw - x, w))
    h = max(1, min(ih - y, h))
    return img[y:y + h, x:x + w].copy()


def draw_roi_preview(img, roi_config):
    preview = img.copy()
    colors = {
        'ally_picks': (0, 255, 255),
        'enemy_picks': (255, 0, 255),
    }
    for group_name, roi_list in roi_config.items():
        color = colors.get(group_name, (255, 255, 255))
        for idx, roi in enumerate(roi_list, 1):
            x, y, w, h = roi
            cv2.rectangle(preview, (x, y), (x + w, y + h), color, 2)
            cv2.putText(preview, f'{group_name}_{idx}', (x, max(15, y - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.42, color, 1, cv2.LINE_AA)
    return preview


def make_circle_transparent_crop(crop):
    h, w = crop.shape[:2]
    bgra = cv2.cvtColor(crop, cv2.COLOR_BGR2BGRA)
    mask = np.zeros((h, w), dtype=np.uint8)
    cx = w // 2
    cy = h // 2
    r = int(min(h, w) * 0.44)
    cv2.circle(mask, (cx, cy), r, 255, -1)
    bgra[:, :, 3] = mask
    bgra[mask == 0] = (0, 0, 0, 0)
    return bgra


def export_slots_from_image(img, image_stem: str, original_name: str):
    cfg = scaled_roi_config(img) if USE_SCALED_ROI else ROI_CONFIG

    group_to_dir = {
        'ally_picks': ALLY_PICKS_DIR,
        'enemy_picks': ENEMY_PICKS_DIR,
    }

    save_count = 0
    for group_name, roi_list in cfg.items():
        out_dir = group_to_dir[group_name]
        ensure_dir(out_dir)
        for idx, roi in enumerate(roi_list, 1):
            crop = crop_roi(img, roi)
            transparent_crop = make_circle_transparent_crop(crop)
            save_path = out_dir / f'{image_stem}__{group_name}_{idx}.png'
            if save_image(save_path, transparent_crop):
                save_count += 1

    ensure_dir(DEBUG_PREVIEW_DIR)
    preview = draw_roi_preview(img, cfg)
    save_image(DEBUG_PREVIEW_DIR / original_name, preview)
    return save_count
