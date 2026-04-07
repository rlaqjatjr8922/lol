from pathlib import Path
import json
import shutil

from core.capture.screen_source import ScreenSource
from core.pipeline.pregame_pipeline import PregamePipeline


class PregameController:
    def __init__(self, app_state):
        self.app_state = app_state

        self.base_dir = Path(__file__).resolve().parents[1]
        self.debug_dir = self.base_dir / "debug"
        self.setting_path = self.base_dir / "data" / "setting.json"

        self.debug_enabled = self._load_debug_setting()

        self.app_state.debug_enabled = self.debug_enabled
        self.app_state.debug_dir = str(self.debug_dir)

        self._clear_debug()

        self.screen_source = ScreenSource()
        self.pipeline = PregamePipeline(app_state, self.screen_source)

    def _load_debug_setting(self):
        if self.setting_path.exists():
            with open(self.setting_path, "r", encoding="utf-8") as f:
                setting = json.load(f)
            return setting.get("debug", True)
        return True

    def _clear_debug(self):
        if self.debug_dir.exists():
            shutil.rmtree(self.debug_dir)
            print("[PregameController] debug 폴더 삭제")

        if self.debug_enabled:
            self.debug_dir.mkdir(parents=True, exist_ok=True)
            print("[PregameController] debug 폴더 생성")
        else:
            print("[PregameController] debug OFF")

    def run(self):
        print("[PregameController] run")

        print("1. 화면 캡처 시작")
        self.screen_source.start()

        print("2. pregame_pipeline 실행")
        self.pipeline.run()

        print("[PregameController] done")