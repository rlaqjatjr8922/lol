import os
import cv2
import numpy as np

# =========================
# 경로
# =========================
INPUT_DIR = r"C:\Users\gimbe\OneDrive\Desktop\lol_project\대이터추출\자료"
OUTPUT_DIR = r"C:\Users\gimbe\OneDrive\Desktop\lol_project\대이터추출\결과"

IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp", ".bmp")

# =========================
# 픽셀 기준 ROI
# 기준 해상도: 현재 쓰는 스샷 기준
# ally_roles 추가
# =========================
ROI_CONFIG = {
    "ally_bans": [
        (113, 19, 71, 71),
        (199, 19, 71, 71),
        (285, 19, 71, 71),
        (372, 19, 71, 71),
        (459, 19, 71, 71),
    ],
    "enemy_bans": [
        (1811, 19, 71, 71),
        (1897, 19, 71, 71),
        (1983, 19, 71, 71),
        (2070, 19, 71, 71),
        (2156, 19, 71, 71),
    ],
    "ally_picks": [
        (200, 150, 109, 109),
        (200, 296, 109, 109),
        (200, 445, 109, 109),
        (200, 591, 109, 109),
        (200, 738, 109, 109),
    ],
    "enemy_picks": [
        (2105, 150, 109, 109),
        (2105, 296, 109, 109),
        (2105, 445, 109, 109),
        (2105, 591, 109, 109),
        (2105, 738, 109, 109),
    ],
    "ally_roles": [
        (235, 231, 40, 40),
        (235, 378, 40, 40),
        (235, 525, 40, 40),
        (235, 672, 40, 40),
        (235, 819, 40, 40),
    ],
}

# 미리보기 이미지 저장 여부
SAVE_PREVIEW = True


def imread_korean(path):
    data = np.fromfile(path, dtype=np.uint8)
    if data.size == 0:
        return None
    return cv2.imdecode(data, cv2.IMREAD_COLOR)


def imwrite_korean(path, img):
    ext = os.path.splitext(path)[1]
    if ext == "":
        ext = ".png"
        path += ".png"

    ok, buf = cv2.imencode(ext, img)
    if ok:
        buf.tofile(path)


def get_image_files(folder):
    if not os.path.exists(folder):
        return []

    files = []
    for name in os.listdir(folder):
        path = os.path.join(folder, name)
        if os.path.isfile(path) and name.lower().endswith(IMAGE_EXTS):
            files.append(path)

    files.sort()
    return files


def crop_roi(img, roi):
    x, y, w, h = roi
    img_h, img_w = img.shape[:2]

    x = max(0, min(x, img_w - 1))
    y = max(0, min(y, img_h - 1))
    w = max(1, min(w, img_w - x))
    h = max(1, min(h, img_h - y))

    return img[y:y + h, x:x + w]


def draw_roi_preview(img, roi_config):
    preview = img.copy()

    group_colors = {
        "ally_bans": (0, 255, 0),
        "enemy_bans": (0, 0, 255),
        "ally_picks": (255, 200, 0),
        "enemy_picks": (255, 0, 255),
        "ally_roles": (0, 255, 255),
    }

    for group_name, roi_list in roi_config.items():
        color = group_colors.get(group_name, (255, 255, 255))

        for idx, roi in enumerate(roi_list, 1):
            x, y, w, h = roi
            cv2.rectangle(preview, (x, y), (x + w, y + h), color, 2)

            label = f"{group_name}_{idx}"
            text_y = max(15, y - 6)
            cv2.putText(
                preview,
                label,
                (x, text_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.42,
                color,
                1,
                cv2.LINE_AA
            )

    return preview


def validate_rois(img, roi_config):
    img_h, img_w = img.shape[:2]
    has_warning = False

    for group_name, roi_list in roi_config.items():
        for idx, (x, y, w, h) in enumerate(roi_list, 1):
            if x < 0 or y < 0 or x + w > img_w or y + h > img_h:
                print(f"[경고] {group_name}_{idx} ROI가 이미지 밖일 수 있음: ({x}, {y}, {w}, {h}) / 이미지크기 {img_w}x{img_h}")
                has_warning = True

    return has_warning


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    image_files = get_image_files(INPUT_DIR)
    print(f"자료 폴더 이미지 수: {len(image_files)}")

    if not image_files:
        print("자료 폴더에 이미지가 없습니다.")
        return

    saved_count = 0

    for img_path in image_files:
        img = imread_korean(img_path)
        if img is None:
            print(f"[실패] 이미지 로드 불가: {img_path}")
            continue

        base_name = os.path.splitext(os.path.basename(img_path))[0]
        h, w = img.shape[:2]
        print(f"\n처리 중: {base_name} | 크기: {w}x{h}")

        validate_rois(img, ROI_CONFIG)

        for group_name, roi_list in ROI_CONFIG.items():
            for idx, roi in enumerate(roi_list, 1):
                cropped = crop_roi(img, roi)

                if cropped is None or cropped.size == 0:
                    print(f"  [건너뜀] {group_name}_{idx} 크롭 실패")
                    continue

                save_name = f"{base_name}__{group_name}_{idx}.png"
                save_path = os.path.join(OUTPUT_DIR, save_name)
                imwrite_korean(save_path, cropped)

                print(f"  저장 완료: {save_name}")
                saved_count += 1

        if SAVE_PREVIEW:
            preview = draw_roi_preview(img, ROI_CONFIG)
            preview_name = f"{base_name}__roi_preview.png"
            preview_path = os.path.join(OUTPUT_DIR, preview_name)
            imwrite_korean(preview_path, preview)
            print(f"  미리보기 저장 완료: {preview_name}")

    print("\n=== 완료 ===")
    print(f"총 저장 개수: {saved_count}")
    print(f"저장 폴더: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()