import os
import cv2
import numpy as np

from .config import TEMPLATE_DIR, ICON_SIZE, EMPTY_SCORE_THRESHOLD
from .models import SlotMatch
from .image_utils import preprocess_icon, cosine_similarity, mean_brightness


def imread_korean(path):
    try:
        data = np.fromfile(path, dtype=np.uint8)
        if data.size == 0:
            return None
        img = cv2.imdecode(data, cv2.IMREAD_COLOR)
        return img
    except Exception:
        return None


class SlotDetector:
    def __init__(self, template_dir=TEMPLATE_DIR):
        self.template_dir = template_dir
        self.templates = self._load_templates()

    def _load_templates(self):
        templates = {}

        print(f"[slot_detector] template_dir = {self.template_dir}")
        print(f"[slot_detector] exists = {os.path.isdir(self.template_dir)}")

        if not os.path.isdir(self.template_dir):
            print(f"[경고] 폴더 없음: {self.template_dir}")
            return templates

        exts = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}

        for name in os.listdir(self.template_dir):
            path = os.path.join(self.template_dir, name)

            if not os.path.isfile(path):
                continue

            base, ext = os.path.splitext(name)
            if ext.lower() not in exts:
                continue

            img = imread_korean(path)
            if img is None:
                print(f"[실패] 이미지 읽기 실패: {path}")
                continue

            proc = preprocess_icon(img, ICON_SIZE)
            if proc is not None:
                templates[base] = proc

        print(f"[slot_detector] templates loaded: {len(templates)}")
        return templates

    def is_empty_slot(self, crop):
        return mean_brightness(crop) < 8.0

    def detect_slot(self, crop):
        if crop is None:
            return SlotMatch(name="", score=0.0, is_empty=True)

        if self.is_empty_slot(crop):
            return SlotMatch(name="", score=0.0, is_empty=True)

        proc = preprocess_icon(crop, ICON_SIZE)
        if proc is None:
            return SlotMatch(name="", score=0.0, is_empty=True)

        best_name = ""
        best_score = -1.0

        for name, tmpl in self.templates.items():
            score = cosine_similarity(proc, tmpl)
            if score > best_score:
                best_score = score
                best_name = name

        if best_score < EMPTY_SCORE_THRESHOLD:
            return SlotMatch(name="", score=best_score, is_empty=True)

        return SlotMatch(name=best_name, score=best_score, is_empty=False)

    def detect_many(self, crops):
        return [self.detect_slot(crop) for crop in crops]