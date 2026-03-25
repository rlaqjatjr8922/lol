from core.flow.pregame_flow import run_pregame_step2, run_pregame_step3
from core.model.draft_input import DraftInput


class PregameController:
    def __init__(self, view):
        self.view = view
        self.view.next_button.config(command=self.on_next)
        self.view.back_button.config(command=self.on_back)

    def on_next(self):
        try:
            if self.view.current_step == 1:
                self._handle_step1_next()
            elif self.view.current_step == 2:
                self._handle_step2_next()
            elif self.view.current_step == 3:
                self._handle_step3_next()
        except Exception as e:
            self.view.set_status(f"다음 처리 실패: {e}")

    def on_back(self):
        try:
            if self.view.current_step == 2:
                self.view.show_step1()
            elif self.view.current_step == 3:
                self.view.show_step2()
        except Exception as e:
            self.view.set_status(f"뒤로 처리 실패: {e}")

    def _handle_step1_next(self):
        inputs = self.view.get_inputs()

        pick_order = (inputs.get("pick_order") or "").strip()
        lane = (inputs.get("lane") or "").strip()
        enemy_champ = (inputs.get("enemy_champ") or "").strip()

        if not lane:
            self.view.set_status("라인 선택 필요")
            return

        if pick_order == "후픽" and not enemy_champ:
            self.view.set_status("후픽은 상대 챔피언 입력 필요")
            return

        self.view.show_step2()
        self.view.show_waiting_in_step2("추천 계산중...")

        draft = DraftInput(
            pick_order=pick_order,
            lane=lane,
            my_champ=(inputs.get("my_champ") or "").strip(),
            enemy_champ=enemy_champ,
        )

        try:
            recommended, reason = run_pregame_step2(draft)
            self.view.set_recommendation(recommended, reason)
            self.view.set_status("추천 챔피언 확인")
        except Exception as e:
            self.view.set_recommendation("오류", str(e))
            self.view.set_status(f"추천 실패: {e}")

    def _handle_step2_next(self):
        inputs = self.view.get_inputs()

        pick_order = (inputs.get("pick_order") or "").strip()
        enemy_champ = (inputs.get("enemy_champ") or "").strip()
        my_champ = (inputs.get("my_champ") or "").strip()
        recommended = (self.view.recommend_value.cget("text") or "").strip()

        if pick_order == "후픽" and not enemy_champ:
            self.view.set_status("후픽은 상대 챔피언 입력해야 다음으로 이동 가능")
            return

        final_my_champ = my_champ if my_champ else recommended

        if not final_my_champ or final_my_champ == "오류":
            self.view.set_status("내 챔피언이 비어 있고 추천값도 없음")
            return

        if not my_champ:
            self.view.my_champ_var.set(final_my_champ)

        self.view.show_step3()
        self.view.show_waiting_in_step3("룬/스펠/아이템 계산중...")

        draft = DraftInput(
            pick_order=pick_order,
            lane=(inputs.get("lane") or "").strip(),
            my_champ=final_my_champ,
            enemy_champ=enemy_champ,
        )

        try:
            title, body, plan = run_pregame_step3(draft, recommended or final_my_champ)
            self.view.set_result(title, body, plan)
            self.view.set_status("데이터 생성 완료 / 게임 시작 버튼 누르세요")
        except Exception as e:
            self.view.set_result("오류", str(e), "")
            self.view.set_status(f"빌드 추천 실패: {e}")

    def _handle_step3_next(self):
        try:
            self.view.set_status("인게임 코치창 여는 중...")
            self.view.root.update()

            self.view.root.destroy()

            from ui.controller.ingame_controller import run_ingame_app
            run_ingame_app()

        except Exception as e:
            try:
                self.view.set_status(f"게임 시작 처리 실패: {e}")
            except Exception:
                print(f"게임 시작 처리 실패: {e}")