import time
import subprocess
from pathlib import Path

import cv2
import numpy as np
import mss
import win32gui
import win32con


SCRCPY_EXE = r"C:\scrcpy-win64-v3.3.3\scrcpy.exe"
WINDOW_WAIT_SECONDS = 12


def save_image_korean_path(path, image):
    path = Path(path)
    ext = path.suffix if path.suffix else ".png"
    ok, buf = cv2.imencode(ext, image)
    if not ok:
        return False
    buf.tofile(str(path))
    return True


def is_probable_scrcpy_mirror_window(title: str) -> bool:
    t = title.strip().lower()
    if not t:
        return False

    positive = ["scrcpy", "android", "sm-", "pixel", "xiaomi", "redmi", "galaxy", "device"]
    if not any(p in t for p in positive):
        return False

    negative = ["scrcpy-win64", "검색", "file explorer", "explorer", "local disk", "로컬 디스크"]
    if any(n in t for n in negative):
        return False

    return True


def launch_scrcpy(scrcpy_exe=SCRCPY_EXE):
    try:
        subprocess.Popen([scrcpy_exe], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"[INFO] scrcpy 실행 요청: {scrcpy_exe}")
        return True
    except FileNotFoundError:
        print(f"[오류] scrcpy 실행 파일을 찾을 수 없습니다: {scrcpy_exe}")
        return False


def debug_print_visible_windows():
    print("\n[DEBUG] 현재 보이는 창 제목들:")
    titles = []

    def enum_handler(hwnd, _ctx):
        if not win32gui.IsWindowVisible(hwnd):
            return
        title = win32gui.GetWindowText(hwnd).strip()
        if title:
            titles.append(title)

    win32gui.EnumWindows(enum_handler, None)

    for t in titles:
        print(" -", t)


def find_scrcpy_window():
    result = []

    def enum_handler(hwnd, _ctx):
        if not win32gui.IsWindowVisible(hwnd):
            return
        title = win32gui.GetWindowText(hwnd).strip()
        if not title:
            return
        if is_probable_scrcpy_mirror_window(title):
            result.append((hwnd, title))

    win32gui.EnumWindows(enum_handler, None)

    if not result:
        return None, None

    for hwnd, title in result:
        if "scrcpy" in title.lower() and "win64" not in title.lower():
            return hwnd, title

    return result[0]


def wait_for_window(timeout=WINDOW_WAIT_SECONDS):
    start = time.time()
    while time.time() - start < timeout:
        hwnd, title = find_scrcpy_window()
        if hwnd is not None:
            return hwnd, title
        time.sleep(0.3)
    return None, None


def get_client_rect_on_screen(hwnd):
    left, top, right, bottom = win32gui.GetClientRect(hwnd)
    pt_left_top = win32gui.ClientToScreen(hwnd, (left, top))
    pt_right_bottom = win32gui.ClientToScreen(hwnd, (right, bottom))
    x1, y1 = pt_left_top
    x2, y2 = pt_right_bottom
    return {"left": x1, "top": y1, "width": x2 - x1, "height": y2 - y1}


def bring_window_to_front(hwnd):
    try:
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32gui.SetForegroundWindow(hwnd)
    except Exception:
        pass


def capture_window_frame(sct, hwnd):
    rect = get_client_rect_on_screen(hwnd)
    if rect["width"] <= 0 or rect["height"] <= 0:
        return None
    shot = sct.grab(rect)
    frame = np.array(shot)
    frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
    return frame


class RealtimeCapture:
    def __init__(self, scrcpy_exe=SCRCPY_EXE, window_wait_seconds=WINDOW_WAIT_SECONDS):
        self.scrcpy_exe = scrcpy_exe
        self.window_wait_seconds = window_wait_seconds
        self.hwnd = None
        self.title = None
        self.sct = None

    def open(self):
        launch_scrcpy(self.scrcpy_exe)
        hwnd, title = wait_for_window(self.window_wait_seconds)
        if hwnd is None:
            debug_print_visible_windows()
            raise RuntimeError("scrcpy 미러링 창을 찾지 못했습니다.")
        self.hwnd = hwnd
        self.title = title
        bring_window_to_front(hwnd)
        self.sct = mss.mss()
        print(f"[INFO] 연결된 창: {title}")

    def read(self):
        if self.sct is None or self.hwnd is None:
            return None
        return capture_window_frame(self.sct, self.hwnd)

    def close(self):
        if self.sct is not None:
            self.sct.close()
            self.sct = None
