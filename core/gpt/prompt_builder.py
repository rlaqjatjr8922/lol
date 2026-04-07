from pathlib import Path

from core.gpt.gpt_runner import run_prompt


def _normalize_name(template_name) -> str:
    if not template_name:
        return ""

    return Path(str(template_name)).stem.strip().lower()


def _resolve_lane_from_template_name(template_name) -> str:
    name = _normalize_name(template_name)

    if not name:
        return "미정"

    if "탑" in name or "top" in name:
        return "탑"

    if "정글" in name or "jungle" in name:
        return "정글"

    if "중단" in name or "미드" in name or "mid" in name:
        return "중단"

    if "바텀" in name or "원딜" in name or "bot" in name or "bottom" in name:
        return "바텀"

    if "서폿" in name or "서포터" in name or "support" in name or "sup" in name:
        return "서폿"

    return "미정"


def _normalize_frequent_champions(champs) -> str:
    if not champs:
        return "없음"

    if isinstance(champs, (list, tuple)):
        values = [str(x).strip() for x in champs if str(x).strip()]
        return ", ".join(values) if values else "없음"

    text = str(champs).strip()
    return text if text else "없음"


def build_ban_prompt(app_state):
    template_name = getattr(app_state, "matched_template_name", None)
    lane = _resolve_lane_from_template_name(template_name)

    champs = getattr(app_state, "frequent_champions", None)
    champs_text = _normalize_frequent_champions(champs)

    return f"""
와일드리프트 밴 단계

판별된 라인: {lane}
자주하는 챔피언: {champs_text}

밴 추천 3개만 아래 형식으로 출력

1. 챔피언 - 이유
2. 챔피언 - 이유
3. 챔피언 - 이유
""".strip()


def run_ban(app_state):
    prompt = build_ban_prompt(app_state)
    return run_prompt(prompt)