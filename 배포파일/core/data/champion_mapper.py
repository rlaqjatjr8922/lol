from core.data.data_loader import load_champion_db, load_translation_map


CHAMPION_DB_EN = load_champion_db()
CHAMPION_NAME_KO = load_translation_map("Champion_KO.json")
CHAMPION_NAME_EN = {ko: en for en, ko in CHAMPION_NAME_KO.items()}


def champion_to_english(name: str) -> str:
    text = (name or "").strip()
    if not text:
        return ""

    if text in CHAMPION_DB_EN:
        return text
    if text in CHAMPION_NAME_EN:
        return CHAMPION_NAME_EN[text]
    return text


def champion_to_korean(name: str) -> str:
    text = champion_to_english(name)
    if not text:
        return "오류"
    return CHAMPION_NAME_KO.get(text, text)