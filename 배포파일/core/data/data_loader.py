from functools import lru_cache
from typing import Dict, List, Set

from core.utils.file_utils import load_json_file


@lru_cache(maxsize=1)
def load_rune_db() -> Dict[str, Set[str]]:
    raw = load_json_file("Rune.json", {})
    result: Dict[str, Set[str]] = {
        "keystone": set(),
        "precision": set(),
        "domination": set(),
        "resolve": set(),
        "inspiration": set(),
    }

    if not isinstance(raw, dict):
        return result

    for key, value in raw.items():
        key_lower = str(key).strip().lower()
        if isinstance(value, list):
            result[key_lower] = {str(x).strip() for x in value if str(x).strip()}

    return result


@lru_cache(maxsize=1)
def load_translation_map(filename: str) -> Dict[str, str]:
    raw = load_json_file(filename, {})
    if not isinstance(raw, dict):
        return {}

    result: Dict[str, str] = {}
    for k, v in raw.items():
        ks = str(k).strip()
        vs = str(v).strip()
        if ks and vs:
            result[ks] = vs
    return result


@lru_cache(maxsize=1)
def load_champion_db() -> Set[str]:
    raw = load_json_file("Champion.json", [])
    if isinstance(raw, list):
        return {str(x).strip() for x in raw if str(x).strip()}
    return set()


@lru_cache(maxsize=1)
def load_spell_db() -> Set[str]:
    raw = load_json_file("Spells.json", {})
    if isinstance(raw, dict):
        values = raw.get("spells", [])
        if isinstance(values, list):
            return {str(x).strip() for x in values if str(x).strip()}
    return set()


@lru_cache(maxsize=1)
def load_item_db() -> List[str]:
    raw = load_json_file("Items.json", [])
    if isinstance(raw, list):
        return [str(x).strip() for x in raw if str(x).strip()]
    if isinstance(raw, dict):
        values = raw.get("items", [])
        if isinstance(values, list):
            return [str(x).strip() for x in values if str(x).strip()]
    return []