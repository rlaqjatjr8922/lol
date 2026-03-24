import os
import re
from dataclasses import dataclass
from typing import Optional, Tuple, Dict, List

import cv2
import numpy as np
import easyocr
import tkinter as tk
from PIL import Image, ImageTk


# =========================
# 설정
# =========================

IMAGE_DIR = r"C:\Users\gimbe\OneDrive\Desktop\lol_project\대이터추출\자료"
DEBUG_SHOW_CROPS = True

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


# =========================
# 데이터 구조
# =========================

@dataclass
class GameState:
    game_time: str = "?"
    team_kills: str = "?"
    enemy_kills: str = "?"
    my_kills: str = "?"
    my_deaths: str = "?"
    my_assists: str = "?"
    raw_time_text: str = ""
    raw_score_text: str = ""
    raw_kda_text: str = ""
    last_error: str = ""


# =========================
# 파일 로드
# =========================

def load_image_list(folder: str) -> List[str]:
    if not os.path.isdir(folder):
        return []

    files = []
    for name in os.listdir(folder):
        if name.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".webp")):
            files.append(os.path.join(folder, name))

    files.sort()
    return files


def imread_korean(path: str) -> Optional[np.ndarray]:
    data = np.fromfile(path, dtype=np.uint8)
    if data.size == 0:
        return None
    return cv2.imdecode(data, cv2.IMREAD_COLOR)


# =========================
# 이미지 유틸
# =========================

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


def bgr_to_tk(img: np.ndarray, max_width: int = 320) -> ImageTk.PhotoImage:
    if img is None or img.size == 0:
        img = np.zeros((20, 20, 3), dtype=np.uint8)

    h, w = img.shape[:2]
    if w > max_width:
        ratio = max_width / w
        img = cv2.resize(img, (int(w * ratio), int(h * ratio)), interpolation=cv2.INTER_AREA)

    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(rgb)
    return ImageTk.PhotoImage(pil_img)


def gray_to_tk(img: np.ndarray, max_width: int = 320) -> ImageTk.PhotoImage:
    if img is None or img.size == 0:
        img = np.zeros((20, 20), dtype=np.uint8)

    h, w = img.shape[:2]
    if w > max_width:
        ratio = max_width / w
        img = cv2.resize(img, (int(w * ratio), int(h * ratio)), interpolation=cv2.INTER_AREA)

    pil_img = Image.fromarray(img)
    return ImageTk.PhotoImage(pil_img)


# =========================
# OCR 파서
# =========================

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
            mm = m.group(1).zfill(2)
            ss = m.group(2)
            return f"{mm}:{ss}"

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


# =========================
# 분석 엔진
# =========================

class RealtimeAnalyzer:
    def __init__(self):
        self.ocr = OCRParser()

    def analyze(self, frame: np.ndarray) -> Tuple[GameState, Dict[str, np.ndarray]]:
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

        kda_pre = preprocess_kda_for_ocr(kda_crop)

        crops["time_raw"] = time_crop
        crops["score_raw"] = score_debug_raw
        crops["kda_raw"] = kda_crop.copy()

        crops["time_pre"] = time_pre
        crops["score_pre"] = preprocess_score_for_ocr(score_crop)
        crops["kda_pre"] = kda_pre

        crops["score_left_mask"] = score_left_mask
        crops["score_right_mask"] = score_right_mask
        crops["score_left_pre"] = score_left_pre
        crops["score_right_pre"] = score_right_pre

        time_text = self.ocr.read_text(time_pre, allowlist="0123456789:")
        score_left_text = self.ocr.read_text(score_left_pre, allowlist="0123456789")
        score_right_text = self.ocr.read_text(score_right_pre, allowlist="0123456789")
        kda_text = self.ocr.read_text(kda_pre, allowlist="0123456789/:")

        game_time = self.ocr.parse_time(time_text)
        team_kills = self.ocr.parse_single_number(score_left_text, max_value=80)
        enemy_kills = self.ocr.parse_single_number(score_right_text, max_value=80)
        my_kills, my_deaths, my_assists = self.ocr.parse_kda_full(kda_text)

        state = GameState(
            game_time=game_time,
            team_kills=team_kills,
            enemy_kills=enemy_kills,
            my_kills=my_kills,
            my_deaths=my_deaths,
            my_assists=my_assists,
            raw_time_text=time_text,
            raw_score_text=f"L={score_left_text} / R={score_right_text}",
            raw_kda_text=kda_text,
            last_error=""
        )

        return state, crops


# =========================
# UI
# =========================

class StatusWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Wild Rift 폴더 이미지 분석")
        self.root.geometry("1100x820+400+40")
        self.root.configure(bg="#111111")

        self.analyzer = RealtimeAnalyzer()
        self.image_paths = load_image_list(IMAGE_DIR)
        self.current_index = 0

        self._time_raw_img = None
        self._score_raw_img = None
        self._kda_raw_img = None
        self._time_pre_img = None
        self._score_pre_img = None
        self._kda_pre_img = None

        title = tk.Label(
            self.root,
            text="Wild Rift 폴더 이미지 분석",
            fg="white",
            bg="#111111",
            font=("맑은 고딕", 16, "bold")
        )
        title.pack(pady=(10, 8))

        btn_frame = tk.Frame(self.root, bg="#111111")
        btn_frame.pack(pady=(0, 10))

        self.prev_btn = tk.Button(
            btn_frame,
            text="◀ 이전",
            command=self.prev_image,
            font=("맑은 고딕", 11),
            bg="#2c2c2c",
            fg="white",
            width=10
        )
        self.prev_btn.pack(side="left", padx=6)

        self.next_btn = tk.Button(
            btn_frame,
            text="다음 ▶",
            command=self.next_image,
            font=("맑은 고딕", 11),
            bg="#2c2c2c",
            fg="white",
            width=10
        )
        self.next_btn.pack(side="left", padx=6)

        self.main_frame = tk.Frame(self.root, bg="#111111")
        self.main_frame.pack(fill="both", expand=True, padx=16, pady=8)

        left = tk.Frame(self.main_frame, bg="#111111")
        left.pack(side="left", fill="y", padx=(0, 12))

        right = tk.Frame(self.main_frame, bg="#111111")
        right.pack(side="left", fill="both", expand=True)

        state_box = tk.Frame(left, bg="#1a1a1a", highlightthickness=1, highlightbackground="#2c2c2c")
        state_box.pack(fill="x")

        self.state_label = tk.Label(
            state_box,
            text="대기중...",
            fg="white",
            bg="#1a1a1a",
            font=("맑은 고딕", 12),
            justify="left",
            anchor="nw",
            padx=12,
            pady=12
        )
        self.state_label.pack(fill="both", expand=True)

        self.time_raw_label = self._make_image_block(right, "시간 ROI (원본)")
        self.score_raw_label = self._make_image_block(right, "킬스코어 ROI (원본)")
        self.kda_raw_label = self._make_image_block(right, "KDA ROI (원본)")

        self.time_pre_label = self._make_image_block(right, "시간 ROI (전처리)")
        self.score_pre_label = self._make_image_block(right, "킬스코어 ROI (전처리)")
        self.kda_pre_label = self._make_image_block(right, "KDA ROI (전처리)")

        self.status_bar = tk.Label(
            self.root,
            text="상태: 준비됨",
            fg="#9aa0a6",
            bg="#111111",
            font=("맑은 고딕", 9)
        )
        self.status_bar.pack(pady=(0, 8))

        self.root.bind("<Right>", lambda e: self.next_image())
        self.root.bind("<Left>", lambda e: self.prev_image())

        if self.image_paths:
            self.process_current_image()
        else:
            self.set_status("이미지 없음")
            self.update_state(GameState(last_error=f"폴더에 이미지가 없음: {IMAGE_DIR}"))

    def _make_image_block(self, parent, title: str):
        frame = tk.Frame(parent, bg="#111111")
        frame.pack(anchor="w", fill="x", pady=(0, 10))

        label_title = tk.Label(
            frame,
            text=title,
            fg="#9ad0ff",
            bg="#111111",
            font=("맑은 고딕", 10, "bold")
        )
        label_title.pack(anchor="w")

        label_img = tk.Label(
            frame,
            bg="#1a1a1a",
            bd=0,
            highlightthickness=0
        )
        label_img.pack(anchor="w", pady=(4, 0))

        return label_img

    def set_status(self, text: str):
        self.status_bar.config(text=f"상태: {text}")

    def update_state(self, state: GameState):
        total = len(self.image_paths)
        current = self.current_index + 1 if total > 0 else 0

        text = (
            f"이미지: {current} / {total}\n"
            f"시간: {state.game_time}\n"
            f"팀 킬스코어: {state.team_kills} : {state.enemy_kills}\n"
            f"내 KDA: {state.my_kills} / {state.my_deaths} / {state.my_assists}\n\n"
            f"[OCR 원문]\n"
            f"시간: {state.raw_time_text}\n"
            f"킬스코어: {state.raw_score_text}\n"
            f"KDA: {state.raw_kda_text}\n"
        )

        if state.last_error:
            text += f"\n오류: {state.last_error}"

        self.state_label.config(text=text)

    def update_crops(self, crops: Dict[str, np.ndarray]):
        if not DEBUG_SHOW_CROPS:
            return

        self._time_raw_img = bgr_to_tk(crops["time_raw"])
        self._score_raw_img = bgr_to_tk(crops["score_raw"])
        self._kda_raw_img = bgr_to_tk(crops["kda_raw"])

        self._time_pre_img = gray_to_tk(crops["time_pre"])
        self._score_pre_img = gray_to_tk(crops["score_pre"])
        self._kda_pre_img = gray_to_tk(crops["kda_pre"])

        self.time_raw_label.config(image=self._time_raw_img)
        self.score_raw_label.config(image=self._score_raw_img)
        self.kda_raw_label.config(image=self._kda_raw_img)

        self.time_pre_label.config(image=self._time_pre_img)
        self.score_pre_label.config(image=self._score_pre_img)
        self.kda_pre_label.config(image=self._kda_pre_img)

    def process_current_image(self):
        if not self.image_paths:
            return

        path = self.image_paths[self.current_index]
        frame = imread_korean(path)

        if frame is None:
            self.update_state(GameState(last_error=f"이미지 로드 실패: {path}"))
            self.set_status("이미지 로드 실패")
            return

        try:
            state, crops = self.analyzer.analyze(frame)
            self.update_state(state)
            self.update_crops(crops)
            self.set_status(os.path.basename(path))
        except Exception as e:
            self.update_state(GameState(last_error=str(e)))
            self.set_status("분석 실패")

    def next_image(self):
        if not self.image_paths:
            return

        self.current_index += 1
        if self.current_index >= len(self.image_paths):
            self.current_index = 0

        self.process_current_image()

    def prev_image(self):
        if not self.image_paths:
            return

        self.current_index -= 1
        if self.current_index < 0:
            self.current_index = len(self.image_paths) - 1

        self.process_current_image()


# =========================
# 메인 실행
# =========================

def main():
    window = StatusWindow()
    window.root.mainloop()


if __name__ == "__main__":
    main()