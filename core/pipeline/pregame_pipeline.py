import time

from core.pipeline.TextStage import TextStage
from core.pipeline.GPTStage import GPTStage
from core.pipeline.StickStage import StickStage
from core.pipeline.BanChampionStage import BanChampionStage
from core.pipeline.UIStage import UIStage

from core.vision.roi_extractor import ROIExtractor
from core.vision.stick_checker import StickChecker
from core.vision.text_template_checker import TextTemplateChecker
from core.vision.champion_image_detector import ChampionImageDetector


class PregamePipeline:
    def __init__(self, app_state, screen_source, detect_stages, gpt_stages):
        self.app_state = app_state
        self.screen_source = screen_source

        self.detect_stages = detect_stages
        self.gpt_stages = gpt_stages

        self.roi_extractor = ROIExtractor()
        self.text_checker = TextTemplateChecker()
        self.stick_checker = StickChecker()
        self.champion_detector = ChampionImageDetector()

        self.text_stage = TextStage(
            self.app_state,
            self.screen_source,
            self.roi_extractor,
            self.text_checker
        )

        self.gpt_stage = GPTStage(
            self.app_state,
            self.gpt_stages
        )

        self.stick_stage = StickStage(
            self.app_state,
            self.screen_source,
            self.roi_extractor,
            self.stick_checker
        )

        self.ban_champion_stage = BanChampionStage(
            self.app_state,
            self.screen_source,
            self.roi_extractor,
            self.champion_detector
        )

        self.ui_stage = UIStage(
            self.app_state
        )

    def run(self):
        print("[PregamePipeline] 시작")

        while True:
            current_stage = self.app_state.stage
            print(f"[PregamePipeline] 현재 stage = {current_stage}")

            # 0단계: 첫 화면 텍스트/템플릿 감지
            if current_stage == 0:
                print("[PregamePipeline] TextStage 0 시도")
                self.text_stage.run(self.detect_stages["0"])

            # 1단계: 상대 선택 중 감지 -> GPT 1 -> UI
            elif current_stage == 1:
                print("[PregamePipeline] TextStage 1 시도")

                if self.text_stage.run(self.detect_stages["1"]):
                    print("[PregamePipeline] TextStage 1 성공")

                    print("[PregamePipeline] GPTStage 1 시도")
                    if self.gpt_stage.run("1"):
                        print("[PregamePipeline] GPTStage 1 성공")
                        self.ui_stage.run()

            # 2단계: 턴 바 / 픽 상태 감지 -> 챔피언 분석 -> GPT 2 -> UI
            elif current_stage == 2:
                print("[PregamePipeline] StickStage 2 시도")

                if self.stick_stage.run(self.detect_stages["2"]):
                    print("[PregamePipeline] StickStage 2 성공")

                    print("[PregamePipeline] BanChampionStage 2 시도")
                    self.ban_champion_stage.run(self.detect_stages["2"])

                    print("[PregamePipeline] GPTStage 2 시도")
                    if self.gpt_stage.run("2"):
                        print("[PregamePipeline] GPTStage 2 성공")
                        self.ui_stage.run()

            # 3단계: 마지막 GPT 추천 -> UI -> 종료
            elif current_stage == 3:
                print("[PregamePipeline] GPTStage 3 시도")

                if self.gpt_stage.run("3"):
                    print("[PregamePipeline] GPTStage 3 성공")
                    self.ui_stage.run()

                print("[PregamePipeline] 완료")
                return True

            else:
                print("[PregamePipeline] 알 수 없는 stage")
                print("[PregamePipeline] 완료")
                return True

            time.sleep(0.1)