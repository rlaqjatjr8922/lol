from __future__ import annotations

class PickStageDetector:
    def is_pick_stage(self, portrait_ok: bool, is_red: bool) -> bool:
        # 기본 규칙:
        # 1) 초상화 UI 가 있어야 하고
        # 2) 밴 단계처럼 강한 빨강 배경이면 안 됨
        return bool(portrait_ok and not is_red)
