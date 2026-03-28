from pathlib import Path
import cv2
import numpy as np

IMAGE_EXTS = {'.png', '.jpg', '.jpeg', '.bmp', '.webp'}


def list_images(folder: Path):
    if not folder.exists():
        return []
    return sorted([p for p in folder.iterdir() if p.suffix.lower() in IMAGE_EXTS])


def read_image(path: Path):
    try:
        data = np.fromfile(str(path), dtype=np.uint8)
        if data.size == 0:
            return None
        return cv2.imdecode(data, cv2.IMREAD_COLOR)
    except Exception:
        return None


def save_image(path: Path, image) -> bool:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        ext = path.suffix.lower() or '.png'
        ok, encoded = cv2.imencode(ext, image)
        if not ok:
            return False
        encoded.tofile(str(path))
        return True
    except Exception:
        return False
