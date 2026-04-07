from __future__ import annotations

import json
from pathlib import Path

import numpy as np

class ChangeDetector:
    def __init__(self):
        config_path = Path(__file__).resolve().parents[2] / "data" / "config.json"
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        self.diff_threshold = float(config["thresholds"]["change_diff_threshold"])

    def has_changed(self, previous_roi, current_roi) -> bool:
        if previous_roi is None or current_roi is None:
            return True
        if previous_roi.shape != current_roi.shape:
            return True

        prev = previous_roi.astype(np.float32)
        curr = current_roi.astype(np.float32)
        diff = float(np.mean(np.abs(prev - curr)))
        return diff >= self.diff_threshold
