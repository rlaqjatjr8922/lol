import subprocess
import time

import requests


PORT = 9222
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
USER_DATA_DIR = r"C:\chrome-debug"


def is_debug_browser_running() -> bool:
    try:
        r = requests.get(f"http://127.0.0.1:{PORT}/json/version", timeout=2)
        return r.status_code == 200
    except Exception:
        return False


def start_debug_chrome() -> bool:
    try:
        subprocess.Popen([
            CHROME_PATH,
            f"--remote-debugging-port={PORT}",
            f"--user-data-dir={USER_DATA_DIR}",
            "https://chatgpt.com",
        ])
    except Exception:
        return False

    for _ in range(30):
        if is_debug_browser_running():
            return True
        time.sleep(1)

    return False