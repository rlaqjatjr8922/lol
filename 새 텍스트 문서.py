import os
import cv2
import numpy as np


INPUT_DIR = r"C:\Users\gimbe\OneDrive\Desktop\lol_project\배포파일\Data\Champion"
OUTPUT_DIR = r"C:\Users\gimbe\OneDrive\Desktop\lol_project\배포파일\Data\Champion_PickStyle"

FINAL_SIZE = 162
PREP_SIZE = 96


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


def make_circle_mask(size=96, shrink=0.88):
    mask = np.zeros((size, size), dtype=np.uint8)
    r = int((size * shrink) / 2)
    cv2.circle(mask, (size // 2, size // 2), r, 255, -1)
    return mask


def convert_template_to_pick_style(img):
    h, w = img.shape[:2]
    if h <= 0 or w <= 0:
        return None

    # 실제 pick detector와 비슷하게 아래쪽 영향 줄이기
    img = img[:int(h * 0.82), :]

    # 정사각형화
    h, w = img.shape[:2]
    side = min(h, w)
    x1 = (w - side) // 2
    y1 = (h - side) // 2
    img = img[y1:y1 + side, x1:x1 + side]

    # detector 전처리와 비슷한 크기
    img = cv2.resize(img, (PREP_SIZE, PREP_SIZE), interpolation=cv2.INTER_AREA)

    # 원형 마스크
    mask = make_circle_mask(PREP_SIZE, shrink=0.88)

    out = np.zeros_like(img)
    out[mask == 255] = img[mask == 255]

    # 저장용으로 조금 크게
    out = cv2.resize(out, (FINAL_SIZE, FINAL_SIZE), interpolation=cv2.INTER_CUBIC)
    return out


def main():
    ensure_dir(OUTPUT_DIR)

    exts = (".png", ".jpg", ".jpeg", ".webp", ".bmp")
    files = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith(exts)]
    files.sort()

    count_ok = 0
    count_fail = 0

    for name in files:
        src_path = os.path.join(INPUT_DIR, name)
        dst_path = os.path.join(OUTPUT_DIR, name)

        img = read_image_korean(src_path)
        if img is None:
            print(f"[실패] 읽기 실패: {name}")
            count_fail += 1
            continue

        out = convert_template_to_pick_style(img)
        if out is None:
            print(f"[실패] 변환 실패: {name}")
            count_fail += 1
            continue

        ok = write_image_korean(dst_path, out)
        if ok:
            print(f"[완료] {name}")
            count_ok += 1
        else:
            print(f"[실패] 저장 실패: {name}")
            count_fail += 1

    print()
    print("=== 완료 ===")
    print("성공:", count_ok)
    print("실패:", count_fail)
    print("출력 폴더:", OUTPUT_DIR)


if __name__ == "__main__":
    main()