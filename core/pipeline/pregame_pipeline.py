import time

from core.pipeline.DetectStage import DetectStage
from core.pipeline.GPTStage import GPTStage
from core.pipeline.stages import StickStage
from core.vision.roi_extractor import ROIExtractor
from core.vision.stick_checker import StickChecker
from core.vision.text_template_checker import TextTemplateChecker


class PregamePipeline:
    def __init__(self, app_state, screen_source, stages):
        self.app_state = app_state
        self.screen_source = screen_source
        self.stages_config = stages

        self.roi_extractor = ROIExtractor()
        self.text_checker = TextTemplateChecker()
        self.stick_checker = StickChecker(debug=False, slot_count=5)

        # 단계별 객체 생성
        self.detect0 = DetectStage("0", self.stages_config, self.roi_extractor, self.text_checker)
        self.detect1 = DetectStage("1", self.stages_config, self.roi_extractor, self.text_checker)
        self.gpt = GPTStage()
        self.stick_stage = StickStage("2", self.stages_config, self.roi_extractor)

    def run(self):
        print("[Pipeline] 시작")

        while True:
            if self.app_state.a == 0:
                self.detect0.run()
                print("[Pipeline] DetectStage 0 시도")

            elif self.app_state.a == 1:
                self.gpt.run()
                print("[Pipeline] gpt 1 시도")
                self.detect.run()
                print("[Pipeline] DetectStage 1 시도")
            elif self.app_state.a == 2:
                self.stick_stage.run()
                print("[Pipeline] StickStage 2 시도")

            else:
                print("[Pipeline] 완료")
                return True
