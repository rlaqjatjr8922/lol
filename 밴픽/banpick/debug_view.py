import os
import cv2

from .config import DEBUG_DIR


def draw_boxes(img, rois, color=(0, 255, 0)):
    out = img.copy()
    for box in rois:
        x, y, w, h = box
        cv2.rectangle(out, (x, y), (x + w, y + h), color, 2)
    return out


def save_debug_image(name, img):
    os.makedirs(DEBUG_DIR, exist_ok=True)
    path = os.path.join(DEBUG_DIR, name)
    cv2.imwrite(path, img)