import os
from typing import Dict

import tkinter as tk
from PIL import Image, ImageTk
import cv2
import numpy as np

from core.ingame_analyzer import IngameAnalyzer, GameState
from core.ingame_coach import analyze_ingame
from device.image_source import FolderImageSource


DEBUG_SHOW_CROPS = True


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


class IngameWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Wild Rift Ingame Coach")
        self.root.attributes("-topmost", True)
        self.root.geometry("980x760+850+50")
        self.root.minsize(900, 680)
        self.root.configure(bg="#111111")

        self.analyzer = IngameAnalyzer()
        self.source = FolderImageSource()

        self._time_raw_img = None
        self._score_raw_img = None
        self._kda_raw_img = None
        self._time_pre_img = None
        self._score_pre_img = None
        self._kda_pre_img = None

        title = tk.Label(
            self.root,
            text="Wild Rift Ingame Coach",
            fg="white",
            bg="#111111",
            font=("맑은 고딕", 16, "bold")
        )
        title.pack(pady=(12, 8))

        self.top_btn_frame = tk.Frame(self.root, bg="#111111")
        self.top_btn_frame.pack(fill="x", padx=16, pady=(0, 10))

        self.prev_button = tk.Button(
            self.top_btn_frame,
            text="이전",
            font=("맑은 고딕", 11, "bold"),
            bg="#6b7280",
            fg="white",
            activebackground="#7b8592",
            activeforeground="white",
            relief="flat",
            command=self.prev_image
        )
        self.prev_button.pack(side="left", padx=(0, 8))

        self.next_button = tk.Button(
            self.top_btn_frame,
            text="다음",
            font=("맑은 고딕", 11, "bold"),
            bg="#2d7d46",
            fg="white",
            activebackground="#369758",
            activeforeground="white",
            relief="flat",
            command=self.next_image
        )
        self.next_button.pack(side="left")

        self.content_frame = tk.Frame(self.root, bg="#111111")
        self.content_frame.pack(fill="both", expand=True, padx=16, pady=(0, 10))

        left = tk.Frame(self.content_frame, bg="#111111")
        left.pack(side="left", fill="y", padx=(0, 12))

        right = tk.Frame(self.content_frame, bg="#111111")
        right.pack(side="left", fill="both", expand=True)

        self.info_box = tk.Frame(
            left,
            bg="#1a1a1a",
            highlightthickness=1,
            highlightbackground="#2a2a2a"
        )
        self.info_box.pack(fill="x")

        self.info_title = tk.Label(
            self.info_box,
            text="실시간 상태",
            fg="#9ad0ff",
            bg="#1a1a1a",
            font=("맑은 고딕", 12, "bold")
        )
        self.info_title.pack(anchor="w", padx=12, pady=(12, 8))

        self.state_label = tk.Label(
            self.info_box,
            text="대기중...",
            fg="white",
            bg="#1a1a1a",
            font=("맑은 고딕", 11),
            justify="left",
            anchor="nw",
            padx=12,
            pady=12,
            wraplength=300
        )
        self.state_label.pack(fill="both", expand=True)

        self.time_raw_label = self._make_image_block(right, "시간 ROI (원본)")
        self.score_raw_label = self._make_image_block(right, "킬스코어 ROI (원본)")
        self.kda_raw_label = self._make_image_block(right, "KDA ROI (원본)")

        self.time_pre_label = self._make_image_block(right, "시간 ROI (전처리)")
        self.score_pre_label = self._make_image_block(right, "킬스코어 ROI (전처리)")
        self.kda_pre_label = self._make_image_block(right, "KDA ROI (전처리)")

        self.status = tk.Label(
            self.root,
            text="상태: 준비됨",
            fg="#9aa0a6",
            bg="#111111",
            font=("맑은 고딕", 9)
        )
        self.status.pack(pady=(0, 8))

        self.root.bind("<Left>", lambda e: self.prev_image())
        self.root.bind("<Right>", lambda e: self.next_image())

        if self.source.count() > 0:
            self.process_current_image()
        else:
            self.set_status("이미지 없음")
            self.update_state(GameState(last_error="이미지 폴더가 비었음"), None)

    def _make_image_block(self, parent, title: str):
        frame = tk.Frame(parent, bg="#111111")
        frame.pack(anchor="w", fill="x", pady=(0, 10))

        title_label = tk.Label(
            frame,
            text=title,
            fg="#9ad0ff",
            bg="#111111",
            font=("맑은 고딕", 10, "bold")
        )
        title_label.pack(anchor="w")

        label_img = tk.Label(
            frame,
            bg="#1a1a1a",
            bd=0,
            highlightthickness=0
        )
        label_img.pack(anchor="w", pady=(4, 0))

        return label_img

    def set_status(self, text: str):
        self.status.config(text=f"상태: {text}")
        self.root.update_idletasks()

    def update_state(self, state: GameState, result=None):
        total = self.source.count()
        current = self.source.index + 1 if total > 0 else 0

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

        if result:
            text += "\n[코칭]\n"
            for tip in result.tips:
                text += f"- {tip}\n"
            text += f"\n[위험도] {result.danger}\n"
            text += f"[단계] {result.phase}\n"

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
        frame = self.source.get_current_frame()

        if frame is None:
            self.update_state(GameState(last_error="이미지 로드 실패"), None)
            self.set_status("이미지 로드 실패")
            return

        try:
            state, crops = self.analyzer.analyze(frame)
            result = analyze_ingame(state)
            self.update_state(state, result)
            self.update_crops(crops)
            self.set_status(os.path.basename(self.source.current_path()))
        except Exception as e:
            self.update_state(GameState(last_error=str(e)), None)
            self.set_status("분석 실패")

    def next_image(self):
        self.source.next()
        self.process_current_image()

    def prev_image(self):
        self.source.prev()
        self.process_current_image()


def run_ingame():
    window = IngameWindow()
    window.root.mainloop()