from pathlib import Path
import cv2
import numpy as np


class PickChampionImageDetector:
    def __init__(self):
        pass

    def _safe_copy(self, img):
        if img is None:
            return None
        return img.copy()

    def _resize(self, img, size=(96, 96)):
        return cv2.resize(img, size, interpolation=cv2.INTER_AREA)

    def _resize_big(self, img, scale=4):
        if img is None:
            return None
        h, w = img.shape[:2]
        return cv2.resize(img, (w * scale, h * scale), interpolation=cv2.INTER_NEAREST)

    def _to_gray(self, img):
        return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    def _normalize_gray(self, gray):
        return cv2.equalizeHist(gray)

    def _to_binary(self, gray):
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return binary

    def _load_pick_ui(self):
        base_dir = Path(__file__).resolve().parents[2]
        ui_path = base_dir / "assets" / "ui" / "pick.png"

        if not ui_path.exists():
            print(f"[PickChampionImageDetector] pick ui not found: {ui_path}")
            return None

        ui_img = cv2.imread(str(ui_path), cv2.IMREAD_UNCHANGED)

        if ui_img is None:
            print(f"[PickChampionImageDetector] failed to read pick ui: {ui_path}")
            return None

        return ui_img

    def _overlay_ui(self, base_img, ui_img):
        if base_img is None:
            return None

        if ui_img is None:
            return base_img.copy()

        h, w = base_img.shape[:2]
        ui_resized = cv2.resize(ui_img, (w, h), interpolation=cv2.INTER_AREA)

        result = base_img.copy()

        # pick.png에 alpha 채널 있으면 투명도 기반 합성
        if ui_resized.shape[2] == 4:
            ui_bgr = ui_resized[:, :, :3]
            alpha = ui_resized[:, :, 3] / 255.0
            alpha = alpha[:, :, None]

            result = (result * (1.0 - alpha) + ui_bgr * alpha).astype(np.uint8)

        # alpha 없으면 그냥 덮기
        else:
            result = ui_resized[:, :, :3].copy()

        return result

    def _calc_template_score(self, roi_gray, tpl_gray):
        result = cv2.matchTemplate(roi_gray, tpl_gray, cv2.TM_CCOEFF_NORMED)
        return float(result[0][0])

    def _calc_hist_score(self, roi_bgr, tpl_bgr):
        roi_hsv = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2HSV)
        tpl_hsv = cv2.cvtColor(tpl_bgr, cv2.COLOR_BGR2HSV)

        roi_hist = cv2.calcHist([roi_hsv], [0, 1], None, [30, 32], [0, 180, 0, 256])
        tpl_hist = cv2.calcHist([tpl_hsv], [0, 1], None, [30, 32], [0, 180, 0, 256])

        cv2.normalize(roi_hist, roi_hist, 0, 1, cv2.NORM_MINMAX)
        cv2.normalize(tpl_hist, tpl_hist, 0, 1, cv2.NORM_MINMAX)

        return float(cv2.compareHist(roi_hist, tpl_hist, cv2.HISTCMP_CORREL))

    def _calc_absdiff_score(self, roi_gray, tpl_gray):
        diff = cv2.absdiff(roi_gray, tpl_gray)
        mean_diff = float(np.mean(diff))
        return 1.0 - (mean_diff / 255.0)

    def _prepare_debug_bundle(self, img, prefix):
        resized = self._resize(img, (96, 96))
        gray = self._to_gray(resized)
        gray_eq = self._normalize_gray(gray)
        binary = self._to_binary(gray_eq)

        return {
            f"{prefix}_resized": self._safe_copy(resized),
            f"{prefix}_gray_big": self._resize_big(gray, scale=4),
            f"{prefix}_gray_eq_big": self._resize_big(gray_eq, scale=4),
            f"{prefix}_binary_big": self._resize_big(binary, scale=4),

            "_resized": resized,
            "_gray": gray,
            "_gray_eq": gray_eq,
            "_binary": binary,
        }

    def detect(self, roi, stage_config):
        debug_images = {
            "roi_resized": None,
            "roi_gray_big": None,
            "roi_gray_eq_big": None,
            "roi_binary_big": None,

            "roi_with_ui": None,
            "best_template_with_ui": None,

            "best_template_resized": None,
            "best_template_gray_big": None,
            "best_template_gray_eq_big": None,
            "best_template_binary_big": None,

            "best_name": None,
            "best_score": -1.0,
            "top_candidates": [],
        }

        if roi is None:
            print("[PickChampionImageDetector] roi is None")
            return "unknown", debug_images

        if roi.size == 0:
            print("[PickChampionImageDetector] roi is empty")
            return "unknown", debug_images

        base_dir = Path(__file__).resolve().parents[2]
        template_dir = base_dir / stage_config["template_dir"]

        print("[PickChampionImageDetector] base_dir =", base_dir)
        print("[PickChampionImageDetector] resolved template_dir =", template_dir)
        print("[PickChampionImageDetector] template_dir exists =", template_dir.exists())

        if not template_dir.exists():
            print(f"[PickChampionImageDetector] template_dir not found: {template_dir}")
            return "unknown", debug_images

        template_files = sorted(template_dir.glob("*.png"))

        print("[PickChampionImageDetector] template_count =", len(template_files))
        print("[PickChampionImageDetector] template_files =", [str(x) for x in template_files])

        if not template_files:
            print(f"[PickChampionImageDetector] no template files in: {template_dir}")
            return "unknown", debug_images

        pick_ui = self._load_pick_ui()

        # 핵심: ROI 위에 pick.png 덮기
        roi_with_ui = self._overlay_ui(roi, pick_ui)
        debug_images["roi_with_ui"] = self._safe_copy(roi_with_ui)

        roi_bundle = self._prepare_debug_bundle(roi_with_ui, "roi")

        debug_images["roi_resized"] = roi_bundle["roi_resized"]
        debug_images["roi_gray_big"] = roi_bundle["roi_gray_big"]
        debug_images["roi_gray_eq_big"] = roi_bundle["roi_gray_eq_big"]
        debug_images["roi_binary_big"] = roi_bundle["roi_binary_big"]

        best_name = None
        best_score = -1.0
        best_tpl_bundle = None
        best_template_with_ui = None
        scores = []

        for template_file in template_files:
            print("[PickChampionImageDetector] reading =", template_file)

            template_img = cv2.imread(str(template_file), cv2.IMREAD_COLOR)
            print("[PickChampionImageDetector] read success =", template_img is not None)

            if template_img is None:
                print(f"[PickChampionImageDetector] failed to read template: {template_file}")
                continue

            # 핵심: 템플릿 위에도 pick.png 덮기
            template_with_ui = self._overlay_ui(template_img, pick_ui)

            tpl_bundle = self._prepare_debug_bundle(template_with_ui, "best_template")

            gray_score = self._calc_template_score(
                roi_bundle["_gray"],
                tpl_bundle["_gray"]
            )

            gray_eq_score = self._calc_template_score(
                roi_bundle["_gray_eq"],
                tpl_bundle["_gray_eq"]
            )

            hist_score = self._calc_hist_score(
                roi_bundle["_resized"],
                tpl_bundle["_resized"]
            )

            absdiff_score = self._calc_absdiff_score(
                roi_bundle["_gray_eq"],
                tpl_bundle["_gray_eq"]
            )

            final_score = (
                gray_score * 0.35
                + gray_eq_score * 0.30
                + hist_score * 0.20
                + absdiff_score * 0.15
            )

            final_score = float(final_score)

            print(
                f"[PickChampionImageDetector] {template_file.stem} | "
                f"gray={gray_score:.4f}, "
                f"gray_eq={gray_eq_score:.4f}, "
                f"hist={hist_score:.4f}, "
                f"absdiff={absdiff_score:.4f}, "
                f"final={final_score:.4f}"
            )

            scores.append({
                "name": template_file.stem,
                "gray_score": gray_score,
                "gray_eq_score": gray_eq_score,
                "hist_score": hist_score,
                "absdiff_score": absdiff_score,
                "final_score": final_score,
            })

            if final_score > best_score:
                best_score = final_score
                best_name = template_file.stem
                best_tpl_bundle = tpl_bundle
                best_template_with_ui = template_with_ui

        scores.sort(key=lambda x: x["final_score"], reverse=True)

        debug_images["top_candidates"] = scores[:5]
        debug_images["best_name"] = best_name
        debug_images["best_score"] = best_score

        if best_tpl_bundle is not None:
            debug_images["best_template_with_ui"] = self._safe_copy(best_template_with_ui)
            debug_images["best_template_resized"] = best_tpl_bundle["best_template_resized"]
            debug_images["best_template_gray_big"] = best_tpl_bundle["best_template_gray_big"]
            debug_images["best_template_gray_eq_big"] = best_tpl_bundle["best_template_gray_eq_big"]
            debug_images["best_template_binary_big"] = best_tpl_bundle["best_template_binary_big"]

        print(f"[PickChampionImageDetector] best_name = {best_name}")
        print(f"[PickChampionImageDetector] best_score = {best_score:.4f}")

        if best_name is None:
            return "unknown", debug_images

        return best_name, debug_images