import os
import re
import requests
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
from urllib.parse import urljoin

HOME_URL = "https://www.wildriftfire.com/"
OUTPUT_DIR = r"C:\Users\gimbe\OneDrive\Desktop\lol_project\dataset\champion\새 폴더"
TARGET_SIZE = (170, 170)

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": HOME_URL,
}

os.makedirs(OUTPUT_DIR, exist_ok=True)


def slugify_filename(name: str) -> str:
    name = name.strip().lower()
    name = name.replace("&", "and")
    name = re.sub(r"[.'’]", "", name)
    name = re.sub(r"[^a-z0-9]+", "-", name)
    name = re.sub(r"-+", "-", name).strip("-")
    return name + ".png"


def get_html(url: str) -> str:
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.text


def extract_guides():
    html = get_html(HOME_URL)
    soup = BeautifulSoup(html, "html.parser")

    guides = []
    seen = set()

    for a in soup.find_all("a", href=True):
        href = a.get("href", "").strip()
        text = a.get_text(" ", strip=True)

        if not href.startswith("/guide/"):
            continue
        if not text:
            continue

        guide_url = urljoin(HOME_URL, href)
        if guide_url in seen:
            continue

        seen.add(guide_url)
        guides.append((text, guide_url))

    return guides


def normalize_img_url(raw_url: str, guide_url: str) -> str:
    raw_url = raw_url.strip()
    full_url = urljoin(guide_url, raw_url)

    # 중복 확장자 강제 정리
    full_url = re.sub(r"\.png\.png$", ".png", full_url, flags=re.IGNORECASE)
    full_url = re.sub(r"\.jpg\.jpg$", ".jpg", full_url, flags=re.IGNORECASE)
    full_url = re.sub(r"\.jpeg\.jpeg$", ".jpeg", full_url, flags=re.IGNORECASE)
    full_url = re.sub(r"\.webp\.webp$", ".webp", full_url, flags=re.IGNORECASE)

    return full_url


def pick_image_from_guide(guide_url: str):
    html = get_html(guide_url)
    soup = BeautifulSoup(html, "html.parser")

    # 1순위: og:image
    tag = soup.find("meta", attrs={"property": "og:image"})
    if tag and tag.get("content"):
        return normalize_img_url(tag["content"], guide_url)

    # 2순위: twitter:image
    tag = soup.find("meta", attrs={"name": "twitter:image"})
    if tag and tag.get("content"):
        return normalize_img_url(tag["content"], guide_url)

    # 3순위: 페이지 내 img
    for img in soup.find_all("img", src=True):
        src = img["src"].strip()
        if src:
            return normalize_img_url(src, guide_url)

    return None


def download_resize_save(img_url: str, out_path: str):
    # 혹시라도 여기서 한 번 더 정리
    img_url = re.sub(r"\.png\.png$", ".png", img_url, flags=re.IGNORECASE)
    img_url = re.sub(r"\.jpg\.jpg$", ".jpg", img_url, flags=re.IGNORECASE)
    img_url = re.sub(r"\.jpeg\.jpeg$", ".jpeg", img_url, flags=re.IGNORECASE)
    img_url = re.sub(r"\.webp\.webp$", ".webp", img_url, flags=re.IGNORECASE)

    r = requests.get(img_url, headers=HEADERS, timeout=30)
    r.raise_for_status()

    img = Image.open(BytesIO(r.content)).convert("RGBA")
    img = img.resize(TARGET_SIZE, Image.LANCZOS)
    img.save(out_path, "PNG")


def main():
    guides = extract_guides()
    print(f"[INFO] guides: {len(guides)}")

    ok_count = 0
    fail_count = 0

    for champ_name, guide_url in guides:
        try:
            img_url = pick_image_from_guide(guide_url)
            if not img_url:
                raise RuntimeError("대표 이미지 URL 못 찾음")

            print("[IMG]", champ_name, "->", img_url)

            filename = slugify_filename(champ_name)
            out_path = os.path.join(OUTPUT_DIR, filename)

            download_resize_save(img_url, out_path)

            ok_count += 1
            print(f"[완료] {champ_name} -> {filename}")

        except Exception as e:
            fail_count += 1
            print(f"[실패] {champ_name}: {e}")

    print()
    print("=== 완료 ===")
    print("성공:", ok_count)
    print("실패:", fail_count)
    print("저장 폴더:", OUTPUT_DIR)


if __name__ == "__main__":
    main()