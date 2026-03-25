from typing import Dict

from core.utils.text_utils import safe_text


def build_pregame_result_text(build: Dict[str, str]) -> str:
    return "\n".join([
        f"핵심룬: {safe_text(build.get('핵심룬'))}",
        f"메인특성 세트: {safe_text(build.get('메인특성 세트'))}",
        f"메인특성1: {safe_text(build.get('메인특성1'))}",
        f"메인특성2: {safe_text(build.get('메인특성2'))}",
        f"메인특성3: {safe_text(build.get('메인특성3'))}",
        f"보조특성세트: {safe_text(build.get('보조특성세트'))}",
        f"보조특성1: {safe_text(build.get('보조특성1'))}",
        f"스팰: {safe_text(build.get('스팰'))}",
        f"시작아탬: {safe_text(build.get('시작아탬'))}",
        f"첫완성탬: {safe_text(build.get('첫완성탬'))}",
    ])