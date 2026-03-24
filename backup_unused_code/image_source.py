import os
from typing import List, Optional

import cv2
import numpy as np


IMAGE_DIR = r"C:\Users\gimbe\OneDrive\Desktop\lol_project\대이터추출\자료"


def load_image_list(folder: str) -> List[str]:
    if not os.path.isdir(folder):
        return []

    files = []
    for name in os.listdir(folder):
        if name.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".webp")):
            files.append(os.path.join(folder, name))

    files.sort()
    return files


def imread_korean(path: str) -> Optional[np.ndarray]:
    data = np.fromfile(path, dtype=np.uint8)
    if data.size == 0:
        return None
    return cv2.imdecode(data, cv2.IMREAD_COLOR)


class FolderImageSource:
    def __init__(self, folder: str = IMAGE_DIR):
        self.folder = folder
        self.paths = load_image_list(folder)
        self.index = 0

    def count(self) -> int:
        return len(self.paths)

    def current_path(self) -> str:
        if not self.paths:
            return ""
        return self.paths[self.index]

    def get_current_frame(self) -> Optional[np.ndarray]:
        if not self.paths:
            return None
        return imread_korean(self.paths[self.index])

    def next(self):
        if not self.paths:
            return
        self.index = (self.index + 1) % len(self.paths)

    def prev(self):
        if not self.paths:
            return
        self.index = (self.index - 1) % len(self.paths)