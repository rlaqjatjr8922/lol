import cv2
import numpy as np

from .models import DraftState
from .image_utils import safe_crop


class StateDetector:
    def __init__(self, yellow_threshold=150):
        self.yellow_threshold = yellow_threshold

    def _yellow_score(self, crop):
        if crop is None:
            return 0.0

        hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
        lower = np.array([15, 80, 80], dtype=np.uint8)
        upper = np.array([45, 255, 255], dtype=np.uint8)

        mask = cv2.inRange(hsv, lower, upper)
        return float(mask.mean())

    def _count_active(self, img, rois):
        result = []
        for box in rois:
            crop = safe_crop(img, box)
            score = self._yellow_score(crop)
            result.append(score > self.yellow_threshold)
        return result

    def detect(self, img, scaled_rois):
        team1_lights = self._count_active(img, scaled_rois["turn_lights_team1"])
        team2_lights = self._count_active(img, scaled_rois["turn_lights_team2"])

        team1_count = sum(team1_lights)
        team2_count = sum(team2_lights)

        current_team = None
        if team1_count > team2_count:
            current_team = "team1"
        elif team2_count > team1_count:
            current_team = "team2"

        phase = "pick"
        step_index = max(team1_count, team2_count)

        return DraftState(
            phase=phase,
            current_team=current_team,
            my_team=None,
            is_my_turn=False,
            step_index=step_index,
        )