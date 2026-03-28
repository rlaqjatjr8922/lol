from config.paths import RAW_PREGAME_DIR, DATASET_DIR
from src.utils.image_io import list_images, read_image
from src.extract.crop_slots import export_slots_from_image
from src.match.champion_matcher import match_champion


def print_match_results(folder_path, title):
    image_paths = list_images(folder_path)
    if not image_paths:
        return

    print()
    print(f"=== {title} ===")

    for image_path in image_paths:
        img = read_image(image_path)
        if img is None:
            print(f"[실패] 읽기 실패: {image_path.name}")
            continue

        name, score = match_champion(img)
        print(f"{image_path.name} -> {name} ({score:.4f})")


def run_pregame_pipeline():
    image_paths = list_images(RAW_PREGAME_DIR)

    if not image_paths:
        print("[안내] dataset/raw_screens/pregame 폴더에 이미지가 없습니다.")
        return

    print("=== 밴픽 파이프라인 시작 ===")

    for image_path in image_paths:
        print(f"[처리] {image_path.name}")
        export_slots_from_image(str(image_path))

    ally_dir = DATASET_DIR / "champion" / "pick_crop" / "ally_picks"
    enemy_dir = DATASET_DIR / "champion" / "pick_crop" / "enemy_picks"

    print_match_results(ally_dir, "ALLY PICKS MATCH")
    print_match_results(enemy_dir, "ENEMY PICKS MATCH")

    print()
    print("=== 완료 ===")