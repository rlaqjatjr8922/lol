import os
import cv2
import numpy as np


INPUT_DIR = r"C:\Users\gimbe\OneDrive\Desktop\lol_project\대이터추출\자료"
OUTPUT_DIR = r"C:\Users\gimbe\OneDrive\Desktop\lol_project\dataset\raw_slots"

IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp", ".bmp")

USE_SCALED_ROI = False
BASE_W = 2280
BASE_H = 1080

# 크게 잡고, 저장할 때 원형 바깥만 제거
ROI_CONFIG = {
    "ally_picks": [
        (198, 146, 116, 116),
        (198, 292, 116, 116),
        (198, 438, 116, 116),
        (198, 584, 116, 116),
        (198, 730, 116, 116),
    ],
    "enemy_picks": [
        (2100, 146, 116, 116),
        (2100, 292, 116, 116),
        (2100, 438, 116, 116),
        (2100, 584, 116, 116),
        (2100, 730, 116, 116),
    ],
}


def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def read_image_korean(path: str):
    try:
        data = np.fromfile(path, dtype=np.uint8)
        if data.size == 0:
            return None
        return cv2.imdecode(data, cv2.IMREAD_COLOR)
    except Exception:
        return None


def write_image_korean(path: str, image) -> bool:
    try:
        folder = os.path.dirname(path)
        if folder:
            os.makedirs(folder, exist_ok=True)

        ext = os.path.splitext(path)[1]
        if not ext:
            ext = ".png"
            path += ext

        ok, encoded = cv2.imencode(ext, image)
        if not ok:
            return False

        encoded.tofile(path)
        return True
    except Exception:
        return False


def scale_roi(roi, img_shape):
    ih, iw = img_shape[:2]
    sx = iw / float(BASE_W)
    sy = ih / float(BASE_H)
    x, y, w, h = roi
    return (
        int(round(x * sx)),
        int(round(y * sy)),
        max(1, int(round(w * sx))),
        max(1, int(round(h * sy))),
    )


def scaled_roi_config(img):
    return {
        key: [scale_roi(roi, img.shape) for roi in rois]
        for key, rois in ROI_CONFIG.items()
    }


def crop_roi(img, roi):
    x, y, w, h = roi
    ih, iw = img.shape[:2]

    x = max(0, min(iw - 1, x))
    y = max(0, min(ih - 1, y))
    w = max(1, min(iw - x, w))
    h = max(1, min(ih - y, h))

    return img[y:y + h, x:x + w].copy()


def draw_roi_preview(img, roi_config):
    preview = img.copy()

    colors = {
        "ally_picks": (0, 255, 255),
        "enemy_picks": (255, 0, 255),
    }

    for group_name, roi_list in roi_config.items():
        color = colors.get(group_name, (255, 255, 255))

        for idx, roi in enumerate(roi_list, 1):
            x, y, w, h = roi
            cv2.rectangle(preview, (x, y), (x + w, y + h), color, 2)
            label = f"{group_name}_{idx}"
            cv2.putText(
                preview,
                label,
                (x, max(15, y - 6)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.42,
                color,
                1,
                cv2.LINE_AA
            )

    return preview


def make_circle_masked_crop(crop):
    h, w = crop.shape[:2]

    mask = np.zeros((h, w), dtype=np.uint8)
    cx = w // 2
    cy = h // 2

    # 얼굴은 충분히 살리고, 슬롯 테두리는 최대한 제거
    r = int(min(h, w) * 0.44)

    cv2.circle(mask, (cx, cy), r, 255, -1)

    masked = np.zeros_like(crop)
    masked[mask == 255] = crop[mask == 255]
    return masked


def export_slots_from_image(image_path: str):
    image_name = os.path.basename(image_path)
    stem = os.path.splitext(image_name)[0]

    img = read_image_korean(image_path)
    if img is None:
        print(f"[실패] 이미지 읽기 실패: {image_name}")
        return 0

    cfg = scaled_roi_config(img) if USE_SCALED_ROI else ROI_CONFIG

    save_count = 0

    for group_name, roi_list in cfg.items():
        group_dir = os.path.join(OUTPUT_DIR, group_name)
        ensure_dir(group_dir)

        for idx, roi in enumerate(roi_list, 1):
            crop = crop_roi(img, roi)
            masked = make_circle_masked_crop(crop)

            save_path = os.path.join(group_dir, f"{stem}__{group_name}_{idx}.png")

            if write_image_korean(save_path, masked):
                save_count += 1
            else:
                print(f"[실패] 저장 실패: {save_path}")

    preview = draw_roi_preview(img, cfg)
    preview_dir = os.path.join(OUTPUT_DIR, "_preview")
    ensure_dir(preview_dir)
    preview_path = os.path.join(preview_dir, f"{stem}__roi_preview.png")
    write_image_korean(preview_path, preview)

    print(f"[완료] {image_name} -> {save_count}개 저장")
    return save_count


def main():
    ensure_dir(OUTPUT_DIR)

    files = []
    for name in os.listdir(INPUT_DIR):
        if name.lower().endswith(IMAGE_EXTS):
            files.append(os.path.join(INPUT_DIR, name))

    files.sort()

    if not files:
        print("[안내] 입력 폴더에 이미지가 없습니다.")
        print("입력 폴더:", INPUT_DIR)
        return

    total_saved = 0
    for path in files:
        total_saved += export_slots_from_image(path)

    print()
    print("=== 완료 ===")
    print("입력 이미지 수:", len(files))
    print("총 저장 슬롯 수:", total_saved)
    print("출력 폴더:", OUTPUT_DIR)


if __name__ == "__main__":
    main()