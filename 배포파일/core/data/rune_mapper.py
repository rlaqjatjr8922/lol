from core.data.data_loader import load_rune_db, load_translation_map


RUNE_DB_EN = load_rune_db()
RUNE_NAME_KO = load_translation_map("Rune_KO.json")
RUNE_NAME_EN = {ko: en for en, ko in RUNE_NAME_KO.items()}


def english_tree_to_korean(tree_en: str) -> str:
    mapping = {
        "precision": "정밀",
        "domination": "지배",
        "resolve": "결의",
        "inspiration": "영감",
    }
    return mapping.get((tree_en or "").strip().lower(), (tree_en or "").strip())


def rune_to_english(name: str) -> str:
    text = (name or "").strip()
    if not text:
        return ""

    if text in RUNE_NAME_EN:
        return RUNE_NAME_EN[text]

    for values in RUNE_DB_EN.values():
        if text in values:
            return text

    lower_map = {}
    for values in RUNE_DB_EN.values():
        for rune in values:
            lower_map[rune.lower()] = rune

    return lower_map.get(text.lower(), text)


def rune_to_korean(name: str) -> str:
    en = rune_to_english(name)
    if not en:
        return "오류"
    return RUNE_NAME_KO.get(en, en)