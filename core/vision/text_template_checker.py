import cv2
import numpy as np
from pathlib import Path


class TextTemplateChecker:
    def __init__(self, threshold=0.90):
        self.threshold = threshold
        self.last_debug = None

    def _read_image_unicode(self, path):
        path = str(path)
        data = np.fromfile(path, dtype=np.uint8)

        if data.size == 0:
            return None

        return cv2.imdecode(data, cv2.IMREAD_COLOR)

    def _preprocess(self, gray):
        h, w = gray.shape[:2]

        if h == 0 or w == 0:
            return None

        resized = cv2.resize(
            gray,
            (max(1, w * 4), max(1, h * 4)),
            interpolation=cv2.INTER_CUBIC
        )
        blur = cv2.GaussianBlur(resized, (3, 3), 0)
        _, th = cv2.threshold(
            blur,
            0,
            255,
            cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )
        return th

    def _compare_images(self, roi_proc, template_proc):
        if roi_proc is None or template_proc is None:
            return -1.0

        th, tw = template_proc.shape[:2]

        if th == 0 or tw == 0:
            return -1.0

        resized_roi = cv2.resize(
            roi_proc,
            (tw, th),
            interpolation=cv2.INTER_AREA
        )

        result = cv2.matchTemplate(
            resized_roi,
            template_proc,
            cv2.TM_CCOEFF_NORMED
        )

        return float(result[0][0])

    def check(self, roi, template_paths, threshold=None):
        self.last_debug = None

        if roi is None:
            return False, None, -1.0

        if not isinstance(template_paths, list) or not template_paths:
            return False, None, -1.0

        try:
            roi_gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        except Exception:
            return False, None, -1.0

        roi_proc = self._preprocess(roi_gray)
        base_dir = Path(__file__).resolve().parents[2]
        threshold = self.threshold if threshold is None else threshold

        matched_items = []

        best_score = -1.0
        best_name = None
        best_template_image = None

        for template_path in template_paths:
            full_template_path = base_dir / Path(template_path)

            template = self._read_image_unicode(full_template_path)
            if template is None:
                print(f"[TemplateChecker] template load 실패: {full_template_path}")
                continue

            try:
                template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
            except Exception as e:
                print(f"[TemplateChecker] template cvtColor 실패: {full_template_path}, {e}")
                continue

            template_proc = self._preprocess(template_gray)
            if template_proc is None:
                print(f"[TemplateChecker] template preprocess 실패: {full_template_path}, shape={template_gray.shape}")

            score = self._compare_images(roi_proc, template_proc)
            print(f"[TemplateChecker] template={full_template_path.name}, score={score:.3f}, roi_proc={'OK' if roi_proc is not None else 'None'}, template_proc={'OK' if template_proc is not None else 'None'}")

            if score > best_score:
                best_score = score
                best_name = full_template_path.name
                best_template_image = template.copy()

            if score >= threshold:
                matched_items.append({
                    "name": full_template_path.name,
                    "score": score,
                })

        self.last_debug = {
            "processed_roi": roi_proc.copy() if roi_proc is not None else None,
            "best_template_image": best_template_image,
            "best_template_name": best_name,
            "best_score": best_score,
        }

        if len(matched_items) == 0:
            return False, None, -1.0

        if len(matched_items) > 1:
            names = [item["name"] for item in matched_items]
            print(f"[TemplateChecker] 경고: {len(matched_items)}개 템플릿이 threshold({threshold})를 넘었습니다: {names}")

        matched = max(matched_items, key=lambda item: item["score"])
        return True, matched["name"], matched["score"]