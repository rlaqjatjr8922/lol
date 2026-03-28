from typing import Optional

from core.gpt.gpt_service import ask_ingame_coach
from core.model.coach_result import CoachResult
from core.model.ingame_state import IngameState


def to_int_or_none(value: str) -> Optional[int]:
    try:
        return int(str(value).strip())
    except Exception:
        return None


def analyze_ingame_state(state: IngameState, use_gpt: bool = False) -> CoachResult:
    my_kills = to_int_or_none(state.my_kills)
    my_deaths = to_int_or_none(state.my_deaths)
    my_assists = to_int_or_none(state.my_assists)
    team_kills = to_int_or_none(state.team_kills)
    enemy_kills = to_int_or_none(state.enemy_kills)

    tips = []
    danger = "normal"

    if my_deaths is not None:
        if my_deaths >= 5:
            tips.append("데스가 많음. 공격보다 생존 우선")
            danger = "high"
        elif my_deaths >= 3:
            tips.append("무리 금지. 시야 없는 곳 진입 조심")
            danger = "medium"

    if my_kills is not None and my_deaths is not None:
        if my_kills >= 5 and my_deaths <= 2:
            tips.append("캐리 가능 상태. 혼자 말고 팀이랑 같이 굴리기")
        elif my_kills >= 3 and my_deaths <= 1:
            tips.append("지금 강한 편. 아군과 같이 교전각 가능")

    if my_assists is not None and my_assists >= 5:
        tips.append("합류 기여 높음. 계속 팀 중심 플레이 유지")

    if team_kills is not None and enemy_kills is not None:
        diff = team_kills - enemy_kills

        if diff <= -5:
            tips.append("팀이 많이 불리함. 정면 교전보다 받아먹기")
            danger = "high"
        elif diff < 0:
            tips.append("약간 불리함. 먼저 여는 싸움 조심")
            if danger == "normal":
                danger = "medium"
        elif diff >= 5:
            tips.append("팀이 유리함. 오브젝트 시야 먼저 잡고 굴리기")
        else:
            tips.append("큰 차이 없음. 숫자 우위일 때만 교전")

    if not tips:
        tips.append("정보 부족. 안전하게 라인/오브젝트 중심 운영")

    if use_gpt:
        kda_text = f"{state.my_kills}/{state.my_deaths}/{state.my_assists}"
        gpt_tips = ask_ingame_coach(
            state.game_time,
            state.team_kills,
            state.enemy_kills,
            kda_text,
        )
        if gpt_tips:
            tips.extend(gpt_tips[:3])

    return CoachResult(
        title=f"{state.game_time} / {state.team_kills}:{state.enemy_kills} / {state.my_kills}-{state.my_deaths}-{state.my_assists}",
        summary="인게임 코치 결과",
        tips=tips,
        danger=danger,
    )