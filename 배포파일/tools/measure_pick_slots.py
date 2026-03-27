import os
import cv2
import numpy as np

IMAGE_PATH = r"C:\Users\gimbe\OneDrive\Desktop\lol_project\대이터추출\자료\a.jpg"
WINDOW_NAME = "measure_pick_slots"


def read_image_korean(path: str):
    try:
        data = np.fromfile(path, dtype=np.uint8)
        if data.size == 0:
            return None
        return cv2.imdecode(data, cv2.IMREAD_COLOR)
    except Exception:
        return None


class RoiMeasurer:
    def __init__(self, image):
        self.original = image
        self.display = image.copy()
        self.points = []
        self.boxes = []

    def reset_current(self):
        self.points = []
        self.redraw()

    def redraw(self):
        self.display = self.original.copy()

        for i, (x, y, w, h) in enumerate(self.boxes, 1):
            cv2.rectangle(self.display, (x, y), (x + w, y + h), (0, 255, 255), 2)
            cv2.putText(
                self.display,
                f"{i}: ({x}, {y}, {w}, {h})",
                (x, max(20, y - 8)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (0, 255, 255),
                2,
                cv2.LINE_AA,
            )

        if len(self.points) == 1:
            x, y = self.points[0]
            cv2.circle(self.display, (x, y), 4, (0, 0, 255), -1)

    def on_mouse(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.points.append((x, y))
            if len(self.points) == 2:
                (x1, y1), (x2, y2) = self.points
                left = min(x1, x2)
                top = min(y1, y2)
                w = abs(x2 - x1)
                h = abs(y2 - y1)
                self.boxes.append((left, top, w, h))
                print(f"ROI {len(self.boxes)} = ({left}, {top}, {w}, {h})")
                self.points = []
            self.redraw()


def main():
    img = read_image_korean(IMAGE_PATH)
    if img is None:
        print("이미지 읽기 실패:", IMAGE_PATH)
        return

    tool = RoiMeasurer(img)

    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.setMouseCallback(WINDOW_NAME, tool.on_mouse)

    print("좌클릭 2번: ROI 한 개 측정")
    print("r: 현재 측정 초기화")
    print("c: 마지막 ROI 삭제")
    print("q 또는 ESC: 종료")

    while True:
        cv2.imshow(WINDOW_NAME, tool.display)
        key = cv2.waitKey(20) & 0xFF

        if key in (27, ord('q')):
            break
        elif key == ord('r'):
            tool.reset_current()
        elif key == ord('c'):
            if tool.boxes:
                tool.boxes.pop()
                tool.redraw()

    cv2.destroyAllWindows()

    if tool.boxes:
        print("\n=== 최종 ROI 목록 ===")
        for i, roi in enumerate(tool.boxes, 1):
            print(f"{i}: {roi}")


if __name__ == "__main__":
    main()
