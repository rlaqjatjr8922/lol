import cv2
import numpy as np
from pathlib import Path

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".webp"}

def list_images(folder: Path):
    if not folder.exists():
        return []
    return [p for p in folder.iterdir() if p.suffix.lower() in IMAGE_EXTS]

def read_image(path: Path):
    data = np.fromfile(str(path), dtype=np.uint8)
    img = cv2.imdecode(data, cv2.IMREAD_COLOR)
    return img

def save_image(path: Path, image):
    ext = path.suffix.lower() or ".png"
    ok, encoded = cv2.imencode(ext, image)
    if not ok:
        raise ValueError(f"이미지 저장 실패: {path}")
    path.write_bytes(encoded.tobytes())
