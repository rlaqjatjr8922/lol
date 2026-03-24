from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class LiveState:
    game_time: str = "?"
    team_kills: str = "?"
    enemy_kills: str = "?"
    my_kills: str = "?"
    my_deaths: str = "?"
    my_assists: str = "?"


@dataclass
class CoachResult:
    phase: str = "unknown"
    danger: str = "normal"
    tips: List[str] = field(default_factory=list)


def _to_int(value) -> Optional[int]:
    if value is None:
        return None

    text = str(value).strip()
    if not text or text == "?":
        return None

    try:
        return int(text)
    except ValueError:
        return None


def _parse_minute(game_time: str) -> Optional[int]:
    if not game_time or game_time == "?" or ":" not in game_time:
        return None

    try:
        mm, _ss = game_time.split(":", 1)
        return int(mm)
    except ValueError:
        return None


def _unique_keep_order(items: List[str]) -> List[str]:
    out = []
    seen = set()

    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)

    return out


class IngameCoach:
    def analyze(self, state: LiveState) -> CoachResult:
        minute = _parse_minute(state.game_time)
        team_kills = _to_int(state.team_kills)
        enemy_kills = _to_int(state.enemy_kills)
        my_kills = _to_int(state.my_kills)
        my_deaths = _to_int(state.my_deaths)
        my_assists = _to_int(state.my_assists)

        tips: List[str] = []
        phase = "unknown"
        danger = "normal"

        if minute is not None:
            if minute < 3:
                phase = "early"
                tips.append("초반 라인전 구간. 무리 교전보다 안전 운영")
            elif minute < 6:
                phase = "objective"
                tips.append("첫 오브젝트 구간. 드래곤/전령 쪽 합류 준비")
            elif minute < 10:
                phase = "mid"
                tips.append("교전 증가 구간. 혼자보다 팀 합류 우선")
            else:
                phase = "late"
                tips.append("중후반 구간. 혼자 다니지 말고 한타 위치 중요")

        if my_deaths is not None:
            if my_deaths >= 5:
                tips.append("데스가 많음. 공격보다 생존 우선")
                danger = "high"
            elif my_deaths >= 3:
                tips.append("무리 금지. 시야 없는 곳 진입 조심")
                if danger != "high":
                    danger = "medium"

        if my_kills is not None and my_deaths is not None:
            if my_kills >= 3 and my_deaths <= 1:
                tips.append("지금 강한 편. 아군과 같이 교전각 가능")
            elif my_kills >= 5 and my_deaths <= 2:
                tips.append("현재 캐리 가능 상태. 혼자 말고 팀과 같이 굴리기")

        if my_assists is not None and my_assists >= 5:
            tips.append("합류 기여 높음. 계속 팀 중심 플레이 유지")

        if team_kills is not None and enemy_kills is not None:
            diff = team_kills - enemy_kills

            if diff <= -5:
                tips.append("팀이 많이 불리함. 정면 교전보다 받아먹기")
                danger = "high"
            elif diff < 0:
                tips.append("팀이 불리함. 숫자 부족 싸움 금지")
                if danger == "normal":
                    danger = "medium"
            elif diff >= 5:
                tips.append("팀이 많이 유리함. 오브젝트 압박 가능")
            elif diff > 0:
                tips.append("팀이 살짝 유리함. 먼저 자리 잡고 싸우기")

        if minute is not None and minute >= 10 and my_deaths is not None and my_deaths >= 3:
            tips.append("지금부터 한 번 죽는 가치가 큼. 절대 먼저 물리지 말기")

        tips = _unique_keep_order(tips)[:3]

        return CoachResult(
            phase=phase,
            danger=danger,
            tips=tips
        )


_default_coach = IngameCoach()


def analyze_ingame(state) -> CoachResult:
    if isinstance(state, dict):
        live_state = LiveState(
            game_time=state.get("game_time", "?"),
            team_kills=state.get("team_kills", "?"),
            enemy_kills=state.get("enemy_kills", "?"),
            my_kills=state.get("my_kills", "?"),
            my_deaths=state.get("my_deaths", "?"),
            my_assists=state.get("my_assists", "?"),
        )
    else:
        live_state = LiveState(
            game_time=getattr(state, "game_time", "?"),
            team_kills=getattr(state, "team_kills", "?"),
            enemy_kills=getattr(state, "enemy_kills", "?"),
            my_kills=getattr(state, "my_kills", "?"),
            my_deaths=getattr(state, "my_deaths", "?"),
            my_assists=getattr(state, "my_assists", "?"),
        )

    return _default_coach.analyze(live_state)


def format_result(result: CoachResult) -> str:
    lines = [
        f"[단계] {result.phase}",
        f"[위험도] {result.danger}",
        "[코칭]",
    ]

    if result.tips:
        for tip in result.tips:
            lines.append(f"- {tip}")
    else:
        lines.append("- 판단 정보 부족")

    return "\n".join(lines)


def run_ingame():
    print("=== 인게임 코치 실행 ===")

    # 실시간 OCR 창 실행
    from core.realtime_ingame import run_ingame as realtime_run
    realtime_run()