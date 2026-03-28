from config.paths import RAW_PREGAME_DIR
from src.utils.image_io import list_images, read_image
from src.extract.crop_slots import process_pregame_image


def run_pregame_pipeline():
    image_paths = list_images(RAW_PREGAME_DIR)
    if not image_paths:
        print("[안내] dataset/raw_screens/pregame 폴더에 이미지가 없습니다.")
        return

    print("=== 밴픽 파이프라인 시작 ===")
    for image_path in image_paths:
        print(f"[처리] {image_path.name}")
        image = read_image(image_path)
        if image is None:
            print(f"[실패] 이미지 로드 실패: {image_path}")
            continue
        process_pregame_image(image, image_path.stem)
    print("=== 완료 ===")
