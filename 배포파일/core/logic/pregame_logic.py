from core.data.champion_mapper import champion_to_english, champion_to_korean
from core.data.item_mapper import item_to_korean
from core.data.rune_mapper import rune_to_korean, english_tree_to_korean
from core.data.spell_mapper import spells_to_korean
from core.gpt.gpt_service import ask_blind_pick, ask_counter_pick, ask_build
from core.utils.text_utils import safe_text, trim_text


def recommend_blind_pick(lane_ko: str):
    data = ask_blind_pick(lane_ko)

    champ_en = safe_text(data.get("champion"), "오류")
    reason = trim_text(data.get("reason"), 120, "오류")

    return {
        "추천 챔피언": champion_to_korean(champ_en),
        "추천 이유": reason,
        "champion": champion_to_korean(champ_en),
        "reason": reason,
    }


def recommend_counter(enemy_champ_ko: str, lane_ko: str):
    enemy_champ_en = champion_to_english(enemy_champ_ko)
    data = ask_counter_pick(enemy_champ_en, lane_ko)

    champ_en = safe_text(data.get("champion"), "오류")
    reason = trim_text(data.get("reason"), 120, "오류")

    return {
        "추천 챔피언": champion_to_korean(champ_en),
        "추천 이유": reason,
        "champion": champion_to_korean(champ_en),
        "reason": reason,
    }


def recommend_build(my_champ_ko: str, enemy_champ_ko: str, lane_ko: str):
    my_champ_en = champion_to_english(my_champ_ko)
    enemy_champ_en = champion_to_english(enemy_champ_ko)

    data = ask_build(my_champ_en, enemy_champ_en, lane_ko)

    return {
        "핵심룬": rune_to_korean(data.get("Keystone", "")),
        "메인특성 세트": english_tree_to_korean(data.get("Primary Tree", "")),
        "메인특성1": rune_to_korean(data.get("Rune1", "")),
        "메인특성2": rune_to_korean(data.get("Rune2", "")),
        "메인특성3": rune_to_korean(data.get("Rune3", "")),
        "보조특성세트": english_tree_to_korean(data.get("Secondary Tree", "")),
        "보조특성1": rune_to_korean(data.get("Secondary Rune", "")),
        "스팰": spells_to_korean(data.get("Spells", "")),
        "시작아탬": item_to_korean(data.get("Starting Item", "")),
        "첫완성탬": item_to_korean(data.get("First Item", "")),
        "초반 운영": safe_text(data.get("Early Game Plan", ""), "오류"),
    }