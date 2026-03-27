import os
import re
from functools import lru_cache

import cv2
import numpy as np

from device.capture import load_image_list, read_image_korean
from core.data.data_loader import load_champion_db
from core.data.champion_mapper import champion_to_korean


# =========================
# 경로
# =========================
PREGAME_IMAGE_DIR = os.environ.get(
    "LOL_PREGAME_IMAGE_DIR",
    r"C:\Users\gimbe\OneDrive\Desktop\lol_project\대이터추출\자료",
)

DEBUG_DIR = os.environ.get(
    "LOL_DEBUG_DIR",
    r"C:\Users\gimbe\OneDrive\Desktop\lol_project\대이터추출\결과",
)

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
DATA_DIR = os.path.join(PROJECT_ROOT, "Data")
CHAMP_TEMPLATE_DIR = os.path.join(DATA_DIR, "Champion")

DETECT_DEBUG = os.environ.get("LOL_DETECT_DEBUG", "1").strip().lower() in ("1", "true", "yes")
CHAMP_MATCH_THRESHOLD = float(os.environ.get("LOL_CHAMP_MATCH_THRESHOLD", "0.25"))

USE_SCALED_ROI = False
BASE_W = 2280
BASE_H = 1080


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


# =========================
# 유틸
# =========================
def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def imwrite_korean(path: str, image) -> bool:
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


def _to_korean(name: str) -> str:
    text = (name or "").strip()
    if not text:
        return ""
    try:
        return champion_to_korean(text)
    except Exception:
        return text


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


def _scale_roi(roi, img_shape):
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


def _scaled_roi_config(img):
    return {
        key: [_scale_roi(roi, img.shape) for roi in rois]
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

    group_colors = {
        "ally_bans": (0, 255, 0),
        "enemy_bans": (0, 0, 255),
        "ally_picks": (255, 200, 0),
        "enemy_picks": (255, 0, 255),
        "ally_roles": (0, 255, 255),
    }

    for group_name, roi_list in roi_config.items():
        color = group_colors.get(group_name, (255, 255, 255))

        for idx, roi in enumerate(roi_list, 1):
            x, y, w, h = roi
            cv2.rectangle(preview, (x, y), (x + w, y + h), color, 2)

            label = f"{group_name}_{idx}"
            text_y = max(15, y - 6)
            cv2.putText(
                preview,
                label,
                (x, text_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.42,
                color,
                1,
                cv2.LINE_AA
            )

    return preview


def validate_rois(img, roi_config):
    img_h, img_w = img.shape[:2]
    has_warning = False

    for group_name, roi_list in roi_config.items():
        for idx, (x, y, w, h) in enumerate(roi_list, 1):
            if x < 0 or y < 0 or x + w > img_w or y + h > img_h:
                print(
                    f"[경고] {group_name}_{idx} ROI가 이미지 밖일 수 있음: "
                    f"({x}, {y}, {w}, {h}) / 이미지크기 {img_w}x{img_h}"
                )
                has_warning = True

    return has_warning


# =========================
# 원형 저장 / 원형 매칭용
# =========================
def _make_circle_mask(size=96, shrink=0.90):
    mask = np.zeros((size, size), dtype=np.uint8)
    r = int((size * shrink) / 2)
    cv2.circle(mask, (size // 2, size // 2), r, 255, -1)
    return mask


def _apply_circle_mask_to_bgr(img, size=162, shrink=0.90):
    """
    저장용: 픽 이미지를 원형으로 저장
    바깥은 검정 배경
    """
    img = cv2.resize(img, (size, size), interpolation=cv2.INTER_AREA)

    mask = np.zeros((size, size), dtype=np.uint8)
    r = int((size * shrink) / 2)
    cx = size // 2
    cy = size // 2
    cv2.circle(mask, (cx, cy), r, 255, -1)

    out = np.zeros_like(img)
    out[mask == 255] = img[mask == 255]
    return out


# =========================
# 템플릿 로딩
# =========================
@lru_cache(maxsize=1)
def _load_champion_templates():
    result = {}
    missing = []

    champion_db = load_champion_db()
    if isinstance(champion_db, dict):
        champion_names = list(champion_db.keys())
    else:
        champion_names = list(champion_db)

    for name in sorted(champion_names):
        slug = _slugify(name)
        path = os.path.join(CHAMP_TEMPLATE_DIR, f"{slug}.png")

        if not os.path.exists(path):
            missing.append(f"{name} -> {slug}.png")
            continue

        img = read_image_korean(path)
        if img is not None:
            result[name] = img

    if DETECT_DEBUG:
        print(f"[pregame_pick_detector] templates loaded: {len(result)} / {len(champion_names)}")
        if missing:
            print("[pregame_pick_detector] missing templates sample:")
            for x in missing[:20]:
                print("  ", x)

    return result


# =========================
# 밴 전처리 / 점수
# =========================
def _prep_ban(img):
    img = cv2.resize(img, (96, 96), interpolation=cv2.INTER_AREA)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)
    edges = cv2.Canny(gray, 45, 140)
    return gray, edges


def _score_ban(a, b):
    ag, ae = _prep_ban(a)
    bg, be = _prep_ban(b)

    s1 = float(cv2.matchTemplate(ag, bg, cv2.TM_CCOEFF_NORMED)[0][0])
    s2 = float(cv2.matchTemplate(ae, be, cv2.TM_CCOEFF_NORMED)[0][0])

    return 0.70 * s1 + 0.30 * s2


# =========================
# 픽 전처리 / 점수
# =========================
def _prep_pick(img):
    h, w = img.shape[:2]

    # ROI는 그대로 두고, 내부 전처리만 함
    # 아래쪽 역할/장식 영향 줄이기
    img = img[:int(h * 0.82), :]
    img = cv2.resize(img, (96, 96), interpolation=cv2.INTER_AREA)

    mask = _make_circle_mask(96, 0.90)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)
    gray = cv2.bitwise_and(gray, gray, mask=mask)

    edges = cv2.Canny(gray, 45, 140)
    edges = cv2.bitwise_and(edges, edges, mask=mask)

    return gray, edges


def _score_pick(a, b):
    ag, ae = _prep_pick(a)
    bg, be = _prep_pick(b)

    s1 = float(cv2.matchTemplate(ag, bg, cv2.TM_CCOEFF_NORMED)[0][0])
    s2 = float(cv2.matchTemplate(ae, be, cv2.TM_CCOEFF_NORMED)[0][0])

    return 0.70 * s1 + 0.30 * s2


# =========================
# 감지
# =========================
def _detect_bans(img, rois, top_n=3):
    templates = _load_champion_templates()
    result = []
    scores = []
    top_candidates = []

    for roi in rois:
        crop = crop_roi(img, roi)

        ranked = []
        for name, tmpl in templates.items():
            try:
                s = _score_ban(crop, tmpl)
                ranked.append((name, float(s)))
            except Exception:
                continue

        ranked.sort(key=lambda x: x[1], reverse=True)

        best_name = ""
        best_score = -1.0
        if ranked:
            best_name, best_score = ranked[0]

        if best_score < CHAMP_MATCH_THRESHOLD:
            result.append("")
        else:
            result.append(best_name)

        scores.append(float(best_score))
        top_candidates.append(ranked[:top_n])

    return result, scores, top_candidates


def _detect_picks(img, rois, top_n=3):
    templates = _load_champion_templates()
    result = []
    scores = []
    top_candidates = []

    for roi in rois:
        crop = crop_roi(img, roi)

        ranked = []
        for name, tmpl in templates.items():
            try:
                s = _score_pick(crop, tmpl)
                ranked.append((name, float(s)))
            except Exception:
                continue

        ranked.sort(key=lambda x: x[1], reverse=True)

        best_name = ""
        best_score = -1.0
        second_score = -1.0

        if ranked:
            best_name, best_score = ranked[0]
        if len(ranked) >= 2:
            second_score = ranked[1][1]

        gap = best_score - second_score if second_score >= 0 else 1.0

        # 확정 규칙 완화
        if best_score < 0.56:
            result.append("")
        elif gap < 0.008:
            result.append("")
        else:
            result.append(best_name)

        scores.append(float(best_score))
        top_candidates.append(ranked[:top_n])

    return result, scores, top_candidates


# =========================
# 디버그 저장
# =========================
def _save_debug_rois(img, roi_config, image_path: str):
    ensure_dir(DEBUG_DIR)

    base = os.path.splitext(os.path.basename(image_path))[0]
    debug_paths = {}

    for group, rois in roi_config.items():
        group_paths = []

        for i, roi in enumerate(rois, 1):
            crop = crop_roi(img, roi)

            # 픽은 원형으로 저장, 밴/역할은 그대로 저장
            if group in ("ally_picks", "enemy_picks"):
                crop_to_save = _apply_circle_mask_to_bgr(crop, size=162, shrink=0.90)
            else:
                crop_to_save = crop

            save_path = os.path.join(DEBUG_DIR, f"{base}__{group}_{i}.png")
            imwrite_korean(save_path, crop_to_save)
            group_paths.append(save_path)

        debug_paths[group] = group_paths

    preview = draw_roi_preview(img, roi_config)
    preview_path = os.path.join(DEBUG_DIR, f"{base}__roi_preview.png")
    imwrite_korean(preview_path, preview)

    return debug_paths, preview_path


# =========================
# 메인 감지
# =========================
def scan_latest_draft_image(preferred_lane=""):
    images = load_image_list(PREGAME_IMAGE_DIR)
    if not images:
        return {
            "ok": False,
            "error": "no_images",
            "image_dir": PREGAME_IMAGE_DIR,
        }

    path = images[-1]
    img = read_image_korean(path)
    if img is None:
        return {
            "ok": False,
            "error": "image_read_failed",
            "image_path": path,
        }

    cfg = _scaled_roi_config(img) if USE_SCALED_ROI else ROI_CONFIG
    validate_rois(img, cfg)

    ally_bans, ally_bans_scores, ally_bans_top = _detect_bans(img, cfg["ally_bans"])
    enemy_bans, enemy_bans_scores, enemy_bans_top = _detect_bans(img, cfg["enemy_bans"])
    ally_picks, ally_picks_scores, ally_picks_top = _detect_picks(img, cfg["ally_picks"])
    enemy_picks, enemy_picks_scores, enemy_picks_top = _detect_picks(img, cfg["enemy_picks"])

    ally_roles = [""] * len(cfg.get("ally_roles", []))

    ally_bans_ko = [_to_korean(x) for x in ally_bans]
    enemy_bans_ko = [_to_korean(x) for x in enemy_bans]
    ally_picks_ko = [_to_korean(x) for x in ally_picks]
    enemy_picks_ko = [_to_korean(x) for x in enemy_picks]

    debug_paths, preview_path = _save_debug_rois(img, cfg, path)

    match_scores = {
        "ally_bans": ally_bans_scores,
        "enemy_bans": enemy_bans_scores,
        "ally_picks": ally_picks_scores,
        "enemy_picks": enemy_picks_scores,
    }

    top_candidates = {
        "ally_bans": ally_bans_top,
        "enemy_bans": enemy_bans_top,
        "ally_picks": ally_picks_top,
        "enemy_picks": enemy_picks_top,
    }

    my_champ = ally_picks[0] if ally_picks else ""
    enemy_champ = enemy_picks[0] if enemy_picks else ""

    result = {
        "ok": True,
        "image_path": path,

        "my_champ": my_champ,
        "my_champ_ko": _to_korean(my_champ),

        "enemy_champ": enemy_champ,
        "enemy_champ_ko": _to_korean(enemy_champ),

        "ally_bans": ally_bans,
        "enemy_bans": enemy_bans,
        "ally_picks": ally_picks,
        "enemy_picks": enemy_picks,
        "ally_roles": ally_roles,

        "ally_bans_ko": ally_bans_ko,
        "enemy_bans_ko": enemy_bans_ko,
        "ally_picks_ko": ally_picks_ko,
        "enemy_picks_ko": enemy_picks_ko,

        "debug_paths": debug_paths,
        "preview_path": preview_path,
        "match_scores": match_scores,
        "top_candidates": top_candidates,
        "debug_dir": DEBUG_DIR,
        "config_base_resolution": (BASE_W, BASE_H),
        "image_resolution": (img.shape[1], img.shape[0]),
    }

    if DETECT_DEBUG:
        print("[pregame_pick_detector] image:", path)
        print("[pregame_pick_detector] ally_picks:", list(zip(ally_picks, ally_picks_scores)))
        print("[pregame_pick_detector] enemy_picks:", list(zip(enemy_picks, enemy_picks_scores)))
        print("[pregame_pick_detector] top ally picks:", ally_picks_top)
        print("[pregame_pick_detector] top enemy picks:", enemy_picks_top)
        print("[pregame_pick_detector] preview:", preview_path)
        print("[pregame_pick_detector] debug dir:", DEBUG_DIR)

    return result


# =========================
# 레포 호환 함수
# =========================
def autofill_view_from_latest_image(view, preferred_lane=""):
    result = scan_latest_draft_image(preferred_lane=preferred_lane)

    if not result.get("ok"):
        return result

    if hasattr(view, "set_detected_picks"):
        try:
            view.set_detected_picks(result)
        except Exception as e:
            if DETECT_DEBUG:
                print("[pregame_pick_detector] set_detected_picks error:", e)

    if hasattr(view, "set_detected_previews"):
        try:
            view.set_detected_previews(result)
        except Exception as e:
            if DETECT_DEBUG:
                print("[pregame_pick_detector] set_detected_previews error:", e)

    return result