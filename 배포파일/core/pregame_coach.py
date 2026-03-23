from __future__ import annotations

import ast
import os
from typing import Dict, Set

from gpt.chatgpt_web_bridge import ask_chatgpt


TREE_KEYS = ["precision", "domination", "resolve", "inspiration"]
FIRST_BUY_KEYS = {"Boots First", "Core Item First"}


def normalize_lane_ui_to_gpt(lane_text: str) -> str:
    mapping = {
        "탑": "top",
        "미드": "mid",
        "원딜": "dragon",
        "서폿": "support",
        "정글": "jungle",
    }
    return mapping.get((lane_text or "").strip(), "top")


def get_project_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_rune_file_path() -> str:
    return os.path.join(get_project_root(), "Data", "Rune.txt")


def get_rune_ko_file_path() -> str:
    return os.path.join(get_project_root(), "Data", "Rune_KO.txt")


def get_champion_file_path() -> str:
    return os.path.join(get_project_root(), "Data", "Champion.txt")


def get_champion_ko_file_path() -> str:
    return os.path.join(get_project_root(), "Data", "Champion_KO.txt")


def get_spell_ko_file_path() -> str:
    return os.path.join(get_project_root(), "Data", "Spells_KO.txt")


def load_rune_db() -> Dict[str, Set[str]]:
    path = get_rune_file_path()

    with open(path, "r", encoding="utf-8") as f:
        raw = f.read().strip()

    if not raw:
        raise ValueError("Data/Rune.txt 파일이 비어 있습니다.")

    if raw.startswith("RUNE_DB_EN"):
        raw = raw.split("=", 1)[1].strip()

    loaded = ast.literal_eval(raw)

    result: Dict[str, Set[str]] = {}
    for key, value in loaded.items():
        if isinstance(value, (set, list, tuple)):
            result[key.lower()] = {str(x).strip() for x in value if str(x).strip()}
        else:
            result[key.lower()] = set()

    required = ["keystone", "precision", "domination", "resolve", "inspiration"]
    for key in required:
        if key not in result:
            raise ValueError(f"Data/Rune.txt에 '{key}' 항목이 없습니다.")

    return result


def load_rune_translation() -> Dict[str, str]:
    path = get_rune_ko_file_path()
    mapping: Dict[str, str] = {}

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if not line:
                continue
            if line.startswith("#"):
                continue
            if "=" not in line:
                continue

            en, ko = line.split("=", 1)
            en = en.strip()
            ko = ko.strip()

            if en and ko:
                mapping[en] = ko

    return mapping


def load_champion_db() -> Set[str]:
    path = get_champion_file_path()

    with open(path, "r", encoding="utf-8") as f:
        raw = f.read().strip()

    if not raw:
        raise ValueError("Data/Champion.txt 파일이 비어 있습니다.")

    loaded = ast.literal_eval(raw)

    if isinstance(loaded, (set, list, tuple)):
        return {str(x).strip() for x in loaded if str(x).strip()}

    raise ValueError("Data/Champion.txt 형식이 올바르지 않습니다.")


def load_champion_translation() -> Dict[str, str]:
    path = get_champion_ko_file_path()
    mapping: Dict[str, str] = {}

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if not line:
                continue
            if line.startswith("#"):
                continue
            if "=" not in line:
                continue

            en, ko = line.split("=", 1)
            en = en.strip()
            ko = ko.strip()

            if en and ko:
                mapping[en] = ko

    return mapping


def load_spell_translation() -> Dict[str, str]:
    path = get_spell_ko_file_path()
    mapping: Dict[str, str] = {}

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if not line:
                continue
            if line.startswith("#"):
                continue
            if "=" not in line:
                continue

            en, ko = line.split("=", 1)
            en = en.strip()
            ko = ko.strip()

            if en and ko:
                mapping[en] = ko

    return mapping


RUNE_DB_EN = load_rune_db()
RUNE_NAME_KO = load_rune_translation()
RUNE_NAME_EN = {ko: en for en, ko in RUNE_NAME_KO.items()}

CHAMPION_DB_EN = load_champion_db()
CHAMPION_NAME_KO = load_champion_translation()

SPELL_NAME_KO = load_spell_translation()


def english_tree_to_korean(tree_en: str) -> str:
    mapping = {
        "precision": "정밀",
        "domination": "지배",
        "resolve": "결의",
        "inspiration": "영감",
    }
    return mapping.get((tree_en or "").strip().lower(), tree_en)


def korean_tree_to_english(tree_ko: str) -> str:
    mapping = {
        "정밀": "precision",
        "지배": "domination",
        "결의": "resolve",
        "영감": "inspiration",
    }
    return mapping.get((tree_ko or "").strip(), (tree_ko or "").strip().lower())


def first_buy_priority_to_korean(value: str) -> str:
    mapping = {
        "Boots First": "신발 먼저",
        "Core Item First": "코어템 먼저",
    }
    return mapping.get((value or "").strip(), value)


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


def champion_to_korean(name: str) -> str:
    text = (name or "").strip()
    if not text or text == "오류":
        return "오류"
    return CHAMPION_NAME_KO.get(text, text)


def spells_to_korean(spells_text: str) -> str:
    text = (spells_text or "").strip()
    if not text or text == "오류":
        return "오류"

    parts = [x.strip() for x in text.split(",") if x.strip()]
    if not parts:
        return "오류"

    return ", ".join(SPELL_NAME_KO.get(x, x) for x in parts)


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
        "",
        "추천 챔피언:",
        "One champion name",
        "",
        "추천 이유:",
        "한글로 1~2문장만 매우 짧게 작성 (불필요한 설명 금지)",
        "",
        "Do not output anything else."
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
        "",
        "추천 챔피언:",
        "One champion name",
        "",
        "추천 이유:",
        "한글로 1~2문장만 매우 짧게 작성 (불필요한 설명 금지)",
        "",
        "Do not output anything else."
    ])


def build_fixed_pick_prompt(my_champ: str, enemy_champ: str, lane: str) -> str:
    return "\n".join([
        "Answer for Wild Rift only.",
        "Do not use PC League of Legends information.",
        "Assume latest Wild Rift meta.",
        "STRICT FORMAT. DO NOT CHANGE KEY NAMES.",
        "Use EXACT keys below.",
        "All fields must be filled.",
        "Use only real Wild Rift runes.",
        "Choose 1 Keystone, 1 Tree, 3 runes from the same Tree, and 1 Secondary rune from a different Tree.",
        "Do not put a Keystone rune into Rune1, Rune2, or Rune3.",
        "Secondary must be from a different Tree.",
        "Do not use PC-only items or systems.",
        "",
        "Keystone, Tree, Rune1, Rune2, Rune3, Secondary, Spells, First Buy Priority, Starting Item, First Item must be in ENGLISH.",
        "초반 운영 must be in KOREAN.",
        "",
        f"My champion: {my_champ}",
        f"Enemy champion: {enemy_champ}",
        f"Lane: {lane}",
        "",
        "Rules:",
        "1. Decide Boots First or Core Item First.",
        "2. Starting Item must be ONE 500 gold component.",
        "3. First Item must be the FIRST completed item (boots OR core).",
        "4. Starting Item should be an appropriate early component for the chosen path.",
        "5. If multiple candidates exist, choose ONE best.",
        "6. Never use Doran's items.",
        "7. Never output a full item as Starting Item.",
        "",
        "Output EXACTLY:",
        "",
        "Keystone:",
        "Tree:",
        "Rune1:",
        "Rune2:",
        "Rune3:",
        "Secondary:",
        "Spells:",
        "First Buy Priority:",
        "Starting Item:",
        "First Item:",
        "초반 운영:",
        "",
        "For First Buy Priority, answer only:",
        "Boots First",
        "Core Item First",
        "",
        "Do not output anything else."
    ])


def parse_counter_pick(text: str) -> dict:
    parsed = {"추천 챔피언": "오류", "추천 이유": "오류"}

    lines = [line.strip() for line in (text or "").splitlines()]
    reason_mode = False
    reason_lines = []

    i = 0
    while i < len(lines):
        line = lines[i]

        if line.startswith("추천 챔피언"):
            if ":" in line:
                after = line.split(":", 1)[1].strip()

                if after:
                    parsed["추천 챔피언"] = after
                else:
                    j = i + 1
                    while j < len(lines) and not lines[j]:
                        j += 1
                    if j < len(lines):
                        parsed["추천 챔피언"] = lines[j]

            reason_mode = False

        elif line.startswith("추천 이유"):
            reason_mode = True

            if ":" in line:
                after = line.split(":", 1)[1].strip()
                if after:
                    reason_lines.append(after)

        elif reason_mode and line:
            reason_lines.append(line)

        i += 1

    if reason_lines:
        parsed["추천 이유"] = "\n".join(reason_lines).strip()

    champion_en = parsed["추천 챔피언"].strip()
    if champion_en in CHAMPION_DB_EN:
        parsed["추천 챔피언(영문)"] = champion_en
        parsed["추천 챔피언"] = champion_to_korean(champion_en)
    else:
        parsed["추천 챔피언(영문)"] = champion_en if champion_en != "오류" else "오류"

    return parsed


def parse_build(text: str) -> dict:
    result = {
        "Keystone": "오류",
        "Tree": "오류",
        "Rune1": "오류",
        "Rune2": "오류",
        "Rune3": "오류",
        "Secondary": "오류",
        "SecondaryTree": "오류",
        "Spells": "오류",
        "First Buy Priority": "오류",
        "Starting Item": "오류",
        "First Item": "오류",
        "초반 운영": "오류",
    }

    lines = [line.strip() for line in (text or "").splitlines()]

    def get_next_value(i: int) -> str:
        j = i + 1
        while j < len(lines) and not lines[j]:
            j += 1
        return lines[j] if j < len(lines) else ""

    for i, line in enumerate(lines):
        if line.startswith("Keystone:"):
            val = line.replace("Keystone:", "", 1).strip()
            result["Keystone"] = val if val else get_next_value(i)

        elif line.startswith("Tree:"):
            val = line.replace("Tree:", "", 1).strip()
            result["Tree"] = val if val else get_next_value(i)

        elif line.startswith("Rune1:"):
            val = line.replace("Rune1:", "", 1).strip()
            result["Rune1"] = val if val else get_next_value(i)

        elif line.startswith("Rune2:"):
            val = line.replace("Rune2:", "", 1).strip()
            result["Rune2"] = val if val else get_next_value(i)

        elif line.startswith("Rune3:"):
            val = line.replace("Rune3:", "", 1).strip()
            result["Rune3"] = val if val else get_next_value(i)

        elif line.startswith("Secondary:"):
            val = line.replace("Secondary:", "", 1).strip()
            result["Secondary"] = val if val else get_next_value(i)

        elif line.startswith("Spells:"):
            val = line.replace("Spells:", "", 1).strip()
            result["Spells"] = val if val else get_next_value(i)

        elif line.startswith("First Buy Priority:"):
            val = line.replace("First Buy Priority:", "", 1).strip()
            result["First Buy Priority"] = val if val else get_next_value(i)

        elif line.startswith("Starting Item:"):
            val = line.replace("Starting Item:", "", 1).strip()
            result["Starting Item"] = val if val else get_next_value(i)

        elif line.startswith("First Item:"):
            val = line.replace("First Item:", "", 1).strip()
            result["First Item"] = val if val else get_next_value(i)

        elif line.startswith("초반 운영:"):
            val = line.replace("초반 운영:", "", 1).strip()
            result["초반 운영"] = val if val else get_next_value(i)

    return result


def normalize_tree_name(tree_name: str) -> str:
    text = (tree_name or "").strip()
    if not text or text == "오류":
        return ""

    text_en = korean_tree_to_english(text)
    if text_en in TREE_KEYS:
        return text_en

    lower_map = {key.lower(): key for key in TREE_KEYS}
    return lower_map.get(text.lower(), "")


def is_valid_keystone(name: str) -> bool:
    rune = rune_to_english(name)
    return bool(rune) and rune in RUNE_DB_EN.get("keystone", set())


def is_valid_rune_in_tree(rune_name: str, tree_name: str) -> bool:
    tree = normalize_tree_name(tree_name)
    rune = rune_to_english(rune_name)

    if not tree or not rune:
        return False

    if tree not in RUNE_DB_EN:
        return False

    return rune in RUNE_DB_EN[tree]


def find_rune_tree(rune_name: str) -> str:
    rune = rune_to_english(rune_name)

    if not rune:
        return ""

    for tree in TREE_KEYS:
        if rune in RUNE_DB_EN.get(tree, set()):
            return tree

    return ""


def validate_each_field(build: dict) -> dict:
    result = dict(build)

    tree = normalize_tree_name(build.get("Tree", ""))
    secondary_tree = find_rune_tree(build.get("Secondary", ""))

    if not is_valid_keystone(build.get("Keystone", "")):
        result["Keystone"] = "오류"

    if not tree:
        result["Tree"] = "오류"

    if not is_valid_rune_in_tree(build.get("Rune1", ""), tree):
        result["Rune1"] = "오류"

    if not is_valid_rune_in_tree(build.get("Rune2", ""), tree):
        result["Rune2"] = "오류"

    if not is_valid_rune_in_tree(build.get("Rune3", ""), tree):
        result["Rune3"] = "오류"

    if not secondary_tree or (tree and secondary_tree == tree):
        result["Secondary"] = "오류"

    if result.get("Secondary") != "오류":
        result["SecondaryTree"] = english_tree_to_korean(secondary_tree)
    else:
        result["SecondaryTree"] = "오류"

    if not build.get("Spells", "").strip():
        result["Spells"] = "오류"

    if build.get("First Buy Priority", "").strip() not in FIRST_BUY_KEYS:
        result["First Buy Priority"] = "오류"

    if not build.get("Starting Item", "").strip():
        result["Starting Item"] = "오류"

    if not build.get("First Item", "").strip():
        result["First Item"] = "오류"

    if not build.get("초반 운영", "").strip():
        result["초반 운영"] = "오류"

    return result


def translate_build_to_korean(build: dict) -> dict:
    translated = dict(build)

    translated["Keystone"] = rune_to_korean(translated.get("Keystone", "오류"))
    translated["Tree"] = english_tree_to_korean(translated.get("Tree", "오류"))

    translated["Rune1"] = rune_to_korean(translated.get("Rune1", "오류"))
    translated["Rune2"] = rune_to_korean(translated.get("Rune2", "오류"))
    translated["Rune3"] = rune_to_korean(translated.get("Rune3", "오류"))

    secondary = translated.get("Secondary", "오류")
    translated["SecondaryTree"] = translated.get("SecondaryTree", "오류")
    translated["Secondary"] = rune_to_korean(secondary)

    translated["Spells"] = spells_to_korean(translated.get("Spells", "오류"))
    translated["First Buy Priority"] = first_buy_priority_to_korean(
        translated.get("First Buy Priority", "오류")
    )

    return translated


def ask_build_until_valid(my_champ: str, enemy_champ: str, lane: str, max_retry: int = 4) -> dict:
    base_prompt = build_fixed_pick_prompt(my_champ, enemy_champ, lane)
    best_validated = None
    best_score = -1

    keys = [
        "Keystone", "Tree", "Rune1", "Rune2", "Rune3",
        "Secondary", "Spells", "First Buy Priority",
        "Starting Item", "First Item", "초반 운영"
    ]

    for _ in range(max_retry):
        answer = ask_chatgpt(base_prompt)

        if not answer or not answer.strip():
            continue

        build = parse_build(answer)
        validated = validate_each_field(build)

        score = sum(1 for key in keys if validated.get(key) != "오류")

        if score > best_score:
            best_score = score
            best_validated = validated

        if score == len(keys):
            return translate_build_to_korean(validated)

    if best_validated is not None:
        return translate_build_to_korean(best_validated)

    return {
        "Keystone": "오류",
        "Tree": "오류",
        "Rune1": "오류",
        "Rune2": "오류",
        "Rune3": "오류",
        "Secondary": "오류",
        "SecondaryTree": "오류",
        "Spells": "오류",
        "First Buy Priority": "오류",
        "Starting Item": "오류",
        "First Item": "오류",
        "초반 운영": "오류",
    }


def recommend_blind_pick(lane_ui: str) -> dict:
    lane = normalize_lane_ui_to_gpt(lane_ui)
    prompt = build_blind_pick_prompt(lane)
    answer = ask_chatgpt(prompt)
    parsed = parse_counter_pick(answer or "")

    if not parsed["추천 챔피언"]:
        parsed["추천 챔피언"] = "오류"
    if not parsed["추천 이유"]:
        parsed["추천 이유"] = "오류"

    return parsed


def recommend_counter(enemy_champ: str, lane_ui: str) -> dict:
    lane = normalize_lane_ui_to_gpt(lane_ui)
    prompt = build_counter_pick_prompt(enemy_champ, lane)
    answer = ask_chatgpt(prompt)
    parsed = parse_counter_pick(answer or "")

    if not parsed["추천 챔피언"]:
        parsed["추천 챔피언"] = "오류"
    if not parsed["추천 이유"]:
        parsed["추천 이유"] = "오류"

    return parsed


def recommend_build(my_champ: str, enemy_champ: str, lane_ui: str) -> dict:
    lane = normalize_lane_ui_to_gpt(lane_ui)
    return ask_build_until_valid(my_champ, enemy_champ, lane)