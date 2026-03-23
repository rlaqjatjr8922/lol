from __future__ import annotations

import json
import os
import re
from typing import Dict, Set, List, Tuple, Optional

from gpt.chatgpt_web_bridge import ask_chatgpt

TREE_KEYS = ["precision", "domination", "resolve", "inspiration"]
FIRST_BUY_KEYS = {"Boots First", "Core Item First"}


# =========================
# 경로 / JSON 로드
# =========================

def get_project_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_data_path(name: str) -> str:
    path = os.path.join(get_project_root(), "Data", f"{name}.json")
    if not os.path.exists(path):
        raise FileNotFoundError(f"데이터 파일이 없습니다: {path}")
    return path


def load_json(name: str):
    path = get_data_path(name)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_champion_db() -> Set[str]:
    data = load_json("Champion")
    if not isinstance(data, list):
        raise ValueError("Champion.json은 리스트 형식이어야 합니다.")
    return {str(x).strip() for x in data if str(x).strip()}


def load_rune_db() -> Dict[str, Set[str]]:
    data = load_json("Rune")
    if not isinstance(data, dict):
        raise ValueError("Rune.json은 딕셔너리 형식이어야 합니다.")

    result: Dict[str, Set[str]] = {}
    for key, value in data.items():
        if not isinstance(value, list):
            raise ValueError(f"Rune.json의 '{key}' 값은 리스트여야 합니다.")
        result[str(key).strip().lower()] = {
            str(x).strip() for x in value if str(x).strip()
        }

    required = ["keystone", "precision", "domination", "resolve", "inspiration"]
    for key in required:
        if key not in result:
            raise ValueError(f"Rune.json에 '{key}' 항목이 없습니다.")

    return result


def load_champion_translation() -> Dict[str, str]:
    data = load_json("Champion_KO")
    if not isinstance(data, dict):
        raise ValueError("Champion_KO.json은 딕셔너리 형식이어야 합니다.")
    return {str(k).strip(): str(v).strip() for k, v in data.items()}


def load_rune_translation() -> Dict[str, str]:
    data = load_json("Rune_KO")
    if not isinstance(data, dict):
        raise ValueError("Rune_KO.json은 딕셔너리 형식이어야 합니다.")
    return {str(k).strip(): str(v).strip() for k, v in data.items()}


def load_spell_translation() -> Dict[str, str]:
    data = load_json("Spells_KO")
    if not isinstance(data, dict):
        raise ValueError("Spells_KO.json은 딕셔너리 형식이어야 합니다.")
    return {str(k).strip(): str(v).strip() for k, v in data.items()}


# =========================
# 문자열 정리 / 변환
# =========================

def normalize_text(text: str) -> str:
    return re.sub(r"\s+", "", text).lower().strip()


def normalize_lane_ui_to_gpt(lane_text: str) -> str:
    mapping = {
        "탑": "top",
        "정글": "jungle",
        "미드": "mid",
        "원딜": "dragon",
        "서폿": "support",
        "듀오": "dragon",
        "바론": "top",
    }
    return mapping.get((lane_text or "").strip(), "top")


def reverse_translation_map(mapping: Dict[str, str]) -> Dict[str, str]:
    result: Dict[str, str] = {}
    for en, ko in mapping.items():
        result[normalize_text(ko)] = en
        result[normalize_text(en)] = en
    return result


# =========================
# 챔피언 / 룬 / 스펠 변환
# =========================

def convert_ko_champion_to_en(name: str, champion_ko: Dict[str, str], champion_db: Set[str]) -> str:
    if not name:
        return ""

    raw = name.strip()
    if raw in champion_db:
        return raw

    name_norm = normalize_text(raw)

    # KO -> EN
    rev = reverse_translation_map(champion_ko)
    if name_norm in rev:
        return rev[name_norm]

    # EN 대소문자 무시 비교
    for champ in champion_db:
        if normalize_text(champ) == name_norm:
            return champ

    return raw


def convert_ko_rune_to_en(name: str, rune_ko: Dict[str, str], rune_db: Dict[str, Set[str]]) -> str:
    if not name:
        return ""

    raw = name.strip()
    all_runes = set().union(*rune_db.values())

    if raw in all_runes:
        return raw

    name_norm = normalize_text(raw)
    rev = reverse_translation_map(rune_ko)

    if name_norm in rev:
        return rev[name_norm]

    for rune in all_runes:
        if normalize_text(rune) == name_norm:
            return rune

    return raw


def convert_ko_spell_to_en(name: str, spell_ko: Dict[str, str]) -> str:
    if not name:
        return ""

    raw = name.strip()
    if raw in spell_ko:
        return raw

    name_norm = normalize_text(raw)
    rev = reverse_translation_map(spell_ko)

    if name_norm in rev:
        return rev[name_norm]

    for spell_en in spell_ko.keys():
        if normalize_text(spell_en) == name_norm:
            return spell_en

    return raw


def translate_en_to_ko(name: str, mapping: Dict[str, str]) -> str:
    return mapping.get(name, name)


# =========================
# 응답 파싱
# =========================

def extract_value(text: str, label: str) -> str:
    pattern = rf"^{re.escape(label)}\s*:\s*(.+)$"
    for line in text.splitlines():
        line = line.strip()
        m = re.match(pattern, line, flags=re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return ""


def parse_spells(value: str) -> List[str]:
    if not value:
        return []

    parts = re.split(r"[,/]| and ", value)
    result = []
    for part in parts:
        p = part.strip()
        if p:
            result.append(p)
    return result


def find_rune_tree_for_rune(rune_name: str, rune_db: Dict[str, Set[str]]) -> Optional[str]:
    for tree in TREE_KEYS:
        if rune_name in rune_db.get(tree, set()):
            return tree
    return None


def validate_result(
    parsed: Dict[str, str],
    champion_db: Set[str],
    rune_db: Dict[str, Set[str]],
    champion_ko: Dict[str, str],
    rune_ko: Dict[str, str],
    spell_ko: Dict[str, str],
) -> Dict[str, object]:
    errors: List[str] = []

    enemy_champion = convert_ko_champion_to_en(parsed.get("Enemy", ""), champion_ko, champion_db)
    my_champion = convert_ko_champion_to_en(parsed.get("Me", ""), champion_ko, champion_db)

    if enemy_champion not in champion_db:
        errors.append(f"상대 챔피언 인식 실패: {parsed.get('Enemy', '')}")
    if my_champion not in champion_db:
        errors.append(f"내 챔피언 인식 실패: {parsed.get('Me', '')}")

    keystone = convert_ko_rune_to_en(parsed.get("Keystone", ""), rune_ko, rune_db)
    if keystone not in rune_db["keystone"]:
        errors.append(f"Keystone 인식 실패: {parsed.get('Keystone', '')}")

    tree = extract_value_block(parsed.get("Tree", "")).lower()
    if tree not in TREE_KEYS:
        errors.append(f"Tree 값 오류: {parsed.get('Tree', '')}")

    rune1 = convert_ko_rune_to_en(parsed.get("Rune1", ""), rune_ko, rune_db)
    rune2 = convert_ko_rune_to_en(parsed.get("Rune2", ""), rune_ko, rune_db)
    rune3 = convert_ko_rune_to_en(parsed.get("Rune3", ""), rune_ko, rune_db)

    if tree in rune_db:
        if rune1 not in rune_db[tree]:
            errors.append(f"Rune1 인식 실패 또는 트리 불일치: {parsed.get('Rune1', '')}")
        if rune2 not in rune_db[tree]:
            errors.append(f"Rune2 인식 실패 또는 트리 불일치: {parsed.get('Rune2', '')}")
        if rune3 not in rune_db[tree]:
            errors.append(f"Rune3 인식 실패 또는 트리 불일치: {parsed.get('Rune3', '')}")

    secondary_raw = parsed.get("Secondary", "").strip()
    secondary_tree = ""
    secondary_rune = ""

    if ":" in secondary_raw:
        secondary_tree, secondary_rune = [x.strip() for x in secondary_raw.split(":", 1)]
    else:
        secondary_tree = secondary_raw.strip()

    secondary_tree = secondary_tree.lower()
    secondary_rune = convert_ko_rune_to_en(secondary_rune, rune_ko, rune_db)

    if secondary_tree not in TREE_KEYS:
        errors.append(f"Secondary 트리 오류: {parsed.get('Secondary', '')}")
    else:
        if secondary_rune and secondary_rune not in rune_db[secondary_tree]:
            errors.append(f"Secondary 룬 오류: {parsed.get('Secondary', '')}")

    spells_raw = parse_spells(parsed.get("Spells", ""))
    spells_en = [convert_ko_spell_to_en(s, spell_ko) for s in spells_raw]
    if len(spells_en) != 2:
        errors.append(f"Spells 개수 오류: {parsed.get('Spells', '')}")

    first_buy = parsed.get("First Buy Priority", "").strip()
    if first_buy not in FIRST_BUY_KEYS:
        errors.append(f"First Buy Priority 오류: {first_buy}")

    return {
        "ok": len(errors) == 0,
        "errors": errors,
        "enemy_champion": enemy_champion,
        "my_champion": my_champion,
        "keystone": keystone,
        "tree": tree,
        "rune1": rune1,
        "rune2": rune2,
        "rune3": rune3,
        "secondary_tree": secondary_tree,
        "secondary_rune": secondary_rune,
        "spells": spells_en,
        "first_buy": first_buy,
        "starting_item": parsed.get("Starting Item", "").strip(),
        "first_item": parsed.get("First Item", "").strip(),
        "early_guide": parsed.get("초반 운영", "").strip(),
    }


def extract_value_block(value: str) -> str:
    return value.strip()


def parse_response_text(text: str) -> Dict[str, str]:
    labels = [
        "Enemy",
        "Me",
        "Keystone",
        "Tree",
        "Rune1",
        "Rune2",
        "Rune3",
        "Secondary",
        "Spells",
        "First Buy Priority",
        "Starting Item",
        "First Item",
        "초반 운영",
    ]

    result: Dict[str, str] = {}
    for label in labels:
        result[label] = extract_value(text, label)

    return result


# =========================
# 프롬프트 생성
# =========================

def build_prompt(
    my_champion_en: str,
    enemy_champion_en: str,
    lane_en: str,
    champion_ko: Dict[str, str],
    rune_ko: Dict[str, str],
    spell_ko: Dict[str, str],
) -> str:
    my_champion_ko = translate_en_to_ko(my_champion_en, champion_ko)
    enemy_champion_ko = translate_en_to_ko(enemy_champion_en, champion_ko)

    prompt = f"""
You are a Wild Rift pregame coach.

My champion: {my_champion_en} ({my_champion_ko})
Enemy champion: {enemy_champion_en} ({enemy_champion_ko})
Lane: {lane_en}

Return answer in EXACT format below.
Use official English rune/spell names if possible.
You may add Korean next to them if needed, but keep the English main token recognizable.

Enemy: {enemy_champion_en}
Me: {my_champion_en}
Keystone: ...
Tree: precision / domination / resolve / inspiration
Rune1: ...
Rune2: ...
Rune3: ...
Secondary: tree_name:rune_name
Spells: spell1, spell2
First Buy Priority: Boots First OR Core Item First
Starting Item: ...
First Item: ...
초반 운영: ...

Rules:
- Tree must be one of: precision, domination, resolve, inspiration
- Keystone must be one valid keystone rune
- Rune1/2/3 must belong to the selected Tree
- Secondary format must be exactly tree:rune
- Spells must contain exactly 2 spells
- First Buy Priority must be either Boots First or Core Item First
- Keep 초반 운영 short and practical
""".strip()

    return prompt


# =========================
# 메인 추천 함수
# =========================

def get_pregame_coaching(my_champion: str, enemy_champion: str, lane_text: str) -> Dict[str, object]:
    champion_db = load_champion_db()
    rune_db = load_rune_db()
    champion_ko = load_champion_translation()
    rune_ko = load_rune_translation()
    spell_ko = load_spell_translation()

    my_champion_en = convert_ko_champion_to_en(my_champion, champion_ko, champion_db)
    enemy_champion_en = convert_ko_champion_to_en(enemy_champion, champion_ko, champion_db)
    lane_en = normalize_lane_ui_to_gpt(lane_text)

    prompt = build_prompt(
        my_champion_en=my_champion_en,
        enemy_champion_en=enemy_champion_en,
        lane_en=lane_en,
        champion_ko=champion_ko,
        rune_ko=rune_ko,
        spell_ko=spell_ko,
    )

    raw_answer = ask_chatgpt(prompt)
    parsed = parse_response_text(raw_answer)
    validated = validate_result(parsed, champion_db, rune_db, champion_ko, rune_ko, spell_ko)

    return {
        "ok": validated["ok"],
        "errors": validated["errors"],
        "raw_answer": raw_answer,
        "parsed": validated,
    }


# =========================
# 출력용 포맷
# =========================

def format_result_for_ui(result: Dict[str, object],
                         champion_ko: Dict[str, str],
                         rune_ko: Dict[str, str],
                         spell_ko: Dict[str, str]) -> str:
    parsed = result["parsed"]

    enemy_en = parsed["enemy_champion"]
    me_en = parsed["my_champion"]

    enemy_ko = translate_en_to_ko(enemy_en, champion_ko)
    me_ko = translate_en_to_ko(me_en, champion_ko)

    keystone_en = parsed["keystone"]
    rune1_en = parsed["rune1"]
    rune2_en = parsed["rune2"]
    rune3_en = parsed["rune3"]
    secondary_tree = parsed["secondary_tree"]
    secondary_rune_en = parsed["secondary_rune"]
    spells_en = parsed["spells"]

    lines = [
        f"상대 챔피언: {enemy_ko} ({enemy_en})",
        f"내 챔피언: {me_ko} ({me_en})",
        f"핵심 룬: {translate_en_to_ko(keystone_en, rune_ko)} ({keystone_en})",
        f"룬 트리: {parsed['tree']}",
        f"룬1: {translate_en_to_ko(rune1_en, rune_ko)} ({rune1_en})",
        f"룬2: {translate_en_to_ko(rune2_en, rune_ko)} ({rune2_en})",
        f"룬3: {translate_en_to_ko(rune3_en, rune_ko)} ({rune3_en})",
        f"보조 룬: {secondary_tree}:{translate_en_to_ko(secondary_rune_en, rune_ko)} ({secondary_rune_en})",
        f"스펠: {', '.join([f'{translate_en_to_ko(s, spell_ko)} ({s})' for s in spells_en])}",
        f"첫 구매 우선순위: {parsed['first_buy']}",
        f"시작 아이템: {parsed['starting_item']}",
        f"첫 코어 아이템: {parsed['first_item']}",
        f"초반 운영: {parsed['early_guide']}",
    ]

    if not result["ok"]:
        lines.append("")
        lines.append("[오류]")
        for err in result["errors"]:
            lines.append(f"- {err}")

    return "\n".join(lines)


# =========================
# 테스트 실행
# =========================

if __name__ == "__main__":
    try:
        champion_ko = load_champion_translation()
        rune_ko = load_rune_translation()
        spell_ko = load_spell_translation()

        # 테스트용
        my_champion = "가렌"
        enemy_champion = "다리우스"
        lane = "탑"

        result = get_pregame_coaching(my_champion, enemy_champion, lane)
        text = format_result_for_ui(result, champion_ko, rune_ko, spell_ko)

        print("=" * 50)
        print(text)
        print("=" * 50)

    except Exception as e:
        print(f"[오류] {e}")