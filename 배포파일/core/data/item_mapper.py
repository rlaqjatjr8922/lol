from core.data.data_loader import load_item_db, load_translation_map


ITEM_DB_EN = set(load_item_db())
ITEM_NAME_KO = load_translation_map("Items_KO.json")
ITEM_NAME_EN = {ko: en for en, ko in ITEM_NAME_KO.items()}


def item_to_english(name: str) -> str:
    text = (name or "").strip()
    if not text:
        return ""

    if text in ITEM_DB_EN:
        return text
    if text in ITEM_NAME_EN:
        return ITEM_NAME_EN[text]
    return text


def item_to_korean(name: str) -> str:
    en = item_to_english(name)
    if not en:
        return "오류"
    return ITEM_NAME_KO.get(en, en)