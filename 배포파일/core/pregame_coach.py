from __future__ import annotations

import json
import os
import re
from typing import Dict, Set

from gpt.chatgpt_web_bridge import ask_chatgpt


def normalize_lane_ui_to_gpt(lane_text: str) -> str:
    mapping = {
        "탑": "top",
        "정글": "jungle",
        "미드": "mid",
        "원딜": "dragon",
        "서폿": "support",
    }
    return mapping.get((lane_text or "").strip(), "top")


def get_project_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_data_path(filename: str) -> str:
    return os.path.join(get_project_root(), "Data", filename)


def load_json(filename: str, default):
    path = get_data_path(filename)

    if not os.path.exists(path):
        print(f"[경고] 파일 없음: {path}")
        return default

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[경고] JSON 로드 실패: {path} / {e}")
        return default


def load_rune_db() -> Dict[str, Set[str]]:
    raw = load_json("Rune.json", {})
    result: Dict[str, Set[str]] = {}

    if not isinstance(raw, dict):
        return {
            "keystone": set(),
            "precision": set(),
            "domination": set(),
            "resolve": set(),
            "inspiration": set(),
        }

    for key, value in raw.items():
        key_lower = str(key).strip().lower()
        if isinstance(value, list):
            result[key_lower] = {str(x).strip() for x in value if str(x).strip()}
        else:
            result[key_lower] = set()

    for key in ["keystone", "precision", "domination", "resolve", "inspiration"]:
        result.setdefault(key, set())

    return result


def load_translation_map(filename: str) -> Dict[str, str]:
    raw = load_json(filename, {})
    if not isinstance(raw, dict):
        return {}

    result: Dict[str, str] = {}
    for k, v in raw.items():
        ks = str(k).strip()
        vs = str(v).strip()
        if ks and vs:
            result[ks] = vs
    return result


def load_champion_db() -> Set[str]:
    raw = load_json("Champion.json", [])
    if isinstance(raw, list):
        return {str(x).strip() for x in raw if str(x).strip()}
    return set()


def load_spell_db() -> Set[str]:
    raw = load_json("Spells.json", {})
    if isinstance(raw, dict):
        values = raw.get("spells", [])
        if isinstance(values, list):
            return {str(x).strip() for x in values if str(x).strip()}
    return set()


RUNE_DB_EN = load_rune_db()
RUNE_NAME_KO = load_translation_map("Rune_KO.json")
RUNE_NAME_EN = {ko: en for en, ko in RUNE_NAME_KO.items()}

CHAMPION_DB_EN = load_champion_db()
CHAMPION_NAME_KO = load_translation_map("Champion_KO.json")
CHAMPION_NAME_EN = {ko: en for en, ko in CHAMPION_NAME_KO.items()}

SPELL_DB_EN = load_spell_db()
SPELL_NAME_KO = load_translation_map("Spells_KO.json")
SPELL_NAME_EN = {ko: en for en, ko in SPELL_NAME_KO.items()}

ITEM_NAME_KO = load_translation_map("Items_KO.json")
ITEM_NAME_EN = {ko: en for en, ko in ITEM_NAME_KO.items()}


def english_tree_to_korean(tree_en: str) -> str:
    mapping = {
        "precision": "정밀",
        "domination": "지배",
        "resolve": "결의",
        "inspiration": "영감",
    }
    return mapping.get((tree_en or "").strip().lower(), tree_en)


def champion_to_english(name: str) -> str:
    text = (name or "").strip()
    if not text or text == "오류":
        return ""

    if text in CHAMPION_DB_EN:
        return text

    if text in CHAMPION_NAME_EN:
        return CHAMPION_NAME_EN[text]

    lower_map = {x.lower(): x for x in CHAMPION_DB_EN}
    return lower_map.get(text.lower(), text)


def champion_to_korean(name: str) -> str:
    english = champion_to_english(name)
    if not english:
        return "오류"
    return CHAMPION_NAME_KO.get(english, english)


def rune_to_english(name: str) -> str:
    text = (name or "").strip()
    if not text or text == "오류":
        return ""

    if text in RUNE_NAME_EN:
        return RUNE_NAME_EN[text]

    for category in RUNE_DB_EN.values():
        if text in category:
            return text

    lower_map: Dict[str, str] = {}
    for category in RUNE_DB_EN.values():
        for rune in category:
            lower_map[rune.lower()] = rune

    return lower_map.get(text.lower(), text)


def rune_to_korean(name: str) -> str:
    english = rune_to_english(name)
    if not english:
        return "오류"
    return RUNE_NAME_KO.get(english, english)


def spells_to_korean(spells_text: str) -> str:
    text = (spells_text or "").strip()
    if not text or text == "오류":
        return "오류"

    parts = [x.strip() for x in text.split(",") if x.strip()]
    if not parts:
        return "오류"

    result = []
    for x in parts:
        if x in SPELL_NAME_KO:
            result.append(SPELL_NAME_KO[x])
        elif x in SPELL_NAME_EN:
            result.append(SPELL_NAME_KO.get(SPELL_NAME_EN[x], x))
        else:
            result.append(x)

    return ", ".join(result)


def item_to_korean(name: str) -> str:
    text = (name or "").strip()
    if not text or text == "오류":
        return "오류"

    if text in ITEM_NAME_KO:
        return ITEM_NAME_KO[text]

    if text in ITEM_NAME_EN:
        return text

    return text


def find_secondary_tree_name(secondary_rune_en: str, main_tree_en: str) -> str:
    sec = rune_to_english(secondary_rune_en)
    main_tree = (main_tree_en or "").strip().lower()

    for tree_name, runes in RUNE_DB_EN.items():
        if tree_name == "keystone":
            continue
        if tree_name == main_tree:
            continue
        if sec in runes:
            return tree_name

    return ""


def build_blind_pick_prompt(lane: str) -> str:
    return "\n".join([
        "Answer for Wild Rift only.",
        "Do not use PC League of Legends information.",
        "Assume latest Wild Rift meta.",
        "Recommend one safe blind-pick champion.",
        "Champion name must be in ENGLISH.",
        "Reason must be in KOREAN and VERY SHORT.",
        "",
        f"Lane: {lane}",
        "",
        "Output exactly in this format:",
        "추천 챔피언: <English>",
        "추천 이유: <Korean short text>",
    ])


def build_counter_pick_prompt(enemy_champ: str, lane: str) -> str:
    return "\n".join([
        "Answer for Wild Rift only.",
        "Do not use PC League of Legends information.",
        "Assume latest Wild Rift meta.",
        "Recommend one counter-pick champion.",
        "Champion name must be in ENGLISH.",
        "Reason must be in KOREAN and VERY SHORT.",
        "",
        f"Enemy champion: {enemy_champ}",
        f"Lane: {lane}",
        "",
        "Output exactly in this format:",
        "추천 챔피언: <English>",
        "추천 이유: <Korean short text>",
    ])


def build_fixed_pick_prompt(my_champ: str, enemy_champ: str, lane: str) -> str:
    return "\n".join([
        "Answer for Wild Rift only.",
        "Do not use PC League of Legends information.",
        "Assume latest Wild Rift meta.",
        "STRICT FORMAT.",
        "DO NOT CHANGE KEY NAMES.",
        "Use only real Wild Rift runes.",
        "",
        f"My champion: {my_champ}",
        f"Enemy champion: {enemy_champ}",
        f"Lane: {lane}",
        "",
        "Output exactly in this format:",
        "핵심룬: <English>",
        "메인특성 세트: <English>",
        "메인특성1: <English>",
        "메인특성2: <English>",
        "메인특성3: <English>",
        "보조특성1: <English>",
        "Spells: <English>, <English>",
        "Starting Item: <English>",
        "First Item: <English>",
        "초반 운영: <Korean short text>",
    ])


def parse_label_value(text: str, label: str) -> str:
    pattern = rf"^{re.escape(label)}\s*:\s*(.+)$"
    for line in text.splitlines():
        line = line.strip()
        m = re.match(pattern, line, flags=re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return ""


def recommend_blind_pick(lane: str) -> Dict[str, str]:
    lane_en = normalize_lane_ui_to_gpt(lane)
    prompt = build_blind_pick_prompt(lane_en)

    try:
        answer = ask_chatgpt(prompt)
    except Exception as e:
        return {
            "champion": "가렌",
            "reason": f"GPT 호출 실패: {e}",
        }

    champ_en = parse_label_value(answer, "추천 챔피언")
    reason = parse_label_value(answer, "추천 이유")

    if not champ_en:
        champ_en = "Garen"
    if not reason:
        reason = "무난하고 안정적인 선택입니다."

    return {
        "champion": champion_to_korean(champ_en),
        "reason": reason,
    }


def recommend_counter(enemy_champ: str, lane: str) -> Dict[str, str]:
    lane_en = normalize_lane_ui_to_gpt(lane)
    enemy_en = champion_to_english(enemy_champ) or enemy_champ
    prompt = build_counter_pick_prompt(enemy_en, lane_en)

    try:
        answer = ask_chatgpt(prompt)
    except Exception as e:
        return {
            "champion": "가렌",
            "reason": f"GPT 호출 실패: {e}",
        }

    champ_en = parse_label_value(answer, "추천 챔피언")
    reason = parse_label_value(answer, "추천 이유")

    if not champ_en:
        champ_en = "Garen"
    if not reason:
        reason = "상대 대응용으로 무난합니다."

    return {
        "champion": champion_to_korean(champ_en),
        "reason": reason,
    }


def recommend_build(my_champ: str, enemy_champ: str, lane: str) -> Dict[str, str]:
    lane_en = normalize_lane_ui_to_gpt(lane)
    my_en = champion_to_english(my_champ) or my_champ
    enemy_en = champion_to_english(enemy_champ) or enemy_champ
    prompt = build_fixed_pick_prompt(my_en, enemy_en, lane_en)

    try:
        answer = ask_chatgpt(prompt)
    except Exception as e:
        return {
            "핵심룬": "오류",
            "메인특성 세트": "오류",
            "메인특성1": "오류",
            "메인특성2": "오류",
            "메인특성3": "오류",
            "보조특성세트": "오류",
            "보조특성1": "오류",
            "스팰": "오류",
            "시작아탬": "오류",
            "첫완성탬": "오류",
            "초반 운영": f"GPT 호출 실패: {e}",
        }

    keystone = parse_label_value(answer, "핵심룬")
    tree = parse_label_value(answer, "메인특성 세트")
    rune1 = parse_label_value(answer, "메인특성1")
    rune2 = parse_label_value(answer, "메인특성2")
    rune3 = parse_label_value(answer, "메인특성3")
    secondary = parse_label_value(answer, "보조특성1")
    spells = parse_label_value(answer, "Spells")
    starting_item = parse_label_value(answer, "Starting Item")
    first_item = parse_label_value(answer, "First Item")
    early_text = parse_label_value(answer, "초반 운영")

    secondary_tree_en = find_secondary_tree_name(secondary, tree)

    return {
        "핵심룬": rune_to_korean(keystone) if keystone else "오류",
        "메인특성 세트": english_tree_to_korean(tree) if tree else "오류",
        "메인특성1": rune_to_korean(rune1) if rune1 else "오류",
        "메인특성2": rune_to_korean(rune2) if rune2 else "오류",
        "메인특성3": rune_to_korean(rune3) if rune3 else "오류",
        "보조특성세트": english_tree_to_korean(secondary_tree_en) if secondary_tree_en else "오류",
        "보조특성1": rune_to_korean(secondary) if secondary else "오류",
        "스팰": spells_to_korean(spells) if spells else "오류",
        "시작아탬": item_to_korean(starting_item),
        "첫완성탬": item_to_korean(first_item),
        "초반 운영": early_text or "오류",
    }