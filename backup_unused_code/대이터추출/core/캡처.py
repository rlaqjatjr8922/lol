import subprocess
import tkinter as tk
from datetime import datetime
import os

ADB_PATH = r"C:\platform-tools\adb.exe"
SAVE_DIR = r"C:\Users\gimbe\OneDrive\Desktop\lol_project\대이터추출\자료"

os.makedirs(SAVE_DIR, exist_ok=True)


def take_screenshot():
    try:
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screen_{now}.png"
        save_path = os.path.join(SAVE_DIR, filename)

        result = subprocess.run(
            [ADB_PATH, "exec-out", "screencap", "-p"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )

        data = result.stdout

        if not data:
            print("에러: 스크린샷 데이터가 비어 있음")
            return

        with open(save_path, "wb") as f:
            f.write(data)

        print(f"저장 완료: {save_path}")
        print(f"파일 크기: {len(data)} bytes")

    except subprocess.CalledProcessError as e:
        print("ADB 실행 에러")
        print("returncode:", e.returncode)
        print("stderr:", e.stderr.decode("utf-8", errors="ignore"))

    except Exception as e:
        print("에러:", e)


root = tk.Tk()
root.title("빠른 스크린샷")

btn = tk.Button(root, text="📸 빠른 스샷", command=take_screenshot, width=20, height=2)
btn.pack(padx=20, pady=20)

root.mainloop()