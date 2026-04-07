import subprocess
import time
from pathlib import Path
import requests

DEBUG_PORT = 9222
DEBUG_URL = f"http://127.0.0.1:{DEBUG_PORT}"
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
USER_DATA_DIR = r"C:\chrome-debug"


def is_debug_browser_running() -> bool:
    try:
        r = requests.get(f"{DEBUG_URL}/json/version", timeout=1.5)
        return r.status_code == 200
    except:
        return False


def start_debug_chrome():
    chrome_path = Path(CHROME_PATH)

    if not chrome_path.exists():
        raise FileNotFoundError("Chrome 없음")

    Path(USER_DATA_DIR).mkdir(parents=True, exist_ok=True)

    subprocess.Popen(
        [
            str(chrome_path),
            f"--remote-debugging-port={DEBUG_PORT}",
            f"--user-data-dir={USER_DATA_DIR}",
            "https://chatgpt.com",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    for _ in range(40):
        if is_debug_browser_running():
            return
        time.sleep(0.1)

    raise RuntimeError("Chrome 실행 실패")


def ensure_debug_chrome():
    if not is_debug_browser_running():
        start_debug_chrome()