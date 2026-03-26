import os
import re
import json
from functools import lru_cache
from typing import Dict, List, Tuple

import cv2
import numpy as np

from device.capture import load_image_list, read_image_korean
from core.data.data_loader import load_champion_db


# =========================
# 경로
# =========================
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_DIR = os.path.join(PROJECT_ROOT, "Data")

PREGAME_IMAGE_DIR = r"C:\Users\gimbe\OneDrive\Desktop\lol_project\대이터추출\자료"
DEBUG_DIR = r"C:\Users\gimbe\OneDrive\Desktop\lol_project\대이터추출\결과"

CHAMP_TEMPLATE_DIR = os.path.join(DATA_DIR, "Champion")
ROLE_TEMPLATE_DIR = os.path.join(DATA_DIR, "Role")

IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp", ".bmp")


# =========================
# ROI
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
        (194, 144, 121, 121),
        (194, 290, 121, 121),
        (194, 439, 121, 121),
        (194, 585, 121, 121),
        (194, 732, 121, 121),
    ],
    "enemy_picks": [
        (2099, 144, 121, 121),
        (2099, 290, 121, 121),
        (2099, 439, 121, 121),
        (2099, 585, 121, 121),
        (2099, 732, 121, 121),
    ],
    "ally_roles": [
        (235, 231, 40, 40),
        (235, 378, 40, 40),
        (235, 525, 40, 40),
        (235, 672, 40, 40),
        (235, 819, 40, 40),
    ],
}


# =========================
# 설정
# =========================
CHAMP_MATCH_THRESHOLD = 0.33
ROLE_MATCH_THRESHOLD = 0.35


# =========================
# 한국어 변환
# =========================
@lru_cache(maxsize=1)
def _load_champion_ko_map():
    path = os.path.join(DATA_DIR, "Champion_KO.json")
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _to_korean(name: str) -> str:
    if not name:
        return ""
    return _load_champion_ko_map().get(name, name)


# =========================
# 유틸
# =========================
def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def imwrite_korean(path, img):
    ok, buf = cv2.imencode(".png", img)
    if ok:
        buf.tofile(path)


def crop_roi(img, roi):
    x, y, w, h = roi
    return img[y:y + h, x:x + w]


# =========================
# 템플릿 로딩
# =========================
@lru_cache(maxsize=1)
def _load_champion_templates():
    result = {}
    for name in load_champion_db():
        slug = name.lower().replace(" ", "-").replace("'", "")
        path = os.path.join(CHAMP_TEMPLATE_DIR, f"{slug}.png")
        if os.path.exists(path):
            img = read_image_korean(path)
            if img is not None:
                result[name] = img
    return result


# =========================
# 매칭
# =========================
def _score(a, b):
    a = cv2.resize(a, (96, 96))
    b = cv2.resize(b, (96, 96))

    g1 = cv2.cvtColor(a, cv2.COLOR_BGR2GRAY)
    g2 = cv2.cvtColor(b, cv2.COLOR_BGR2GRAY)

    return cv2.matchTemplate(g1, g2, cv2.TM_CCOEFF_NORMED)[0][0]


def _detect_list(img, rois):
    templates = _load_champion_templates()
    result = []

    for roi in rois:
        crop = crop_roi(img, roi)

        best_name = ""
        best_score = -1

        for name, tmpl in templates.items():
            s = _score(crop, tmpl)
            if s > best_score:
                best_score = s
                best_name = name

        if best_score < CHAMP_MATCH_THRESHOLD:
            result.append("")
        else:
            result.append(best_name)

    return result


# =========================
# 메인
# =========================
def scan_latest_draft_image(preferred_lane=""):
    images = load_image_list(PREGAME_IMAGE_DIR)
    if not images:
        return {"ok": False}

    path = images[-1]
    img = read_image_korean(path)

    ally_bans = _detect_list(img, ROI_CONFIG["ally_bans"])
    enemy_bans = _detect_list(img, ROI_CONFIG["enemy_bans"])
    ally_picks = _detect_list(img, ROI_CONFIG["ally_picks"])
    enemy_picks = _detect_list(img, ROI_CONFIG["enemy_picks"])

    # 한국어 변환
    ally_bans_ko = [_to_korean(x) for x in ally_bans]
    enemy_bans_ko = [_to_korean(x) for x in enemy_bans]
    ally_picks_ko = [_to_korean(x) for x in ally_picks]
    enemy_picks_ko = [_to_korean(x) for x in enemy_picks]

    base = os.path.splitext(os.path.basename(path))[0]

    ensure_dir(DEBUG_DIR)

    debug_paths = {}

    for group, rois in ROI_CONFIG.items():
        lst = []
        for i, roi in enumerate(rois, 1):
            crop = crop_roi(img, roi)
            save = os.path.join(DEBUG_DIR, f"{base}__{group}_{i}.png")
            imwrite_korean(save, crop)
            lst.append(save)
        debug_paths[group] = lst

    return {
        "ok": True,
        "image_path": path,

        "ally_bans": ally_bans,
        "enemy_bans": enemy_bans,
        "ally_picks": ally_picks,
        "enemy_picks": enemy_picks,

        "ally_bans_ko": ally_bans_ko,
        "enemy_bans_ko": enemy_bans_ko,
        "ally_picks_ko": ally_picks_ko,
        "enemy_picks_ko": enemy_picks_ko,

        "debug_paths": debug_paths,
    }


# =========================
# UI 연결
# =========================
def autofill_view_from_latest_image(view):
    result = scan_latest_draft_image()

    if hasattr(view, "set_detected_picks"):
        view.set_detected_picks(result)

    if hasattr(view, "set_detected_previews"):
        view.set_detected_previews(result)

    return "자동 인식 완료"