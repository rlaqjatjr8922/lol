import re
from typing import Dict, List


def parse_label_value(text: str, label: str) -> str:
    pattern = rf"^{re.escape(label)}\s*:\s*(.+)$"

    for line in (text or "").splitlines():
        line = line.strip()
        m = re.match(pattern, line, flags=re.IGNORECASE)
        if m:
            return m.group(1).strip()

    return ""


def parse_pick_result(text: str) -> Dict[str, str]:
    champ = parse_label_value(text, "Champion")
    reason = parse_label_value(text, "Reason")

    return {
        "champion": champ,
        "reason": reason,
    }


def parse_build_result(text: str) -> Dict[str, str]:
    return {
        "Keystone": parse_label_value(text, "Keystone"),
        "Primary Tree": parse_label_value(text, "Primary Tree"),
        "Rune1": parse_label_value(text, "Rune1"),
        "Rune2": parse_label_value(text, "Rune2"),
        "Rune3": parse_label_value(text, "Rune3"),
        "Secondary Tree": parse_label_value(text, "Secondary Tree"),
        "Secondary Rune": parse_label_value(text, "Secondary Rune"),
        "Spells": parse_label_value(text, "Spells"),
        "Starting Item": parse_label_value(text, "Starting Item"),
        "First Item": parse_label_value(text, "First Item"),
        "Early Game Plan": parse_label_value(text, "Early Game Plan"),
    }


def parse_ingame_tips(text: str) -> List[str]:
    result = []

    for label in ["Summary", "Tip1", "Tip2", "Tip3", "한줄요약", "팁1", "팁2", "팁3"]:
        value = parse_label_value(text, label)
        if value:
            result.append(value)

    return result