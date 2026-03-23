from ui.coach_window import CoachWindow
from core.pregame_coach import recommend_blind_pick, recommend_counter, recommend_build


def safe_text(value: str) -> str:
    text = (value or "").strip()
    return text if text else "오류"


def build_text_from_build(build: dict) -> str:
    return "\n".join([
        f"핵심 룬: {safe_text(build.get('Keystone', '오류'))}",
        f"특성 세트: {safe_text(build.get('Tree', '오류'))}",
        f"룬 1: {safe_text(build.get('Rune1', '오류'))}",
        f"룬 2: {safe_text(build.get('Rune2', '오류'))}",
        f"룬 3: {safe_text(build.get('Rune3', '오류'))}",
        f"보조 특성 세트: {safe_text(build.get('SecondaryTree', '오류'))}",
        f"보조 특성: {safe_text(build.get('Secondary', '오류'))}",
        f"스펠: {safe_text(build.get('Spells', '오류'))}",
        f"시작 아이템: {safe_text(build.get('Starting Items', '오류'))}",
    ])


def trim_reason(reason: str, max_len: int = 120) -> str:
    text = (reason or "").strip()
    if not text:
        return "오류"
    if len(text) > max_len:
        return text[:max_len] + "..."
    return text


def run_pregame_then_ingame():
    window = CoachWindow()

    while True:
        # --------------------------
        # 1단계
        # --------------------------
        window.show_step1()
        window.wait_for_next()

        inputs = window.get_inputs()
        pick_order = safe_text(inputs.get("pick_order", "오류"))
        lane_step1 = safe_text(inputs.get("lane", "오류"))
        enemy_champ_step1 = safe_text(inputs.get("enemy_champ", "오류"))

        # --------------------------
        # 2단계
        # --------------------------
        window.show_step2()
        window.show_waiting_in_step2("GPT 응답 대기중...\n챔피언 추천 불러오는 중")

        if pick_order == "선픽":
            rec = recommend_blind_pick(lane_step1)
        else:
            rec = recommend_counter(enemy_champ_step1, lane_step1)

        recommended = safe_text(rec.get("추천 챔피언", "오류"))
        reason = trim_reason(rec.get("추천 이유", "오류"))
        window.set_recommendation(recommended, reason)

        decision = window.wait_for_back_or_next()
        if decision == "back":
            continue

        inputs = window.get_inputs()
        my_champ = safe_text(inputs.get("my_champ", "오류"))
        enemy_champ = safe_text(inputs.get("enemy_champ", "오류"))
        lane = safe_text(inputs.get("lane", lane_step1))

        if my_champ == "오류" and recommended != "오류":
            my_champ = recommended

        if enemy_champ == "오류" and enemy_champ_step1 != "오류":
            enemy_champ = enemy_champ_step1

        # --------------------------
        # 3단계
        # --------------------------
        window.show_step3()
        window.show_waiting_in_step3("GPT 응답 대기중...\n룬 추천 계산중")

        build = recommend_build(my_champ, enemy_champ, lane)

        result_title = "\n".join([
            f"추천 챔피언: {recommended}",
            f"[{pick_order}] {my_champ} vs {enemy_champ} ({lane})"
        ])
        result_body = build_text_from_build(build)
        result_plan = f"초반 운영: {safe_text(build.get('초반 운영', '오류'))}"

        window.set_result(result_title, result_body, result_plan)

        while True:
            result_decision = window.wait_for_back_or_next()

            if result_decision == "back":
                break

            if result_decision == "next":
                window.set_status("프리게임 완료")
                return