from core.data.data_loader import load_spell_db, load_translation_map


SPELL_DB_EN = load_spell_db()
SPELL_NAME_KO = load_translation_map("Spells_KO.json")
SPELL_NAME_EN = {ko: en for en, ko in SPELL_NAME_KO.items()}


def spell_to_english(name: str) -> str:
    text = (name or "").strip()
    if not text:
        return ""

    if text in SPELL_DB_EN:
        return text
    if text in SPELL_NAME_EN:
        return SPELL_NAME_EN[text]
    return text


def spells_to_korean(spells_text: str) -> str:
    text = (spells_text or "").strip()
    if not text:
        return "오류"

    parts = [x.strip() for x in text.split(",") if x.strip()]
    if not parts:
        return "오류"

    return ", ".join(SPELL_NAME_KO.get(x, x) for x in parts)