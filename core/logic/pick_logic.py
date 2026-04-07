from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


class PickLogic:
    def __init__(self):
        data_dir = Path(__file__).resolve().parents[2] / "data" / "champions"
        with open(data_dir / "champion_roles.json", "r", encoding="utf-8") as f:
            self.champion_roles = json.load(f)
        with open(data_dir / "champion_stats.json", "r", encoding="utf-8") as f:
            self.champion_stats = json.load(f)
        with open(data_dir / "champion_synergy.json", "r", encoding="utf-8") as f:
            self.champion_synergy = json.load(f)

    def run(self, frame) -> dict:
        """
        실제 챔피언 인식 전 단계용 임시 분석.
        현재는 데이터 로딩과 기본 추천 뼈대만 제공한다.
        """
        frame_shape = None if frame is None else list(frame.shape)

        recommended = self._top_recommendations(limit=3)

        return {
            "status": "ok",
            "message": "pick_logic placeholder executed",
            "executed_at": datetime.now().isoformat(timespec="seconds"),
            "frame_shape": frame_shape,
            "recommended": recommended,
        }

    def _top_recommendations(self, limit: int = 3) -> list[dict]:
        merged = []
        for champ, stats in self.champion_stats.items():
            role = self.champion_roles.get(champ, "unknown")
            synergy = self.champion_synergy.get(champ, 0.0)
            score = float(stats.get("power", 0.0)) + float(synergy)
            merged.append({
                "champion": champ,
                "role": role,
                "score": round(score, 2),
            })
        merged.sort(key=lambda x: x["score"], reverse=True)
        return merged[:limit]
