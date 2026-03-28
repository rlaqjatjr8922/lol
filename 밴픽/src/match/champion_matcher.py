import cv2
from pathlib import Path

from config.paths import CHAMPION_CANONICAL_DIR
from src.utils.image_io import list_images, read_image


def match_champion(query_img):
    templates = list_images(CHAMPION_CANONICAL_DIR)
    if not templates:
        return None, 0.0

    query_gray = cv2.cvtColor(query_img, cv2.COLOR_BGR2GRAY)

    best_name = None
    best_score = -1.0

    for template_path in templates:
        template = read_image(template_path)
        if template is None:
            continue

        # canonical 이미지를 crop 크기에 맞춤
        resized = cv2.resize(template, (query_img.shape[1], query_img.shape[0]))
        template_gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)

        result = cv2.matchTemplate(query_gray, template_gray, cv2.TM_CCOEFF_NORMED)
        score = float(result.max())

        if score > best_score:
            best_score = score
            best_name = template_path.stem

    return best_name, best_score