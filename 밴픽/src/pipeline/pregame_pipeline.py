from config.paths import RAW_PREGAME_DIR, DATASET_DIR, DEBUG_RESULT_DIR
from src.utils.image_io import list_images, read_image
from src.extract.crop_slots import export_slots_from_image
from src.match.champion_matcher import match_champion
from src.match.match_debug import save_pair_debug


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

        name, score, best_raw, best_path = match_champion(img)
        print(f"{image_path.name} -> {name} ({score:.4f})")

        if best_raw is not None and best_path is not None:
            out_path = DEBUG_RESULT_DIR / f"{image_path.stem}__PAIR.png"
            save_pair_debug(
                output_path=out_path,
                query_img=img,
                cand_img=best_raw,
                score=score,
                query_name=image_path.name,
                cand_name=best_path.name,
            )


def run_pregame_pipeline():
    image_paths = list_images(RAW_PREGAME_DIR)

    if not image_paths:
        print("[안내] dataset/raw_screens/pregame 폴더에 이미지가 없습니다.")
        return

    print("=== 밴픽 파이프라인 시작 ===")

    for image_path in image_paths:
        print(f"[처리] {image_path.name}")

        img = read_image(image_path)
        if img is None:
            print(f"[실패] 이미지 읽기 실패: {image_path.name}")
            continue

        export_slots_from_image(
            img=img,
            image_stem=image_path.stem,
            original_name=image_path.name,
        )

    ally_dir = DATASET_DIR / "champion" / "pick_crop" / "ally_picks"
    enemy_dir = DATASET_DIR / "champion" / "pick_crop" / "enemy_picks"

    print_match_results(ally_dir, "ALLY PICKS MATCH")
    print_match_results(enemy_dir, "ENEMY PICKS MATCH")

    print()
    print("=== 완료 ===")