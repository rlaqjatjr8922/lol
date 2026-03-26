
import os
import re
from functools import lru_cache
from typing import Dict, List, Tuple

import cv2
import numpy as np

from device.capture import load_image_list, read_image_korean
from core.data.data_loader import load_champion_db
from core.data.champion_mapper import champion_to_korean

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_DIR = os.path.join(PROJECT_ROOT, "Data")

PREGAME_IMAGE_DIR = os.environ.get(
    "LOL_PREGAME_IMAGE_DIR",
    r"C:\Users\gimbe\OneDrive\Desktop\lol_project\대이터추출\자료",
)
DEBUG_DIR = os.environ.get(
    "LOL_DEBUG_DIR",
    r"C:\Users\gimbe\OneDrive\Desktop\lol_project\대이터추출\결과",
)

CHAMP_TEMPLATE_DIR = os.path.join(DATA_DIR, "Champion")
IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp", ".bmp")

BASE_W, BASE_H = 2280, 1080
CHAMP_MATCH_THRESHOLD = float(os.environ.get("LOL_CHAMP_MATCH_THRESHOLD", "0.30"))
SAVE_DEBUG = True
DETECT_DEBUG = os.environ.get("LOL_DETECT_DEBUG", "0").strip() in ("1", "true", "True")

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

ROLE_FILE_TO_KO = {
    "top": "탑",
    "jungle": "정글",
    "mid": "미드",
    "bottom_duo": "원딜",
    "support": "서폿",
}


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def imwrite_korean(path: str, img: np.ndarray) -> None:
    ok, buf = cv2.imencode(".png", img)
    if ok:
        buf.tofile(path)


def crop_roi(img: np.ndarray, roi: Tuple[int, int, int, int]) -> np.ndarray:
    x, y, w, h = roi
    ih, iw = img.shape[:2]
    x = max(0, min(iw - 1, x))
    y = max(0, min(ih - 1, y))
    w = max(1, min(iw - x, w))
    h = max(1, min(ih - y, h))
    return img[y:y + h, x:x + w]


def _scale_roi(roi: Tuple[int, int, int, int], img_shape) -> Tuple[int, int, int, int]:
    ih, iw = img_shape[:2]
    if iw == BASE_W and ih == BASE_H:
        return roi
    sx = iw / float(BASE_W)
    sy = ih / float(BASE_H)
    x, y, w, h = roi
    return (
        int(round(x * sx)),
        int(round(y * sy)),
        max(1, int(round(w * sx))),
        max(1, int(round(h * sy))),
    )


def _scaled_roi_config(img: np.ndarray):
    return {k: [_scale_roi(r, img.shape) for r in v] for k, v in ROI_CONFIG.items()}


def draw_roi_preview(img: np.ndarray, scaled_config=None) -> np.ndarray:
    preview = img.copy()
    cfg = scaled_config or ROI_CONFIG
    colors = {
        "ally_bans": (0, 255, 0),
        "enemy_bans": (0, 0, 255),
        "ally_picks": (255, 200, 0),
        "enemy_picks": (255, 0, 255),
        "ally_roles": (0, 255, 255),
    }
    for group_name, rois in cfg.items():
        color = colors.get(group_name, (255, 255, 255))
        for idx, (x, y, w, h) in enumerate(rois, 1):
            cv2.rectangle(preview, (x, y), (x + w, y + h), color, 2)
            cv2.putText(
                preview,
                f"{group_name}_{idx}",
                (x, max(15, y - 5)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.42,
                color,
                1,
                cv2.LINE_AA,
            )
    return preview


def _slugify(name: str) -> str:
    s = (name or "").strip().lower()
    s = s.replace("&", " amp ")
    s = s.replace("’", "'")
    s = s.replace("'", "")
    s = s.replace(".", "")
    s = re.sub(r"[^a-z0-9\s-]", " ", s)
    s = re.sub(r"\s+", "-", s)
    s = re.sub(r"-{2,}", "-", s).strip("-")
    return s


@lru_cache(maxsize=1)
def _load_champion_templates() -> Dict[str, np.ndarray]:
    result: Dict[str, np.ndarray] = {}
    missing = []
    for name in sorted(load_champion_db()):
        slug = _slugify(name)
        path = os.path.join(CHAMP_TEMPLATE_DIR, f"{slug}.png")
        if not os.path.exists(path):
            missing.append(f"{name} -> {slug}.png")
            continue
        img = read_image_korean(path)
        if img is not None and img.size > 0:
            result[name] = img

    if DETECT_DEBUG:
        print(f"[detector] templates loaded: {len(result)} / {len(load_champion_db())}")
        if missing:
            print(f"[detector] missing templates sample: {missing[:10]}")

    return result


def _to_korean(name: str) -> str:
    if not name:
        return ""
    try:
        return champion_to_korean(name)
    except Exception:
        return name


def _center_crop(img: np.ndarray, margin_ratio: float = 0.08) -> np.ndarray:
    h, w = img.shape[:2]
    m = int(min(h, w) * margin_ratio)
    if m <= 0 or h - 2 * m < 8 or w - 2 * m < 8:
        return img
    return img[m:h - m, m:w - m]


def _prep(img: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    img = _center_crop(img, 0.08)
    img = cv2.resize(img, (96, 96), interpolation=cv2.INTER_AREA)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)
    edges = cv2.Canny(gray, 45, 140)
    return gray, edges


def _score(a: np.ndarray, b: np.ndarray) -> float:
    ag, ae = _prep(a)
    bg, be = _prep(b)
    s1 = float(cv2.matchTemplate(ag, bg, cv2.TM_CCOEFF_NORMED)[0][0])
    s2 = float(cv2.matchTemplate(ae, be, cv2.TM_CCOEFF_NORMED)[0][0])
    return 0.70 * s1 + 0.30 * s2


def _top_matches(crop: np.ndarray, templates: Dict[str, np.ndarray], topk: int = 3):
    scored = []
    for name, tmpl in templates.items():
        scored.append((name, _score(crop, tmpl)))
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:topk]


def _detect_list(img: np.ndarray, rois: List[Tuple[int, int, int, int]], group_name: str):
    templates = _load_champion_templates()
    result: List[str] = []
    scores: List[float] = []

    for idx, roi in enumerate(rois, 1):
        crop = crop_roi(img, roi)
        best_name = ""
        best_score = -1.0

        for name, tmpl in templates.items():
            s = _score(crop, tmpl)
            if s > best_score:
                best_score = s
                best_name = name

        if DETECT_DEBUG:
            print(f"[{group_name}_{idx}] top3 = {_top_matches(crop, templates, 3)}")
            print(f"[{group_name}_{idx}] selected = {best_name!r}, score = {best_score:.4f}")

        if best_score < CHAMP_MATCH_THRESHOLD:
            result.append("")
        else:
            result.append(best_name)
        scores.append(float(best_score))

    return result, scores


def _save_debug(base_name: str, img: np.ndarray, scaled_config) -> Dict[str, object]:
    ensure_dir(DEBUG_DIR)
    debug_paths: Dict[str, object] = {}

    preview = draw_roi_preview(img, scaled_config)
    preview_path = os.path.join(DEBUG_DIR, f"{base_name}__pregame_roi_preview.png")
    imwrite_korean(preview_path, preview)
    debug_paths["roi_preview"] = preview_path

    for group_name, rois in scaled_config.items():
        saved_list = []
        for idx, roi in enumerate(rois, 1):
            crop = crop_roi(img, roi)
            save_path = os.path.join(DEBUG_DIR, f"{base_name}__{group_name}_{idx}.png")
            imwrite_korean(save_path, crop)
            saved_list.append(save_path)
        debug_paths[group_name] = saved_list

    return debug_paths


def scan_latest_draft_image(preferred_lane: str = "") -> dict:
    images = load_image_list(PREGAME_IMAGE_DIR)
    if not images:
        return {"ok": False, "error": "no_images", "image_dir": PREGAME_IMAGE_DIR}

    path = images[-1]
    img = read_image_korean(path)
    if img is None:
        return {"ok": False, "error": "image_read_failed", "image_path": path}

    cfg = _scaled_roi_config(img)

    ally_bans, ally_bans_scores = _detect_list(img, cfg["ally_bans"], "ally_bans")
    enemy_bans, enemy_bans_scores = _detect_list(img, cfg["enemy_bans"], "enemy_bans")
    ally_picks, ally_picks_scores = _detect_list(img, cfg["ally_picks"], "ally_picks")
    enemy_picks, enemy_picks_scores = _detect_list(img, cfg["enemy_picks"], "enemy_picks")

    ally_bans_ko = [_to_korean(x) for x in ally_bans]
    enemy_bans_ko = [_to_korean(x) for x in enemy_bans]
    ally_picks_ko = [_to_korean(x) for x in ally_picks]
    enemy_picks_ko = [_to_korean(x) for x in enemy_picks]

    base = os.path.splitext(os.path.basename(path))[0]
    debug_paths = _save_debug(base, img, cfg) if SAVE_DEBUG else {}

    if DETECT_DEBUG:
        print("[detector] image:", path)
        print("[detector] ally_picks:", list(zip(ally_picks, ally_picks_scores)))
        print("[detector] enemy_picks:", list(zip(enemy_picks, enemy_picks_scores)))

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
        "my_champ": "",
        "enemy_champ": "",
        "my_champ_ko": "",
        "enemy_champ_ko": "",
        "debug_paths": debug_paths,
        "match_scores": {
            "ally_bans": ally_bans_scores,
            "enemy_bans": enemy_bans_scores,
            "ally_picks": ally_picks_scores,
            "enemy_picks": enemy_picks_scores,
        },
        "config_base_resolution": (BASE_W, BASE_H),
        "image_resolution": (img.shape[1], img.shape[0]),
    }


def autofill_view_from_latest_image(view) -> str:
    result = scan_latest_draft_image()

    try:
        if hasattr(view, "set_detected_picks"):
            view.set_detected_picks(result)
        if hasattr(view, "set_detected_previews"):
            view.set_detected_previews(result)
    except Exception:
        pass

    if not result.get("ok"):
        return f"자동 인식 실패: {result.get('error', 'unknown')}"

    ally_text = ", ".join([x or "-" for x in result.get("ally_picks_ko", [])])
    enemy_text = ", ".join([x or "-" for x in result.get("enemy_picks_ko", [])])
    return f"자동 인식 완료 | 아군: {ally_text} | 적군: {enemy_text}"


if __name__ == "__main__":
    os.environ["LOL_DETECT_DEBUG"] = "1"
    print(scan_latest_draft_image())
