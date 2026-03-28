def safe_text(value: str, default: str = "오류") -> str:
    text = (value or "").strip()
    return text if text else default


def trim_text(value: str, max_len: int = 120, default: str = "오류") -> str:
    text = safe_text(value, default=default)
    if text == default:
        return default
    if len(text) > max_len:
        return text[:max_len] + "..."
    return text