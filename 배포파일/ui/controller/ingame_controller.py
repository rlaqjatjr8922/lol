import os
import tkinter as tk

from core.flow.ingame_flow import run_ingame_once
from device.device_state import DeviceState
from device.capture import load_image_list
from ui.view.ingame_view import IngameView


class IngameController:
    def __init__(self, ingame_view):
        self.view = ingame_view
        self.device_state = DeviceState()
        self.image_paths = load_image_list(self.device_state.screenshot_dir)
        self.current_index = 0

        self.view.prev_btn.config(command=self.prev_image)
        self.view.run_btn.config(command=self.process_current_image)
        self.view.next_btn.config(command=self.next_image)

        root = self.view.winfo_toplevel()
        root.bind("<Left>", lambda e: self.prev_image())
        root.bind("<Right>", lambda e: self.next_image())

        if self.image_paths:
            self.process_current_image()
        else:
            self.view.set_status_bar("이미지 없음")
            self.view.set_state_text(
                current_index=0,
                total_count=0,
                game_time="?",
                team_kills="?",
                enemy_kills="?",
                my_kills="?",
                my_deaths="?",
                my_assists="?",
                last_error=f"폴더에 이미지가 없음: {self.device_state.screenshot_dir}",
            )

    def refresh_images(self):
        self.image_paths = load_image_list(self.device_state.screenshot_dir)
        if self.current_index >= len(self.image_paths):
            self.current_index = max(0, len(self.image_paths) - 1)

    def process_current_image(self):
        self.refresh_images()

        if not self.image_paths:
            self.view.set_status_bar("이미지 없음")
            self.view.set_state_text(
                current_index=0,
                total_count=0,
                game_time="?",
                team_kills="?",
                enemy_kills="?",
                my_kills="?",
                my_deaths="?",
                my_assists="?",
                last_error=f"폴더에 이미지가 없음: {self.device_state.screenshot_dir}",
            )
            return

        state, result, extra = run_ingame_once(
            self.device_state,
            use_gpt=False,
            image_path=self.image_paths[self.current_index]
        )

        total = len(self.image_paths)
        current = self.current_index + 1

        if state is None:
            self.view.set_status_bar("분석 실패")
            self.view.set_state_text(
                current_index=current,
                total_count=total,
                game_time="?",
                team_kills="?",
                enemy_kills="?",
                my_kills="?",
                my_deaths="?",
                my_assists="?",
                last_error=str(extra),
            )
            return

        debug = extra if isinstance(extra, dict) else {}
        basename = os.path.basename(self.image_paths[self.current_index])

        self.view.set_status_bar(basename)
        self.view.set_state_text(
            current_index=current,
            total_count=total,
            game_time=state.game_time,
            team_kills=state.team_kills,
            enemy_kills=state.enemy_kills,
            my_kills=state.my_kills,
            my_deaths=state.my_deaths,
            my_assists=state.my_assists,
            raw_time_text=state.raw_time_text,
            raw_score_text=state.raw_score_text,
            raw_kda_text=state.raw_kda_text,
            last_error=state.last_error,
        )
        self.view.set_crops(debug)

    def next_image(self):
        self.refresh_images()
        if not self.image_paths:
            return

        self.current_index += 1
        if self.current_index >= len(self.image_paths):
            self.current_index = 0

        self.process_current_image()

    def prev_image(self):
        self.refresh_images()
        if not self.image_paths:
            return

        self.current_index -= 1
        if self.current_index < 0:
            self.current_index = len(self.image_paths) - 1

        self.process_current_image()


def run_ingame_app():
    root = tk.Tk()
    root.title("Wild Rift 폴더 이미지 분석")
    root.geometry("1100x820+400+40")
    root.configure(bg="#111111")

    ingame_view = IngameView(root)
    ingame_view.pack(fill="both", expand=True)

    IngameController(ingame_view)

    root.mainloop()