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

        self.detect_config_path = self.base_dir / "data" / "detect_stages.json"
        self.gpt_config_path = self.base_dir / "data" / "gpt_stages.json"

        self.detect_config = self._load_json(self.detect_config_path)
        self.gpt_config = self._load_json(self.gpt_config_path)

        self.detect_stages = self.detect_config["stages"]
        self.gpt_stages = self.gpt_config["gpt"]

        self.app_state.detect_stages = self.detect_stages
        self.app_state.gpt_stages = self.gpt_stages
        self.app_state.debug_dir = str(self.debug_dir)

        self._clear_debug()

        self.screen_source = ScreenSource()

        self.pipeline = PregamePipeline(
            app_state=self.app_state,
            screen_source=self.screen_source,
            detect_stages=self.detect_stages,
            gpt_stages=self.gpt_stages
        )

    def _load_json(self, path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _clear_debug(self):
        if self.debug_dir.exists():
            shutil.rmtree(self.debug_dir)
            print("[PregameController] debug 폴더 삭제")

        self.debug_dir.mkdir(parents=True, exist_ok=True)
        print("[PregameController] debug 폴더 생성")

    def run(self):
        print("[PregameController] run")

        self.screen_source.start()

        result = self.pipeline.run()

        if not result:
            raise RuntimeError("[PregameController] pipeline 실행 실패")

        print("[PregameController] done")