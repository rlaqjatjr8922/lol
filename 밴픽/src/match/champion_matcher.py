from src.match.template_matcher import match_best_template
from config.paths import CHAMPION_CANONICAL_DIR


def match_champion(query_img):
    return match_best_template(query_img, CHAMPION_CANONICAL_DIR)
