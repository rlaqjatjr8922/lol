from .models import BanPickSnapshot
from .roi import get_scaled_rois
from .image_utils import safe_crop
from .slot_detector import SlotDetector
from .state_detector import StateDetector
from .side_resolver import apply_my_team_to_state
from .recommender_bridge import should_run_recommend, build_recommend_input


class BanPickController:
    def __init__(self, my_team="team1"):
        self.slot_detector = SlotDetector()
        self.state_detector = StateDetector()
        self.my_team = my_team

    def _detect_group(self, img, rois):
        crops = [safe_crop(img, box) for box in rois]
        return self.slot_detector.detect_many(crops)

    def process(self, img):
        scaled_rois = get_scaled_rois(img.shape)

        snapshot = BanPickSnapshot()

        snapshot.ally_bans = self._detect_group(img, scaled_rois["ally_bans"])
        snapshot.enemy_bans = self._detect_group(img, scaled_rois["enemy_bans"])
        snapshot.ally_picks = self._detect_group(img, scaled_rois["ally_picks"])
        snapshot.enemy_picks = self._detect_group(img, scaled_rois["enemy_picks"])

        hover_crop = safe_crop(img, scaled_rois["hover_pick"])
        snapshot.hover_pick = self.slot_detector.detect_slot(hover_crop)

        snapshot.state = self.state_detector.detect(img, scaled_rois)
        snapshot.state = apply_my_team_to_state(snapshot.state, self.my_team)

        recommend_payload = None
        if should_run_recommend(snapshot):
            recommend_payload = build_recommend_input(snapshot)

        return snapshot, recommend_payload