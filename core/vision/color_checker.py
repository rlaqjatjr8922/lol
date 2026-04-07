import subprocess
from pathlib import Path

import cv2
import numpy as np


class ScreenSource:
    def __init__(self, debug=False, debug_dir="debug"):
        self.scrcpy_path = r"C:\scrcpy-win64-v3.3.3\scrcpy.exe"
        self.process = None

        self.debug = debug
        self.debug_dir = Path(debug_dir) / "captures"
        self.capture_count = 0

        if self.debug:
            self.debug_dir.mkdir(parents=True, exist_ok=True)

        print("[ScreenSource] debug =", self.debug)
        print("[ScreenSource] debug_dir =", self.debug_dir)

    def _save_debug_image(self, save_path, image):
        try:
            ext = save_path.suffix
            success, encoded = cv2.imencode(ext, image)

            if not success:
                print(f"[ScreenSource] imencode 실패: {save_path}")
                return False

            encoded.tofile(str(save_path))
            return True

        except Exception as e:
            print(f"[ScreenSource] 저장 오류: {e}")
            return False

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

            if self.debug:
                filename = f"capture_{self.capture_count:04d}.png"
                save_path = self.debug_dir / filename

                saved = self._save_debug_image(save_path, frame)

                if saved:
                    print(f"[ScreenSource] debug 저장 성공: {save_path}")
                    self.capture_count += 1
                else:
                    print(f"[ScreenSource] debug 저장 실패: {save_path}")

            return frame

        except Exception as e:
            print(f"[ScreenSource] capture 오류: {e}")
            return None