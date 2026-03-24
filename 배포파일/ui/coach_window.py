import tkinter as tk
from tkinter import ttk


class CoachWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Wild Rift Pregame Coach")
        self.root.attributes("-topmost", True)
        self.root.geometry("720x700+900+70")
        self.root.minsize(680, 620)
        self.root.configure(bg="#111111")

        self.pick_order_var = tk.StringVar(value="선픽")
        self.my_champ_var = tk.StringVar(value="")
        self.enemy_champ_var = tk.StringVar(value="")
        self.lane_var = tk.StringVar(value="탑")

        self._next_clicked = False
        self._back_clicked = False

        title = tk.Label(
            self.root,
            text="Wild Rift Pregame Coach",
            fg="white",
            bg="#111111",
            font=("맑은 고딕", 16, "bold")
        )
        title.pack(pady=(12, 8))

        # ==========================
        # 본문 컨테이너
        # ==========================
        self.content_frame = tk.Frame(self.root, bg="#111111")
        self.content_frame.pack(fill="both", expand=True, padx=16, pady=(0, 10))

        # --------------------------
        # 1단계
        # --------------------------
        self.step1_frame = tk.Frame(self.content_frame, bg="#111111")

        step1_title = tk.Label(
            self.step1_frame,
            text="1단계 · 픽 정보 입력",
            fg="white",
            bg="#111111",
            font=("맑은 고딕", 12, "bold")
        )
        step1_title.pack(anchor="w", pady=(8, 14))

        pick_row = tk.Frame(self.step1_frame, bg="#111111")
        pick_row.pack(anchor="w", pady=(0, 12), fill="x")

        pick_label = tk.Label(
            pick_row,
            text="픽 순서",
            fg="white",
            bg="#111111",
            font=("맑은 고딕", 11, "bold"),
            width=10,
            anchor="w"
        )
        pick_label.pack(side="left")

        self.pick_combo = ttk.Combobox(
            pick_row,
            textvariable=self.pick_order_var,
            values=["선픽", "후픽"],
            state="readonly",
            width=20
        )
        self.pick_combo.pack(side="left", padx=(8, 0))
        self.pick_combo.bind("<<ComboboxSelected>>", self.on_pick_change)

        lane_row = tk.Frame(self.step1_frame, bg="#111111")
        lane_row.pack(anchor="w", pady=(0, 12), fill="x")

        lane_label = tk.Label(
            lane_row,
            text="라인",
            fg="white",
            bg="#111111",
            font=("맑은 고딕", 11, "bold"),
            width=10,
            anchor="w"
        )
        lane_label.pack(side="left")

        self.step1_lane_combo = ttk.Combobox(
            lane_row,
            textvariable=self.lane_var,
            values=["탑", "미드", "원딜", "서폿", "정글"],
            state="readonly",
            width=20
        )
        self.step1_lane_combo.pack(side="left", padx=(8, 0))

        self.enemy_row_step1 = tk.Frame(self.step1_frame, bg="#111111")

        self.enemy_label_step1 = tk.Label(
            self.enemy_row_step1,
            text="상대 챔피언",
            fg="white",
            bg="#111111",
            font=("맑은 고딕", 11, "bold"),
            width=10,
            anchor="w"
        )

        self.enemy_entry_step1 = tk.Entry(
            self.enemy_row_step1,
            textvariable=self.enemy_champ_var,
            width=24,
            font=("맑은 고딕", 11)
        )

        self.step1_guide = tk.Label(
            self.step1_frame,
            text="후픽일 때만 상대 챔피언을 입력하면 됩니다.",
            fg="#9aa0a6",
            bg="#111111",
            font=("맑은 고딕", 9),
            justify="left",
            anchor="w"
        )
        self.step1_guide.pack(anchor="w", pady=(8, 0))

        # --------------------------
        # 2단계
        # --------------------------
        self.step2_frame = tk.Frame(self.content_frame, bg="#111111")

        step2_title = tk.Label(
            self.step2_frame,
            text="2단계 · 챔피언 추천 확인",
            fg="white",
            bg="#111111",
            font=("맑은 고딕", 12, "bold")
        )
        step2_title.grid(row=0, column=0, columnspan=2, sticky="w", pady=(6, 14))

        self.recommend_label = tk.Label(
            self.step2_frame,
            text="추천 챔피언",
            fg="#9ad0ff",
            bg="#111111",
            font=("맑은 고딕", 11, "bold")
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
            width=32
        )
        self.recommend_value.grid(row=1, column=1, sticky="ew", pady=6, padx=8)

        self.reason_label = tk.Label(
            self.step2_frame,
            text="추천 이유",
            fg="#9ad0ff",
            bg="#111111",
            font=("맑은 고딕", 11, "bold")
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
            insertbackground="white"
        )
        self.reason_value.grid(row=2, column=1, sticky="nsew", pady=6, padx=8)
        self.reason_value.config(state="disabled")

        self.my_label = tk.Label(
            self.step2_frame,
            text="내 챔피언",
            fg="white",
            bg="#111111",
            font=("맑은 고딕", 11, "bold")
        )
        self.my_label.grid(row=3, column=0, sticky="w", pady=6)

        self.my_entry = tk.Entry(
            self.step2_frame,
            textvariable=self.my_champ_var,
            width=28,
            font=("맑은 고딕", 11)
        )
        self.my_entry.grid(row=3, column=1, sticky="ew", pady=6, padx=8)

        self.enemy_label = tk.Label(
            self.step2_frame,
            text="상대 챔피언",
            fg="white",
            bg="#111111",
            font=("맑은 고딕", 11, "bold")
        )
        self.enemy_label.grid(row=4, column=0, sticky="w", pady=6)

        self.enemy_entry = tk.Entry(
            self.step2_frame,
            textvariable=self.enemy_champ_var,
            width=28,
            font=("맑은 고딕", 11)
        )
        self.enemy_entry.grid(row=4, column=1, sticky="ew", pady=6, padx=8)

        self.lane_label = tk.Label(
            self.step2_frame,
            text="라인",
            fg="white",
            bg="#111111",
            font=("맑은 고딕", 11, "bold")
        )
        self.lane_label.grid(row=5, column=0, sticky="w", pady=6)

        self.lane_combo = ttk.Combobox(
            self.step2_frame,
            textvariable=self.lane_var,
            values=["탑", "미드", "원딜", "서폿", "정글"],
            state="readonly",
            width=20
        )
        self.lane_combo.grid(row=5, column=1, sticky="w", pady=6, padx=8)

        self.step2_frame.grid_columnconfigure(0, weight=0)
        self.step2_frame.grid_columnconfigure(1, weight=1)
        self.step2_frame.grid_rowconfigure(2, weight=1)

        # --------------------------
        # 3단계
        # --------------------------
        self.step3_frame = tk.Frame(self.content_frame, bg="#111111")

        step3_title = tk.Label(
            self.step3_frame,
            text="3단계 · 룬/스펠/아이템 추천 결과",
            fg="white",
            bg="#111111",
            font=("맑은 고딕", 12, "bold")
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
            wraplength=640
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
            wraplength=640
        )
        self.result_title_label.pack(anchor="w", pady=(0, 10), fill="x")

        self.result_box = tk.Frame(
            self.step3_frame,
            bg="#1a1a1a",
            highlightthickness=1,
            highlightbackground="#2a2a2a"
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
            insertbackground="white"
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
            wraplength=640
        )
        self.result_plan_label.pack(anchor="w", pady=(0, 10), fill="x")

        # --------------------------
        # 버튼
        # --------------------------
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
            command=self._on_back
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
            command=self._on_next
        )

        self.btn_frame.grid_columnconfigure(0, weight=1)
        self.btn_frame.grid_columnconfigure(1, weight=1)

        self.status = tk.Label(
            self.root,
            text="상태: 픽 순서와 라인 선택",
            fg="#9aa0a6",
            bg="#111111",
            font=("맑은 고딕", 9),
            wraplength=640,
            justify="left"
        )
        self.status.pack(pady=(0, 8))

        self.current_step = 1
        self.show_step1()
        self.on_pick_change()

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_next(self):
        # 🔥 3단계에서 다음 누르면 인게임 코치 실행
        if self.current_step == 3:
            from core.ingame_coach import run_ingame

            print("👉 인게임 실행")
            self.root.destroy()
            run_ingame()
            return

        self._next_clicked = True

    def _on_back(self):
        self._back_clicked = True

    def _on_close(self):
        self.root.destroy()

    def on_pick_change(self, event=None):
        is_counter = self.pick_order_var.get().strip() == "후픽"

        if is_counter:
            if not self.enemy_row_step1.winfo_ismapped():
                self.enemy_row_step1.pack(anchor="w", pady=(0, 8), fill="x")
            self.enemy_label_step1.pack(side="left")
            self.enemy_entry_step1.pack(side="left", padx=(8, 0))
            self.step1_guide.config(text="후픽이므로 상대 챔피언을 입력하세요.")
        else:
            self.enemy_label_step1.pack_forget()
            self.enemy_entry_step1.pack_forget()
            self.enemy_row_step1.pack_forget()
            self.step1_guide.config(text="선픽이므로 상대 챔피언 입력 없이 진행합니다.")

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

        self.set_status("픽 순서와 라인 선택")
        self.on_pick_change()
        self.root.update()

    def show_step2(self):
        self.current_step = 2
        self._hide_all_steps()
        self.step2_frame.pack(fill="both", expand=True)

        self.back_button.grid(row=0, column=0, sticky="ew", padx=4)
        self.next_button.config(text="다음")
        self.next_button.grid(row=0, column=1, sticky="ew", padx=4)

        self.set_status("챔피언 정보 입력")
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

    def wait_for_next(self):
        self._next_clicked = False
        while not self._next_clicked:
            self.root.update()
            self.root.after(50)

    def wait_for_back_or_next(self):
        self._next_clicked = False
        self._back_clicked = False

        while True:
            self.root.update()
            self.root.after(50)

            if self._back_clicked:
                return "back"
            if self._next_clicked:
                return "next"

    def tick(self):
        self.root.update()