import cv2
import numpy as np


def safe_crop(img, box):
    x, y, w, h = box
    ih, iw = img.shape[:2]

    x1 = max(0, x)
    y1 = max(0, y)
    x2 = min(iw, x + w)
    y2 = min(ih, y + h)

    if x1 >= x2 or y1 >= y2:
        return None

    return img[y1:y2, x1:x2].copy()


def to_gray(img):
    if img is None:
        return None
    if len(img.shape) == 2:
        return img
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


def preprocess_icon(img, size=72):
    if img is None:
        return None
    gray = to_gray(img)
    gray = cv2.resize(gray, (size, size), interpolation=cv2.INTER_AREA)
    gray = cv2.GaussianBlur(gray, (3, 3), 0)
    return gray


def cosine_similarity(a, b):
    a = a.astype(np.float32).reshape(-1)
    b = b.astype(np.float32).reshape(-1)

    na = np.linalg.norm(a)
    nb = np.linalg.norm(b)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def mean_brightness(img):
    if img is None:
        return 0.0
    gray = to_gray(img)
    return float(np.mean(gray))