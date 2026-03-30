from pathlib import Path

BASE_WIDTH = 2048
BASE_HEIGHT = 945

ICON_SIZE = 72
EMPTY_SCORE_THRESHOLD = 0.20
MATCH_SCORE_THRESHOLD = 0.60

DEBUG_SAVE = True
DEBUG_DIR = "debug_banpick"

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = str(PROJECT_ROOT / "data" / "champions")