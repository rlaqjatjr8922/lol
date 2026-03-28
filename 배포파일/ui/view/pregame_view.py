import tkinter as tk
from tkinter import ttk


class PregameView(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg="#111111")

        self.pick_order_var = tk.StringVar(value="선픽")
        self.my_champ_var = tk.StringVar(value="")
        self.enemy_champ_var = tk.StringVar(value="")
        self.lane_var = tk.StringVar(value="탑")

        title = tk.Label(
            self,
            text="Wild Rift Pregame Coach",
            fg="white",
            bg="#111111",
            font=("맑은 고딕", 16, "bold"),
        )
        title.pack(pady=(12, 8))

        self.status_label = tk.Label(
            self,
            text="대기중",
            fg="#bbbbbb",
            bg="#111111",
            font=("맑은 고딕", 10),
        )
        self.status_label.pack(anchor="w", padx=16)

        form = tk.Frame(self, bg="#111111")
        form.pack(fill="x", padx=16, pady=12)

        self._make_combo(form, "픽 순서", self.pick_order_var, ["선픽", "후픽"]).pack(fill="x", pady=4)
        self._make_combo(form, "라인", self.lane_var, ["탑", "정글", "미드", "원딜", "서폿"]).pack(fill="x", pady=4)
        self._make_entry(form, "내 챔피언", self.my_champ_var).pack(fill="x", pady=4)
        self._make_entry(form, "상대 챔피언", self.enemy_champ_var).pack(fill="x", pady=4)

        self.rec_title = tk.Label(
            self,
            text="추천 챔피언: -",
            fg="white",
            bg="#111111",
            font=("맑은 고딕", 12, "bold"),
        )
        self.rec_title.pack(anchor="w", padx=16, pady=(16, 8))

        self.reason_text = tk.Text(self, height=4, bg="#222222", fg="white")
        self.reason_text.pack(fill="x", padx=16)

        self.result_text = tk.Text(self, height=14, bg="#222222", fg="white")
        self.result_text.pack(fill="both", expand=True, padx=16, pady=16)

    def _make_combo(self, master, label_text, variable, values):
        row = tk.Frame(master, bg="#111111")
        tk.Label(row, text=label_text, fg="white", bg="#111111", width=10, anchor="w").pack(side="left")
        ttk.Combobox(row, textvariable=variable, values=values, state="readonly", width=24).pack(side="left", padx=(8, 0))
        return row

    def _make_entry(self, master, label_text, variable):
        row = tk.Frame(master, bg="#111111")
        tk.Label(row, text=label_text, fg="white", bg="#111111", width=10, anchor="w").pack(side="left")
        tk.Entry(row, textvariable=variable, width=28).pack(side="left", padx=(8, 0))
        return row

    def get_inputs(self):
        return {
            "pick_order": self.pick_order_var.get().strip(),
            "lane": self.lane_var.get().strip(),
            "my_champ": self.my_champ_var.get().strip(),
            "enemy_champ": self.enemy_champ_var.get().strip(),
        }

    def set_status(self, text: str):
        self.status_label.config(text=text)

    def set_recommendation(self, champion: str, reason: str):
        self.rec_title.config(text=f"추천 챔피언: {champion}")
        self.reason_text.delete("1.0", "end")
        self.reason_text.insert("1.0", reason)

    def set_build_result(self, title: str, body: str, plan: str):
        self.result_text.delete("1.0", "end")
        self.result_text.insert("1.0", f"{title}\n\n{body}\n\n{plan}")