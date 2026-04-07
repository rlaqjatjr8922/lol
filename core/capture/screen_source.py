import subprocess

import cv2
import numpy as np


class ScreenSource:
    def __init__(self):
        self.scrcpy_path = r"C:\scrcpy-win64-v3.3.3\scrcpy.exe"
        self.process = None

    def start(self):
        try:
            self.process = subprocess.Popen([
                self.scrcpy_path,
                "--window-width", "540",
                "--window-height", "1170"
            ])
            print("[ScreenSource] scrcpy 실행됨")
        except Exception as e:
            print(f"[ScreenSource] 실행 오류: {e}")

    def capture(self):
        try:
            result = subprocess.run(
                ["adb", "exec-out", "screencap", "-p"],
                stdout=subprocess.PIPE
            )

            if not result.stdout:
                print("[ScreenSource] 캡처 데이터 없음")
                return None

            img_array = np.frombuffer(result.stdout, dtype=np.uint8)
            frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

            if frame is None:
                print("[ScreenSource] frame decode 실패")
                return None

            return frame

        except Exception as e:
            print(f"[ScreenSource] capture 오류: {e}")
            return None