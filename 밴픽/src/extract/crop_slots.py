import cv2
from pathlib import Path

from config.roi_config import ROI_CONFIG
from config.paths import (
    DEBUG_PREVIEW_DIR,
    CHAMPION_HOVER_CROP_DIR,
    CHAMPION_PICK_CROP_DIR,
    CHAMPION_BAN_CROP_DIR,
    ROLE_CROP_DIR,
)
from src.utils.file_utils import ensure_dir
from src.utils.image_io import save_image


def crop_roi(image, roi):
    x, y, w, h = roi
    return image[y:y+h, x:x+w]


def draw_rois(image, groups):
    preview = image.copy()
    colors = {
        "ally_hover_slots": (0, 255, 255),
        "ally_pick_slots": (0, 255, 0),
        "ally_ban_slots": (0, 0, 255),
        "role_slots": (255, 0, 0),
    }
    for group_name, rois in groups.items():
        color = colors.get(group_name, (255, 255, 255))
        for idx, (x, y, w, h) in enumerate(rois, start=1):
            cv2.rectangle(preview, (x, y), (x + w, y + h), color, 2)
            cv2.putText(
                preview,
                f"{group_name}_{idx}",
                (x, y - 6),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                color,
                1,
                cv2.LINE_AA,
            )
    return preview


def save_group_crops(image, image_stem: str, group_name: str, output_dir: Path):
    ensure_dir(output_dir)
    rois = ROI_CONFIG[group_name]
    for idx, roi in enumerate(rois, start=1):
        cropped = crop_roi(image, roi)
        out_name = f"{image_stem}_{group_name}_{idx:02d}.png"
        save_image(output_dir / out_name, cropped)


def process_pregame_image(image, image_stem: str):
    ensure_dir(DEBUG_PREVIEW_DIR)
    preview = draw_rois(image, ROI_CONFIG)
    save_image(DEBUG_PREVIEW_DIR / f"{image_stem}_preview.png", preview)
    save_group_crops(image, image_stem, "ally_hover_slots", CHAMPION_HOVER_CROP_DIR)
    save_group_crops(image, image_stem, "ally_pick_slots", CHAMPION_PICK_CROP_DIR)
    save_group_crops(image, image_stem, "ally_ban_slots", CHAMPION_BAN_CROP_DIR)
    save_group_crops(image, image_stem, "role_slots", ROLE_CROP_DIR)
