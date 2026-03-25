import re
from typing import Optional, Tuple, Dict

import cv2
import easyocr
import numpy as np

from core.model.ingame_state import IngameState


ROI_CONFIG = {
    "time":  (0.745, 0.04, 0.77, 0.065),
    "score": (0.735, 0.01, 0.785, 0.04),
    "kda":   (0.83, 0.01, 0.885, 0.04),
}

SCORE_BOXES = {
    "left":  (0.00, 0.00, 0.30, 1.00),
    "right": (0.70, 0.00, 1.00, 1.00),
}

COLOR_CONFIG = {
    "score_left":  {"hex": "#4492CE", "tolerance": 80},
    "score_right": {"hex": "#DA3A2C", "tolerance": 80},
}


def crop_ratio(img: np.ndarray, roi: Tuple[float, float, float, float]) -> np.ndarray:
    h, w = img.shape[:2]
    x1, y1, x2, y2 = roi

    px1 = max(0, min(w, int(w * x1)))
    py1 = max(0, min(h, int(h * y1)))
    px2 = max(0, min(w, int(w * x2)))
    py2 = max(0, min(h, int(h * y2)))

    if px2 <= px1 or py2 <= py1:
        return np.zeros((10, 10, 3), dtype=np.uint8)

    return img[py1:py2, px1:px2].copy()


def crop_inner_ratio(img: np.ndarray, inner_roi: Tuple[float, float, float, float]) -> np.ndarray:
    h, w = img.shape[:2]
    x1, y1, x2, y2 = inner_roi

    px1 = max(0, min(w, int(w * x1)))
    py1 = max(0, min(h, int(h * y1)))
    px2 = max(0, min(w, int(w * x2)))
    py2 = max(0, min(h, int(h * y2)))

    if px2 <= px1 or py2 <= py1:
        return np.zeros((10, 10, 3), dtype=np.uint8)

    return img[py1:py2, px1:px2].copy()


def draw_inner_boxes(img: np.ndarray, boxes, color=(0, 255, 0), thickness=2) -> np.ndarray:
    out = img.copy()
    h, w = out.shape[:2]

    for (x1, y1, x2, y2) in boxes:
        px1 = int(w * x1)
        py1 = int(h * y1)
        px2 = int(w * x2)
        py2 = int(h * y2)
        cv2.rectangle(out, (px1, py1), (px2, py2), color, thickness)

    return out


def preprocess_time_for_ocr(img: np.ndarray, scale: int = 6) -> np.ndarray:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    gray = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX)
    gray = cv2.GaussianBlur(gray, (3, 3), 0)
    _, th = cv2.threshold(gray, 170, 255, cv2.THRESH_BINARY)
    return th


def preprocess_kda_for_ocr(img: np.ndarray, scale: int = 5) -> np.ndarray:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    gray = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX)
    gray = cv2.GaussianBlur(gray, (3, 3), 0)
    _, th = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
    return th


def preprocess_score_for_ocr(img: np.ndarray, scale: int = 3) -> np.ndarray:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    gray = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX)
    return gray


def hex_to_bgr(hex_color: str) -> np.ndarray:
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return np.array([b, g, r], dtype=np.uint8)


def extract_color_mask(img: np.ndarray, hex_color: str, tolerance: int = 40) -> np.ndarray:
    target = hex_to_bgr(hex_color).astype(np.int16)

    lower = np.clip(target - tolerance, 0, 255).astype(np.uint8)
    upper = np.clip(target + tolerance, 0, 255).astype(np.uint8)

    mask = cv2.inRange(img, lower, upper)

    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    return mask


def preprocess_color_mask_for_ocr(mask: np.ndarray, scale: int = 4) -> np.ndarray:
    enlarged = cv2.resize(mask, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    enlarged = cv2.GaussianBlur(enlarged, (3, 3), 0)
    _, th = cv2.threshold(enlarged, 127, 255, cv2.THRESH_BINARY)
    return th


class OCRParser:
    def __init__(self):
        self.reader = easyocr.Reader(["en"], gpu=False)

    def read_text(self, img: np.ndarray, allowlist: Optional[str] = None) -> str:
        results = self.reader.readtext(
            img,
            detail=0,
            paragraph=False,
            allowlist=allowlist
        )
        return " ".join(results).strip()

    def parse_time(self, text: str) -> str:
        text = text.replace(" ", "")
        text = text.replace(".", ":")
        text = text.replace(";", ":")
        text = text.replace(",", ":")
        text = text.replace("::", ":")

        m = re.search(r"(\d{1,2})[:](\d{2})", text)
        if m:
            return f"{m.group(1).zfill(2)}:{m.group(2)}"

        nums = re.findall(r"\d", text)
        if len(nums) >= 4:
            mm = nums[0] + nums[1]
            ss = nums[2] + nums[3]
            try:
                if 0 <= int(ss) <= 59:
                    return f"{mm}:{ss}"
            except ValueError:
                pass

        return "?"

    def parse_single_number(self, text: str, max_value: Optional[int] = None) -> str:
        nums = re.findall(r"\d{1,3}", text)
        if not nums:
            return "?"

        nums = sorted(nums, key=lambda x: abs(len(x) - 2))

        for n in nums:
            if max_value is None or int(n) <= max_value:
                return n

        return nums[0]

    def parse_kda_full(self, text: str):
        text = text.replace(" ", "")
        text = text.replace("|", "/")
        text = text.replace("\\", "/")
        text = text.replace(":", "/")
        text = text.replace(";", "/")
        text = text.replace("I", "1")
        text = text.replace("l", "1")
        text = text.replace("]", "1")
        text = text.replace("[", "1")

        m = re.search(r"(\d{1,2})[\/]+(\d{1,2})[\/]+(\d{1,2})", text)
        if m:
            return m.group(1), m.group(2), m.group(3)

        nums = re.findall(r"\d{1,2}", text)
        if len(nums) >= 3:
            return nums[0], nums[1], nums[2]

        return "?", "?", "?"


class IngameOCRMatcher:
    def __init__(self):
        self.ocr = OCRParser()

    def extract_state_from_frame(self, frame: np.ndarray):
        crops: Dict[str, np.ndarray] = {}

        time_crop = crop_ratio(frame, ROI_CONFIG["time"])
        score_crop = crop_ratio(frame, ROI_CONFIG["score"])
        kda_crop = crop_ratio(frame, ROI_CONFIG["kda"])

        score_debug_raw = draw_inner_boxes(
            score_crop,
            [SCORE_BOXES["left"], SCORE_BOXES["right"]],
            color=(0, 255, 0),
            thickness=2
        )

        time_pre = preprocess_time_for_ocr(time_crop)

        score_left_crop = crop_inner_ratio(score_crop, SCORE_BOXES["left"])
        score_right_crop = crop_inner_ratio(score_crop, SCORE_BOXES["right"])

        score_left_mask = extract_color_mask(
            score_left_crop,
            COLOR_CONFIG["score_left"]["hex"],
            COLOR_CONFIG["score_left"]["tolerance"]
        )
        score_right_mask = extract_color_mask(
            score_right_crop,
            COLOR_CONFIG["score_right"]["hex"],
            COLOR_CONFIG["score_right"]["tolerance"]
        )

        score_left_pre = preprocess_color_mask_for_ocr(score_left_mask)
        score_right_pre = preprocess_color_mask_for_ocr(score_right_mask)

        score_pre = preprocess_score_for_ocr(score_crop)
        kda_pre = preprocess_kda_for_ocr(kda_crop)

        crops["time_raw"] = time_crop
        crops["score_raw"] = score_debug_raw
        crops["kda_raw"] = kda_crop.copy()
        crops["time_pre"] = time_pre
        crops["score_pre"] = score_pre
        crops["kda_pre"] = kda_pre

        time_text = self.ocr.read_text(time_pre, allowlist="0123456789:")
        score_left_text = self.ocr.read_text(score_left_pre, allowlist="0123456789")
        score_right_text = self.ocr.read_text(score_right_pre, allowlist="0123456789")
        kda_text = self.ocr.read_text(kda_pre, allowlist="0123456789/:")

        kills, deaths, assists = self.ocr.parse_kda_full(kda_text)

        state = IngameState(
            game_time=self.ocr.parse_time(time_text),
            team_kills=self.ocr.parse_single_number(score_left_text, max_value=80),
            enemy_kills=self.ocr.parse_single_number(score_right_text, max_value=80),
            my_kills=kills,
            my_deaths=deaths,
            my_assists=assists,
            raw_time_text=time_text,
            raw_score_text=f"L={score_left_text} / R={score_right_text}",
            raw_kda_text=kda_text,
            last_error=""
        )

        return state, crops