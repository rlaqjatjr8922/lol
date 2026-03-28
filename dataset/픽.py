import os
from PIL import Image, ImageDraw

# =========================
# 경로 설정
# =========================
INPUT_DIR = r"C:\Users\gimbe\OneDrive\Desktop\lol_project\dataset\champion"
OUTPUT_DIR = r"C:\Users\gimbe\OneDrive\Desktop\lol_project\dataset\픽"

IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp", ".bmp")
OUTPUT_SIZE = None   # 예: 116 으로 하면 116x116으로 저장, 그대로 두면 자동 크기 유지

os.makedirs(OUTPUT_DIR, exist_ok=True)

# =========================
# 유틸
# =========================
def is_image_file(filename: str) -> bool:
    return filename.lower().endswith(IMAGE_EXTS)

def center_crop_square(img: Image.Image) -> Image.Image:
    w, h = img.size
    s = min(w, h)
    left = (w - s) // 2
    top = (h - s) // 2
    return img.crop((left, top, left + s, top + s))

def make_circle_png(img: Image.Image, output_size=None) -> Image.Image:
    img = center_crop_square(img).convert("RGBA")

    if output_size is not None:
        img = img.resize((output_size, output_size), Image.LANCZOS)

    w, h = img.size

    # 원형 마스크 생성
    mask = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, w - 1, h - 1), fill=255)

    # 투명 배경 적용
    result = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    result.paste(img, (0, 0), mask)

    return result

# =========================
# 변환 실행
# =========================
count = 0

for filename in os.listdir(INPUT_DIR):
    if not is_image_file(filename):
        continue

    input_path = os.path.join(INPUT_DIR, filename)

    try:
        img = Image.open(input_path)
        out_img = make_circle_png(img, OUTPUT_SIZE)

        # 출력은 PNG로 저장
        stem = os.path.splitext(filename)[0]
        output_path = os.path.join(OUTPUT_DIR, stem + ".png")

        out_img.save(output_path, "PNG")
        print(f"[저장 완료] {output_path}")
        count += 1

    except Exception as e:
        print(f"[오류] {filename}: {e}")

print()
print(f"총 {count}개 완료")