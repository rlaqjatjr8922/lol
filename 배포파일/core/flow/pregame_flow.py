from core.logic.pregame_logic import recommend_blind_pick, recommend_counter, recommend_build
from core.model.draft_input import DraftInput
from core.utils.format_utils import build_pregame_result_text
from core.utils.text_utils import safe_text, trim_text


def run_pregame_step2(draft: DraftInput):
    if draft.pick_order == "선픽":
        rec = recommend_blind_pick(draft.lane)
    else:
        rec = recommend_counter(draft.enemy_champ, draft.lane)

    recommended = safe_text(
        rec.get("champion") or rec.get("추천 챔피언"),
        "오류",
    )
    reason = trim_text(
        rec.get("reason") or rec.get("추천 이유"),
        120,
        "오류",
    )

    return recommended, reason


def run_pregame_step3(draft: DraftInput, recommended: str):
    my_champ = draft.my_champ.strip() or recommended
    build = recommend_build(my_champ, draft.enemy_champ, draft.lane)

    title = "\n".join([
        f"추천 챔피언: {recommended}",
        f"[{draft.pick_order}] {my_champ} vs {draft.enemy_champ} ({draft.lane})",
    ])
    body = build_pregame_result_text(build)
    plan = f"초반 운영: {safe_text(build.get('초반 운영'), '오류')}"

    return title, body, plan