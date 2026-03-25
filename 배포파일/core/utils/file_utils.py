import json
import os
from functools import lru_cache
from typing import Any


@lru_cache(maxsize=1)
def get_project_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def get_data_path(filename: str) -> str:
    return os.path.join(get_project_root(), "Data", filename)


def load_json_file(filename: str, default: Any):
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