from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_DIR = BASE_DIR / 'dataset'
RAW_PREGAME_DIR = DATASET_DIR / 'raw_screens' / 'pregame'
CHAMPION_CANONICAL_DIR = DATASET_DIR / 'champion' / 'canonical'
CHAMPION_PICK_CROP_DIR = DATASET_DIR / 'champion' / 'pick_crop'
ALLY_PICKS_DIR = CHAMPION_PICK_CROP_DIR / 'ally_picks'
ENEMY_PICKS_DIR = CHAMPION_PICK_CROP_DIR / 'enemy_picks'
DEBUG_PREVIEW_DIR = DATASET_DIR / 'debug' / 'preview'
CHAMPION_CANONICAL_DIR = DATASET_DIR / "champion" / "canonical"
DEBUG_RESULT_DIR = DATASET_DIR / "debug" / "result"
ROLE_TEMPLATE_DIR = DATASET_DIR / "role" / "templates"
