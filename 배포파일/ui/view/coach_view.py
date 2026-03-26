import os
import tkinter as tk
from tkinter import ttk

import cv2
import numpy as np
from PIL import Image, ImageTk


class CoachView:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Wild Rift Pregame Coach")
        self.root.attributes("-topmost", True)
        self.root.geometry("1280x900+700+40")
        self.root.minsize(1100, 760)
        self.root.configure(bg="#111111")

        self.pick_order_var = tk.StringVar(value="선픽")
        self.my_champ_var = tk.StringVar(value="")
        self.enemy_champ_var = tk.StringVar(value="")
        self.lane_var = tk.StringVar(value="탑")

        self.detected_image_var = tk.StringVar(value="대기 중")
        self.detected_my_var = tk.StringVar(value="-")
        self.detected_enemy_var = tk.StringVar(value="-")
        self.detected_ally_list_var = tk.StringVar(value="-")
        self.detected_enemy_list_var = tk.StringVar(value="-")

        self.preview_groups = {}

        self._next_clicked = False
        self._back_clicked = False

        title = tk.Label(
            self.root,
            text="Wild Rift Pregame Coach",
            fg="white",
            bg="#111111",
            font=("맑은 고딕", 16, "bold"),
        )
        title.pack(pady=(12, 8))

        self.content_frame = tk.Frame(self.root, bg="#111111")
        self.content_frame.pack(fill="both", expand=True, padx=16, pady=(0, 10))

        # =========================
        # 1단계
        # =========================
        self.step1_frame = tk.Frame(self.content_frame, bg="#111111")

        step1_title = tk.Label(
            self.step1_frame,
            text="1단계 · 픽 정보 확인",
            fg="white",
            bg="#111111",
            font=("맑은 고딕", 12, "bold"),
        )
        step1_title.pack(anchor="w", pady=(8, 14))

        top_control_frame = tk.Frame(self.step1_frame, bg="#111111")
        top_control_frame.pack(fill="x", pady=(0, 10))

        pick_row = tk.Frame(top_control_frame, bg="#111111")
        pick_row.pack(anchor="w", pady=(0, 8), fill="x")

        pick_label = tk.Label(
            pick_row,
            text="픽 순서",
            fg="white",
            bg="#111111",
            font=("맑은 고딕", 11, "bold"),
            width=10,
            anchor="w",
        )
        pick_label.pack(side="left")

        self.pick_combo = ttk.Combobox(
            pick_row,
            textvariable=self.pick_order_var,
            values=["선픽", "후픽"],
            state="readonly",
            width=20,
        )
        self.pick_combo.pack(side="left", padx=(8, 0))
        self.pick_combo.bind("<<ComboboxSelected>>", self.on_pick_change)

        lane_row = tk.Frame(top_control_frame, bg="#111111")
        lane_row.pack(anchor="w", pady=(0, 8), fill="x")

        lane_label = tk.Label(
            lane_row,
            text="라인",
            fg="white",
            bg="#111111",
            font=("맑은 고딕", 11, "bold"),
            width=10,
            anchor="w",
        )
        lane_label.pack(side="left")

        self.step1_lane_combo = ttk.Combobox(
            lane_row,
            textvariable=self.lane_var,
            values=["탑", "미드", "원딜", "서폿", "정글"],
            state="readonly",
            width=20,
        )
        self.step1_lane_combo.pack(side="left", padx=(8, 0))

        self.step1_guide = tk.Label(
            self.step1_frame,
            text="자료 폴더 이미지를 자동으로 읽어서 현재 픽을 인식합니다.",
            fg="#9aa0a6",
            bg="#111111",
            font=("맑은 고딕", 9),
            justify="left",
            anchor="w",
        )
        self.step1_guide.pack(anchor="w", pady=(4, 10))

        self.detect_box = tk.Frame(
            self.step1_frame,
            bg="#1a1a1a",
            highlightthickness=1,
            highlightbackground="#2a2a2a",
        )
        self.detect_box.pack(fill="both", expand=True, pady=(4, 8))

        detect_title = tk.Label(
            self.detect_box,
            text="현재 인식한 결과",
            fg="#9ad0ff",
            bg="#1a1a1a",
            font=("맑은 고딕", 11, "bold"),
            anchor="w",
        )
        detect_title.pack(anchor="w", padx=12, pady=(10, 8))

        self._make_info_row(self.detect_box, "이미지", self.detected_image_var)
        self._make_info_row(self.detect_box, "내 챔피언", self.detected_my_var)
        self._make_info_row(self.detect_box, "상대 챔피언", self.detected_enemy_var)
        self._make_info_row(self.detect_box, "아군 픽", self.detected_ally_list_var, wrap=900)
        self._make_info_row(self.detect_box, "적군 픽", self.detected_enemy_list_var, wrap=900)

        self.preview_title = tk.Label(
            self.detect_box,
            text="잘라낸 ROI 이미지",
            fg="#9ad0ff",
            bg="#1a1a1a",
            font=("맑은 고딕", 11, "bold"),
            anchor="w",
        )
        self.preview_title.pack(anchor="w", padx=12, pady=(12, 8))

        preview_scroll_wrap = tk.Frame(self.detect_box, bg="#1a1a1a")
        preview_scroll_wrap.pack(fill="both", expand=True, padx=8, pady=(0, 10))

        self.preview_canvas = tk.Canvas(
            preview_scroll_wrap,
            bg="#1a1a1a",
            highlightthickness=0,
            bd=0,
        )
        self.preview_canvas.pack(side="left", fill="both", expand=True)

        preview_scrollbar = tk.Scrollbar(
            preview_scroll_wrap,
            orient="vertical",
            command=self.preview_canvas.yview,
        )
        preview_scrollbar.pack(side="right", fill="y")

        self.preview_canvas.configure(yscrollcommand=preview_scrollbar.set)

        self.preview_inner = tk.Frame(self.preview_canvas, bg="#1a1a1a")
        self.preview_canvas_window = self.preview_canvas.create_window(
            (0, 0),
            window=self.preview_inner,
            anchor="nw",
        )

        self.preview_inner.bind("<Configure>", self._on_preview_inner_configure)
        self.preview_canvas.bind("<Configure>", self._on_preview_canvas_configure)

        self._make_preview_group(self.preview_inner, "아군 밴", "ally_bans")
        self._make_preview_group(self.preview_inner, "적군 밴", "enemy_bans")
        self._make_preview_group(self.preview_inner, "아군 픽", "ally_picks")
        self._make_preview_group(self.preview_inner, "적군 픽", "enemy_picks")
        self._make_preview_group(self.preview_inner, "아군 역할", "ally_roles")

        # =========================
        # 2단계
        # =========================
        self.step2_frame = tk.Frame(self.content_frame, bg="#111111")

        step2_title = tk.Label(
            self.step2_frame,
            text="2단계 · 챔피언 추천 확인",
            fg="white",
            bg="#111111",
            font=("맑은 고딕", 12, "bold"),
        )
        step2_title.grid(row=0, column=0, columnspan=2, sticky="w", pady=(6, 14))

        self.recommend_label = tk.Label(
            self.step2_frame,
            text="추천 챔피언",
            fg="#9ad0ff",
            bg="#111111",
            font=("맑은 고딕", 11, "bold"),
        )
        self.recommend_label.grid(row=1, column=0, sticky="nw", pady=6)

        self.recommend_value = tk.Label(
            self.step2_frame,
            text="",
            fg="white",
            bg="#1a1a1a",
            font=("맑은 고딕", 11, "bold"),
            anchor="w",
            justify="left",
            padx=10,
            pady=8,
            width=32,
        )
        self.recommend_value.grid(row=1, column=1, sticky="ew", pady=6, padx=8)

        self.reason_label = tk.Label(
            self.step2_frame,
            text="추천 이유",
            fg="#9ad0ff",
            bg="#111111",
            font=("맑은 고딕", 11, "bold"),
        )
        self.reason_label.grid(row=2, column=0, sticky="nw", pady=6)

        self.reason_value = tk.Text(
            self.step2_frame,
            width=46,
            height=6,
            font=("맑은 고딕", 10),
            bg="#1a1a1a",
            fg="white",
            relief="flat",
            wrap="word",
            insertbackground="white",
        )
        self.reason_value.grid(row=2, column=1, sticky="nsew", pady=6, padx=8)
        self.reason_value.config(state="disabled")

        self.my_label = tk.Label(
            self.step2_frame,
            text="현재 내 챔피언",
            fg="white",
            bg="#111111",
            font=("맑은 고딕", 11, "bold"),
        )
        self.my_label.grid(row=3, column=0, sticky="w", pady=6)

        self.my_value_label = tk.Label(
            self.step2_frame,
            textvariable=self.detected_my_var,
            fg="white",
            bg="#1a1a1a",
            font=("맑은 고딕", 11),
            anchor="w",
            justify="left",
            padx=10,
            pady=8,
        )
        self.my_value_label.grid(row=3, column=1, sticky="ew", pady=6, padx=8)

        self.enemy_label = tk.Label(
            self.step2_frame,
            text="현재 상대 챔피언",
            fg="white",
            bg="#111111",
            font=("맑은 고딕", 11, "bold"),
        )
        self.enemy_label.grid(row=4, column=0, sticky="w", pady=6)

        self.enemy_value_label = tk.Label(
            self.step2_frame,
            textvariable=self.detected_enemy_var,
            fg="white",
            bg="#1a1a1a",
            font=("맑은 고딕", 11),
            anchor="w",
            justify="left",
            padx=10,
            pady=8,
        )
        self.enemy_value_label.grid(row=4, column=1, sticky="ew", pady=6, padx=8)

        self.lane_label = tk.Label(
            self.step2_frame,
            text="라인",
            fg="white",
            bg="#111111",
            font=("맑은 고딕", 11, "bold"),
        )
        self.lane_label.grid(row=5, column=0, sticky="w", pady=6)

        self.lane_combo = ttk.Combobox(
            self.step2_frame,
            textvariable=self.lane_var,
            values=["탑", "미드", "원딜", "서폿", "정글"],
            state="readonly",
            width=20,
        )
        self.lane_combo.grid(row=5, column=1, sticky="w", pady=6, padx=8)

        self.step2_frame.grid_columnconfigure(0, weight=0)
        self.step2_frame.grid_columnconfigure(1, weight=1)
        self.step2_frame.grid_rowconfigure(2, weight=1)

        # =========================
        # 3단계
        # =========================
        self.step3_frame = tk.Frame(self.content_frame, bg="#111111")

        step3_title = tk.Label(
            self.step3_frame,
            text="3단계 · 룬/스펠/아이템 추천 결과",
            fg="white",
            bg="#111111",
            font=("맑은 고딕", 12, "bold"),
        )
        step3_title.pack(anchor="w", pady=(6, 12))

        self.waiting_label = tk.Label(
            self.step3_frame,
            text="",
            fg="#ffd166",
            bg="#111111",
            font=("맑은 고딕", 11, "bold"),
            justify="left",
            anchor="w",
            wraplength=1000,
        )
        self.waiting_label.pack(anchor="w", pady=(0, 10), fill="x")

        self.result_title_label = tk.Label(
            self.step3_frame,
            text="",
            fg="#9ad0ff",
            bg="#111111",
            font=("맑은 고딕", 11, "bold"),
            justify="left",
            anchor="w",
            wraplength=1000,
        )
        self.result_title_label.pack(anchor="w", pady=(0, 10), fill="x")

        self.result_box = tk.Frame(
            self.step3_frame,
            bg="#1a1a1a",
            highlightthickness=1,
            highlightbackground="#2a2a2a",
        )
        self.result_box.pack(fill="both", expand=True, pady=(0, 10))

        self.result_body_text = tk.Text(
            self.result_box,
            font=("맑은 고딕", 11),
            bg="#1a1a1a",
            fg="white",
            relief="flat",
            wrap="word",
            height=14,
            insertbackground="white",
        )
        self.result_body_text.pack(fill="both", expand=True, padx=10, pady=10)
        self.result_body_text.config(state="disabled")

        self.result_plan_label = tk.Label(
            self.step3_frame,
            text="",
            fg="#9ad0ff",
            bg="#111111",
            font=("맑은 고딕", 11),
            justify="left",
            anchor="w",
            wraplength=1000,
        )
        self.result_plan_label.pack(anchor="w", pady=(0, 10), fill="x")

        self.btn_frame = tk.Frame(self.root, bg="#111111")
        self.btn_frame.pack(fill="x", padx=16, pady=10)

        self.back_button = tk.Button(
            self.btn_frame,
            text="뒤로",
            font=("맑은 고딕", 11, "bold"),
            bg="#6b7280",
            fg="white",
            activebackground="#7b8592",
            activeforeground="white",
            relief="flat",
            command=self._on_back,
        )

        self.next_button = tk.Button(
            self.btn_frame,
            text="다음",
            font=("맑은 고딕", 11, "bold"),
            bg="#2d7d46",
            fg="white",
            activebackground="#369758",
            activeforeground="white",
            relief="flat",
            command=self._on_next,
        )

        self.btn_frame.grid_columnconfigure(0, weight=1)
        self.btn_frame.grid_columnconfigure(1, weight=1)

        self.status = tk.Label(
            self.root,
            text="상태: 자료 폴더 이미지 대기",
            fg="#9aa0a6",
            bg="#111111",
            font=("맑은 고딕", 9),
            wraplength=1000,
            justify="left",
        )
        self.status.pack(pady=(0, 8))

        self.current_step = 1
        self.show_step1()
        self.on_pick_change()

    def _on_preview_inner_configure(self, event=None):
        self.preview_canvas.configure(scrollregion=self.preview_canvas.bbox("all"))

    def _on_preview_canvas_configure(self, event):
        self.preview_canvas.itemconfig(self.preview_canvas_window, width=event.width)

    def _make_info_row(self, parent, title, var, wrap=420):
        row = tk.Frame(parent, bg="#1a1a1a")
        row.pack(fill="x", padx=12, pady=4)

        label = tk.Label(
            row,
            text=title,
            fg="#9ad0ff",
            bg="#1a1a1a",
            font=("맑은 고딕", 10, "bold"),
            width=12,
            anchor="w",
        )
        label.pack(side="left", anchor="n")

        value = tk.Label(
            row,
            textvariable=var,
            fg="white",
            bg="#1a1a1a",
            font=("맑은 고딕", 10),
            anchor="w",
            justify="left",
            wraplength=wrap,
        )
        value.pack(side="left", fill="x", expand=True)

    def _make_preview_group(self, parent, title, key):
        outer = tk.Frame(parent, bg="#1a1a1a")
        outer.pack(fill="x", padx=12, pady=(4, 10))

        title_label = tk.Label(
            outer,
            text=title,
            fg="#9ad0ff",
            bg="#1a1a1a",
            font=("맑은 고딕", 10, "bold"),
            anchor="w",
        )
        title_label.pack(anchor="w", pady=(0, 4))

        row = tk.Frame(outer, bg="#1a1a1a")
        row.pack(anchor="w")

        image_labels = []
        text_labels = []

        for i in range(5):
            cell = tk.Frame(row, bg="#1a1a1a")
            cell.grid(row=0, column=i, padx=4)

            img_label = tk.Label(
                cell,
                text="없음",
                width=110,
                height=110,
                fg="#9aa0a6",
                bg="#111111",
                bd=1,
                relief="solid",
                compound="center",
            )
            img_label.pack()

            txt_label = tk.Label(
                cell,
                text="-",
                fg="white",
                bg="#1a1a1a",
                font=("맑은 고딕", 8),
                wraplength=105,
                justify="center",
            )
            txt_label.pack(pady=(4, 0))

            image_labels.append(img_label)
            text_labels.append(txt_label)

        self.preview_groups[key] = {
            "image_labels": image_labels,
            "text_labels": text_labels,
            "photos": [],
        }

    def _load_photo_from_path(self, path, max_size=96):
        if not path or not os.path.exists(path):
            return None

        try:
            data = np.fromfile(path, dtype=np.uint8)
            img = cv2.imdecode(data, cv2.IMREAD_COLOR)

            if img is None:
                return None

            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

            h, w = img.shape[:2]
            if h <= 0 or w <= 0:
                return None

            scale = min(max_size / max(w, 1), max_size / max(h, 1))
            new_w = max(1, int(w * scale))
            new_h = max(1, int(h * scale))

            img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)

            pil_img = Image.fromarray(img)
            return ImageTk.PhotoImage(pil_img)
        except Exception:
            return None

    def _set_preview_group(self, key, paths, names):
        group = self.preview_groups.get(key)
        if not group:
            return

        photos = []

        for i in range(5):
            img_label = group["image_labels"][i]
            txt_label = group["text_labels"][i]

            path = paths[i] if i < len(paths) else ""
            name = names[i] if i < len(names) and names[i] else "-"

            photo = self._load_photo_from_path(path, max_size=96)

            if photo is not None:
                img_label.config(image=photo, text="", width=110, height=110)
                img_label.image = photo
            else:
                img_label.config(image="", text="없음", width=110, height=110)
                img_label.image = None

            txt_label.config(text=name)
            photos.append(photo)

        group["photos"] = photos

    def set_detected_previews(self, result: dict):
        debug_paths = result.get("debug_paths", {}) or {}

        self._set_preview_group(
            "ally_bans",
            debug_paths.get("ally_bans", []),
            result.get("ally_bans_ko") or result.get("ally_bans", []),
        )
        self._set_preview_group(
            "enemy_bans",
            debug_paths.get("enemy_bans", []),
            result.get("enemy_bans_ko") or result.get("enemy_bans", []),
        )
        self._set_preview_group(
            "ally_picks",
            debug_paths.get("ally_picks", []),
            result.get("ally_picks_ko") or result.get("ally_picks", []),
        )
        self._set_preview_group(
            "enemy_picks",
            debug_paths.get("enemy_picks", []),
            result.get("enemy_picks_ko") or result.get("enemy_picks", []),
        )
        self._set_preview_group(
            "ally_roles",
            debug_paths.get("ally_roles", []),
            result.get("ally_roles", []),
        )

        self.root.update_idletasks()

    def _on_next(self):
        self._next_clicked = True

    def _on_back(self):
        self._back_clicked = True

    def on_pick_change(self, event=None):
        if self.pick_order_var.get().strip() == "후픽":
            self.step1_guide.config(text="후픽 기준으로 자동 인식한 상대 챔피언을 사용합니다.")
        else:
            self.step1_guide.config(text="선픽 기준으로 자료 폴더 이미지를 자동 인식합니다.")
        self.root.update_idletasks()

    def _hide_all_steps(self):
        self.step1_frame.pack_forget()
        self.step2_frame.pack_forget()
        self.step3_frame.pack_forget()

    def show_step1(self):
        self.current_step = 1
        self._hide_all_steps()
        self.step1_frame.pack(fill="both", expand=True)
        self.back_button.grid_remove()
        self.next_button.config(text="다음")
        self.next_button.grid(row=0, column=1, sticky="ew", padx=4)
        self.set_status("픽 순서와 라인 선택 / 자동 인식 결과 확인")
        self.on_pick_change()
        self.root.update()

    def show_step2(self):
        self.current_step = 2
        self._hide_all_steps()
        self.step2_frame.pack(fill="both", expand=True)
        self.back_button.grid(row=0, column=0, sticky="ew", padx=4)
        self.next_button.config(text="다음")
        self.next_button.grid(row=0, column=1, sticky="ew", padx=4)
        self.set_status("인식된 챔피언 기준 추천 확인")
        self.root.update()

    def show_step3(self):
        self.current_step = 3
        self._hide_all_steps()
        self.step3_frame.pack(fill="both", expand=True)
        self.back_button.grid(row=0, column=0, sticky="ew", padx=4)
        self.next_button.config(text="게임 시작")
        self.next_button.grid(row=0, column=1, sticky="ew", padx=4)
        self.set_status("프리게임 완료")
        self.root.update()

    def set_detected_picks(self, result: dict):
        image_path = result.get("image_path", "")
        image_name = os.path.basename(image_path) if image_path else "-"

        my_champ = result.get("my_champ_ko") or result.get("my_champ") or "-"
        enemy_champ = result.get("enemy_champ_ko") or result.get("enemy_champ") or "-"

        ally_picks = result.get("ally_picks_ko") or result.get("ally_picks", []) or []
        enemy_picks = result.get("enemy_picks_ko") or result.get("enemy_picks", []) or []

        ally_text = ", ".join([x for x in ally_picks if x]) or "-"
        enemy_text = ", ".join([x for x in enemy_picks if x]) or "-"

        self.detected_image_var.set(image_name)
        self.detected_my_var.set(my_champ)
        self.detected_enemy_var.set(enemy_champ)
        self.detected_ally_list_var.set(ally_text)
        self.detected_enemy_list_var.set(enemy_text)

        self.root.update_idletasks()

    def set_recommendation(self, champ: str, reason: str):
        self.recommend_value.config(text=champ or "")
        self.reason_value.config(state="normal")
        self.reason_value.delete("1.0", "end")
        self.reason_value.insert("1.0", reason or "")
        self.reason_value.config(state="disabled")
        self.root.update()

    def show_waiting_in_step2(self, text: str):
        self.recommend_value.config(text=text)
        self.reason_value.config(state="normal")
        self.reason_value.delete("1.0", "end")
        self.reason_value.config(state="disabled")
        self.set_status("GPT 응답 대기중")
        self.root.update()

    def show_waiting_in_step3(self, text="GPT 응답 대기중..."):
        self.waiting_label.config(text=text)
        self.result_title_label.config(text="")
        self.result_body_text.config(state="normal")
        self.result_body_text.delete("1.0", "end")
        self.result_body_text.config(state="disabled")
        self.result_plan_label.config(text="")
        self.set_status("GPT 응답 대기중")
        self.root.update()

    def clear_waiting_in_step3(self):
        self.waiting_label.config(text="")
        self.root.update()

    def set_result(self, title_text: str, body_text: str, plan_text: str):
        self.clear_waiting_in_step3()
        self.result_title_label.config(text=title_text or "")
        self.result_body_text.config(state="normal")
        self.result_body_text.delete("1.0", "end")
        self.result_body_text.insert("1.0", body_text or "")
        self.result_body_text.config(state="disabled")
        self.result_plan_label.config(text=plan_text or "")
        self.set_status("추천 결과 확인")
        self.root.update()

    def get_inputs(self):
        return {
            "pick_order": self.pick_order_var.get().strip(),
            "my_champ": self.my_champ_var.get().strip(),
            "enemy_champ": self.enemy_champ_var.get().strip(),
            "lane": self.lane_var.get().strip(),
        }

    def set_status(self, text: str):
        self.status.config(text=f"상태: {text}")
        self.root.update()

    def mainloop(self):
        self.root.mainloop()