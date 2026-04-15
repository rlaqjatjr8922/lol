from pathlib import Path
import json
import shutil

from core.capture.screen_source import ScreenSource
from core.pipeline.pregame_pipeline import PregamePipeline
from core.gpt.browser import GPTBrowser


class PregameController:
    def __init__(self, app_state):
        self.app_state = app_state

        self.base_dir = Path(__file__).resolve().parents[1]
        self.debug_dir = self.base_dir / "debug"

        self.detect_config_path = self.base_dir / "data" / "detect.json"
        self.gpt_config_path = self.base_dir / "data" / "gpt.json"

        self.detect_config = self._load_json(self.detect_config_path)
        self.gpt_config = self._load_json(self.gpt_config_path)

        self.detect_stages = self.detect_config["stages"]
        self.gpt_stages = self.gpt_config["gpt"]

        self.app_state.detect_stages = self.detect_stages
        self.app_state.gpt_stages = self.gpt_stages

        self.GPTbrowser = GPTBrowser()
        self.screen_source = ScreenSource()

        self.pipeline = PregamePipeline(
            app_state=self.app_state,
            screen_source=self.screen_source,
            detect_stages=self.detect_stages,
            gptjson=self.gpt_stages,
            gpt_browser=self.GPTbrowser
        )

    def _load_json(self, path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _reset_debug_dir(self):
        if self.debug_dir.exists():
            shutil.rmtree(self.debug_dir)

        self.debug_dir.mkdir(parents=True, exist_ok=True)

        structure = {
            "stage_0": ["TextStage"],
            "stage_1": ["TextStage", "BanChampionStage"],
            "stage_2": ["TextStage", "BanChampionStage", "StickStage"],
        }

        subfolders = ["original", "roi", "processed", "result"]

        for stage_name, stage_classes in structure.items():
            for stage_class in stage_classes:
                for subfolder in subfolders:
                    folder_path = self.debug_dir / stage_name / stage_class / subfolder
                    folder_path.mkdir(parents=True, exist_ok=True)

    def run(self):
        print("[PregameController] run")

        self._reset_debug_dir()

        self.GPTbrowser.start_and_connect()

        self.screen_source.start()

        result = self.pipeline.run()

        if not result:
            raise RuntimeError("[PregameController] pipeline 실행 실패")

        print("[PregameController] done")