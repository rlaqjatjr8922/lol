import os
import re
import time
from io import BytesIO
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from PIL import Image

BASE_URL = "https://www.wildriftfire.com/"
SAVE_DIR = r"C:\Users\gimbe\OneDrive\Desktop\lol_project\대이터추출\결과"
TARGET_SIZE = (162, 162)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/137.0.0.0 Safari/537.36"
    )
}

session = requests.Session()
session.headers.update(HEADERS)


def get_soup(url: str) -> BeautifulSoup:
    resp = session.get(url, timeout=20)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")


def get_slug_from_href(href: str) -> str:
    # /guide/aatrox -> aatrox
    parts = href.strip("/").split("/")
    if len(parts) >= 2 and parts[0] == "guide":
        return parts[1].lower().strip()
    return ""


def get_champion_guides():
    soup = get_soup(BASE_URL)

    guides = []
    seen = set()

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()

        if not href.startswith("/guide/"):
            continue

        slug = get_slug_from_href(href)
        if not slug:
            continue

        # 챔피언 가이드만 남기기 위해 너무 이상한 slug 제외
        # 예: 너무 긴 경로나 중복 링크 방지
        if "/" in slug or len(slug) > 40:
            continue

        if slug in seen:
            continue
        seen.add(slug)

        guides.append({
            "slug": slug,
            "url": urljoin(BASE_URL, href)
        })

    guides.sort(key=lambda x: x["slug"])
    return guides


def normalize_image_url(raw_src: str, page_url: str) -> str:
    if not raw_src:
        return ""

    src = raw_src.strip()

    # //domain.com/a.png -> https://domain.com/a.png
    if src.startswith("//"):
        src = "https:" + src

    # 상대경로 -> 절대경로
    src = urljoin(page_url, src)

    # 중복 확장자 제거
    src = re.sub(r"\.png\.png($|\?)", r".png\1", src, flags=re.IGNORECASE)
    src = re.sub(r"\.jpg\.jpg($|\?)", r".jpg\1", src, flags=re.IGNORECASE)
    src = re.sub(r"\.jpeg\.jpeg($|\?)", r".jpeg\1", src, flags=re.IGNORECASE)
    src = re.sub(r"\.webp\.webp($|\?)", r".webp\1", src, flags=re.IGNORECASE)

    return src


def score_image_url(url: str, slug: str) -> int:
    score = 0
    lower_url = url.lower()

    if slug in lower_url:
        score += 10
    if "/images/champion/icon/" in lower_url:
        score += 8
    if "/images/champion/square/" in lower_url:
        score += 7
    if "/champion/icon/" in lower_url:
        score += 6
    if "/champion/square/" in lower_url:
        score += 5
    if lower_url.endswith(".png"):
        score += 3
    if "skin" in lower_url:
        score -= 3
    if "splash" in lower_url:
        score -= 3
    if "loading" in lower_url:
        score -= 3

    return score


def pick_best_champion_image(soup: BeautifulSoup, guide_url: str, slug: str) -> str:
    candidates = []

    # 1) 메타 태그 이미지
    for meta in soup.find_all("meta"):
        prop = meta.get("property", "").strip().lower()
        name = meta.get("name", "").strip().lower()
        content = meta.get("content", "").strip()

        if not content:
            continue

        if prop in ("og:image", "twitter:image") or name == "twitter:image":
            candidates.append(content)

    # 2) img 태그
    for img in soup.find_all("img", src=True):
        src = img["src"].strip()
        alt = (img.get("alt") or "").strip().lower()

        # 챔피언명 포함이면 우선 후보
        if slug in src.lower() or slug == alt or slug.replace("-", " ") in alt:
            candidates.insert(0, src)
        else:
            candidates.append(src)

    # URL 정리 및 중복 제거
    cleaned = []
    seen = set()
    for c in candidates:
        u = normalize_image_url(c, guide_url)
        if not u or u in seen:
            continue
        seen.add(u)
        cleaned.append(u)

    if not cleaned:
        return ""

    cleaned.sort(key=lambda x: score_image_url(x, slug), reverse=True)
    return cleaned[0]


def download_and_resize_to_png(url: str, save_path: str):
    resp = session.get(url, timeout=30)
    resp.raise_for_status()

    img = Image.open(BytesIO(resp.content)).convert("RGBA")
    img = img.resize(TARGET_SIZE, Image.LANCZOS)
    img.save(save_path, "PNG")


def main():
    os.makedirs(SAVE_DIR, exist_ok=True)

    try:
        guides = get_champion_guides()
    except Exception as e:
        print(f"[치명적 오류] 메인 페이지 로드 실패: {e}")
        return

    print(f"챔피언 수: {len(guides)}")

    ok_count = 0
    fail_count = 0
    fail_list = []

    for i, champ in enumerate(guides, 1):
        slug = champ["slug"]
        guide_url = champ["url"]

        try:
            soup = get_soup(guide_url)
            img_url = pick_best_champion_image(soup, guide_url, slug)

            if not img_url:
                print(f"[실패] {slug}: 이미지 URL 못 찾음")
                fail_count += 1
                fail_list.append(slug)
                continue

            save_path = os.path.join(SAVE_DIR, f"{slug}.png")
            download_and_resize_to_png(img_url, save_path)

            print(f"[{i}/{len(guides)}] 저장 완료: {slug}.png <- {img_url}")
            ok_count += 1

            time.sleep(0.15)

        except Exception as e:
            print(f"[에러] {slug}: {e}")
            fail_count += 1
            fail_list.append(slug)

    print("\n=== 완료 ===")
    print("성공:", ok_count)
    print("실패:", fail_count)
    print("저장 폴더:", SAVE_DIR)

    if fail_list:
        print("\n실패 목록:")
        for name in fail_list:
            print("-", name)


if __name__ == "__main__":
    main()