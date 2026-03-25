import tkinter as tk
from PIL import Image, ImageTk
import cv2
import numpy as np


def bgr_to_tk(img: np.ndarray, max_width: int = 300) -> ImageTk.PhotoImage:
    if img is None or img.size == 0:
        img = np.zeros((20, 20, 3), dtype=np.uint8)

    h, w = img.shape[:2]
    if w > max_width:
        ratio = max_width / w
        img = cv2.resize(img, (int(w * ratio), int(h * ratio)), interpolation=cv2.INTER_AREA)

    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    return ImageTk.PhotoImage(Image.fromarray(rgb))


def gray_to_tk(img: np.ndarray, max_width: int = 300) -> ImageTk.PhotoImage:
    if img is None or img.size == 0:
        img = np.zeros((20, 20), dtype=np.uint8)

    h, w = img.shape[:2]
    if w > max_width:
        ratio = max_width / w
        img = cv2.resize(img, (int(w * ratio), int(h * ratio)), interpolation=cv2.INTER_AREA)

    return ImageTk.PhotoImage(Image.fromarray(img))


class IngameView(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg="#111111")

        self._time_raw_img = None
        self._score_raw_img = None
        self._kda_raw_img = None
        self._time_pre_img = None
        self._score_pre_img = None
        self._kda_pre_img = None

        title = tk.Label(
            self,
            text="Wild Rift 폴더 이미지 분석",
            fg="white",
            bg="#111111",
            font=("맑은 고딕", 16, "bold")
        )
        title.pack(pady=(10, 8))

        self.button_row = tk.Frame(self, bg="#111111")
        self.button_row.pack(pady=(0, 10))

        self.prev_btn = tk.Button(self.button_row, text="◀ 이전", font=("맑은 고딕", 11), bg="#2c2c2c", fg="white", width=10)
        self.prev_btn.pack(side="left", padx=6)

        self.run_btn = tk.Button(self.button_row, text="분석", font=("맑은 고딕", 11), bg="#2c2c2c", fg="white", width=10)
        self.run_btn.pack(side="left", padx=6)

        self.next_btn = tk.Button(self.button_row, text="다음 ▶", font=("맑은 고딕", 11), bg="#2c2c2c", fg="white", width=10)
        self.next_btn.pack(side="left", padx=6)

        self.main_frame = tk.Frame(self, bg="#111111")
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
            self,
            text="상태: 준비됨",
            fg="#9aa0a6",
            bg="#111111",
            font=("맑은 고딕", 9)
        )
        self.status_bar.pack(pady=(0, 8))

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

        label_img = tk.Label(frame, bg="#1a1a1a", bd=0, highlightthickness=0)
        label_img.pack(anchor="w", pady=(4, 0))

        return label_img

    def set_status_bar(self, text: str):
        self.status_bar.config(text=f"상태: {text}")

    def set_state_text(
        self,
        current_index: int,
        total_count: int,
        game_time: str,
        team_kills: str,
        enemy_kills: str,
        my_kills: str,
        my_deaths: str,
        my_assists: str,
        raw_time_text: str = "",
        raw_score_text: str = "",
        raw_kda_text: str = "",
        last_error: str = "",
    ):
        text = (
            f"이미지: {current_index} / {total_count}\n"
            f"시간: {game_time}\n"
            f"팀 킬스코어: {team_kills} : {enemy_kills}\n"
            f"내 KDA: {my_kills} / {my_deaths} / {my_assists}\n\n"
            f"[OCR 원문]\n"
            f"시간: {raw_time_text}\n"
            f"킬스코어: {raw_score_text}\n"
            f"KDA: {raw_kda_text}\n"
        )

        if last_error:
            text += f"\n오류: {last_error}"

        self.state_label.config(text=text)

    def set_crops(self, crops: dict):
        self._time_raw_img = bgr_to_tk(crops.get("time_raw"))
        self._score_raw_img = bgr_to_tk(crops.get("score_raw"))
        self._kda_raw_img = bgr_to_tk(crops.get("kda_raw"))

        self._time_pre_img = gray_to_tk(crops.get("time_pre"))
        self._score_pre_img = gray_to_tk(crops.get("score_pre"))
        self._kda_pre_img = gray_to_tk(crops.get("kda_pre"))

        self.time_raw_label.config(image=self._time_raw_img)
        self.score_raw_label.config(image=self._score_raw_img)
        self.kda_raw_label.config(image=self._kda_raw_img)

        self.time_pre_label.config(image=self._time_pre_img)
        self.score_pre_label.config(image=self._score_pre_img)
        self.kda_pre_label.config(image=self._kda_pre_img)