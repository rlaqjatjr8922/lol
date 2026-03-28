import os
from typing import List, Optional

import cv2
import numpy as np

from device.device_state import DeviceState


def load_image_list(folder: str) -> List[str]:
    if not os.path.isdir(folder):
        return []

    files = []
    for name in os.listdir(folder):
        if name.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".webp")):
            files.append(os.path.join(folder, name))

    files.sort()
    return files


def read_image_korean(path: str) -> Optional[np.ndarray]:
    data = np.fromfile(path, dtype=np.uint8)
    if data.size == 0:
        return None
    return cv2.imdecode(data, cv2.IMREAD_COLOR)


def load_latest_frame(device_state: DeviceState):
    files = load_image_list(device_state.screenshot_dir)
    if not files:
        return None, None

    latest = files[-1]
    img = read_image_korean(latest)
    return img, latest
