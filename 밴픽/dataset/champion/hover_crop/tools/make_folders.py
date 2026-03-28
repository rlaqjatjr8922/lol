from config.paths import (
    RAW_PREGAME_DIR,
    RAW_DEBUG_DIR,
    CHAMPION_CANONICAL_DIR,
    CHAMPION_BAN_CROP_DIR,
    CHAMPION_PICK_CROP_DIR,
    CHAMPION_HOVER_CROP_DIR,
    ROLE_TEMPLATE_DIR,
    ROLE_CROP_DIR,
    UI_EMPTY_DIR,
    UI_HOVER_DIR,
    UI_LOCKED_DIR,
    UI_BANNED_DIR,
    DEBUG_PREVIEW_DIR,
    DEBUG_RESULT_DIR,
)

ALL_DIRS = [
    RAW_PREGAME_DIR,
    RAW_DEBUG_DIR,
    CHAMPION_CANONICAL_DIR,
    CHAMPION_BAN_CROP_DIR,
    CHAMPION_PICK_CROP_DIR,
    CHAMPION_HOVER_CROP_DIR,
    ROLE_TEMPLATE_DIR,
    ROLE_CROP_DIR,
    UI_EMPTY_DIR,
    UI_HOVER_DIR,
    UI_LOCKED_DIR,
    UI_BANNED_DIR,
    DEBUG_PREVIEW_DIR,
    DEBUG_RESULT_DIR,
]


def main():
    for folder in ALL_DIRS:
        folder.mkdir(parents=True, exist_ok=True)
        print(f"[생성] {folder}")


if __name__ == "__main__":
    main()
