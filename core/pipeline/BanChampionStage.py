class BanChampionStage:
    def __init__(self, app_state, screen_source, roi_extractor, champion_detector):
        self.app_state = app_state
        self.screen_source = screen_source
        self.roi_extractor = roi_extractor
        self.champion_detector = champion_detector

    def run(self, stage_config):
        print("[BanChampionStage] 시작")

        frame = self.screen_source.capture()
        self.app_state.current_frame = frame

        pick_slots = stage_config["pick_slots"]

        roi_list = []
        for slot in pick_slots:
            roi = self.roi_extractor.extract(frame, slot)
            roi_list.append(roi)

        current_champions = []

        debug_stage = self.app_state.debug["BanChampionStage"]
        debug_stage["original"] = frame
        debug_stage["roi"] = []
        debug_stage["processed"] = []
        debug_stage["result"] = []

        for roi in roi_list:
            self.app_state.current_roi = roi

            if roi is not None:
                debug_stage["roi"].append(roi)

            champ_name = self.champion_detector.detect(roi, stage_config)

            last_debug = self.champion_detector.last_debug

            if last_debug is not None:
                roi_steps = last_debug.get("roi_steps", [])
                matched_template_steps = last_debug.get("matched_template_steps", [])

                for step_name, img in roi_steps:
                    if img is not None:
                        debug_stage["processed"].append(img)

                for step_name, img in matched_template_steps:
                    if img is not None:
                        debug_stage["processed"].append(img)

            debug_stage["result"].append(champ_name)
            current_champions.append(champ_name)

        print(f"[BanChampionStage] 현재 챔피언 = {current_champions}")

        if current_champions != self.app_state.ban_champions:
            print("[BanChampionStage] 변화 감지됨")
            print(f"[BanChampionStage] 이전 = {self.app_state.ban_champions}")

            self.app_state.ban_champions = current_champions
            return True

        print("[BanChampionStage] 변화 없음")
        return False