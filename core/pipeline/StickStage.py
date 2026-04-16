class StickStage:
    def __init__(self, app_state, screen_source, roi_extractor, stick_checker):
        self.app_state = app_state
        self.screen_source = screen_source
        self.roi_extractor = roi_extractor
        self.stick_checker = stick_checker

    def _convert_slots_to_bars(self, slots, slot_ratios, color_name):
        bars = []
        for slot in slots:
            strength = slot_ratios.get(slot, 0.0)
            bars.append((slot - 1, color_name, strength))
        return bars

    def _merge_duplicate_bars(self, bars):
        merged = {}
        for idx, color, strength in bars:
            if idx not in merged or strength > merged[idx][2]:
                merged[idx] = (idx, color, strength)
        return sorted(merged.values(), key=lambda x: x[0])

    def run(self, stage_config):
        print("[StickStage] 시작")

        frame = self.screen_source.capture()
        if frame is None:
            print("[StickStage] frame 없음")
            return False

        ally_roi = self.roi_extractor.extract(frame, stage_config.get("ally_turn_bar_roi"))
        enemy_roi = self.roi_extractor.extract(frame, stage_config.get("enemy_turn_bar_roi"))

        if ally_roi is None or enemy_roi is None:
            print("[StickStage] ROI 추출 실패")
            return False

        raw_lit_bars = self.stick_checker.check(
            ally_roi,
            enemy_roi,
            colors=["blue", "yellow", "red"],
            stage_config=stage_config,
        )

        info = self.stick_checker.last_info
        if not info:
            print("[StickStage] last_info 없음")
            return False

        blue_slots = info.get("blue_slots", [])
        yellow_slots = info.get("yellow_slots", [])
        red_slots = info.get("red_slots", [])

        blue_slot_ratios = info.get("blue_slot_ratios", {})
        yellow_slot_ratios = info.get("yellow_slot_ratios", {})
        red_slot_ratios = info.get("red_slot_ratios", {})

        ally_bars = []
        ally_bars.extend(self._convert_slots_to_bars(blue_slots, blue_slot_ratios, "blue"))
        ally_bars.extend(self._convert_slots_to_bars(yellow_slots, yellow_slot_ratios, "yellow"))
        ally_bars = self._merge_duplicate_bars(ally_bars)

        enemy_bars = self._convert_slots_to_bars(red_slots, red_slot_ratios, "red")
        enemy_bars = self._merge_duplicate_bars(enemy_bars)

        pick_turn_team = info.get("pick_turn_team")
        is_my_turn = info.get("is_my_turn", False)

        if pick_turn_team == "enemy":
            turn_owner = "enemy"
        elif pick_turn_team == "ally":
            turn_owner = "me" if is_my_turn else "team"
        else:
            turn_owner = None

        ally_active_slots = tuple(info.get("ally_active_slots", []))
        enemy_active_slots = tuple(info.get("enemy_active_slots", []))

        self.app_state.lit_bars = [ally_bars, enemy_bars, turn_owner]
        self.app_state.lit_bars_calc = [ally_active_slots, enemy_active_slots]

        self.app_state.pick_turn_team = pick_turn_team
        self.app_state.is_my_turn = is_my_turn
        self.app_state.pick_order = info.get("pick_order")
        self.app_state.stick_last_info = info

        print("lit_bars =", self.app_state.lit_bars)
        print("lit_bars_calc =", self.app_state.lit_bars_calc)
        print("pick_turn_team =", pick_turn_team)
        print("is_my_turn =", is_my_turn)
        print("pick_order =", self.app_state.pick_order)
        print("raw_lit_bars =", raw_lit_bars)

        return (
            len(ally_bars) > 0
            or len(enemy_bars) > 0
            or turn_owner is not None
            or len(ally_active_slots) > 0
            or len(enemy_active_slots) > 0
        )