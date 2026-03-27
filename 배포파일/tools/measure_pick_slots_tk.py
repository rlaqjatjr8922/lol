import os
import tkinter as tk
from PIL import Image, ImageTk

IMAGE_PATH = r"C:\Users\gimbe\OneDrive\Desktop\lol_project\대이터추출\자료\a.jpg"
MAX_WIDTH = 1600
MAX_HEIGHT = 900


class RoiTool:
    def __init__(self, root, image_path):
        self.root = root
        self.root.title("measure_pick_slots_tk")

        self.image_path = image_path
        self.original_image = Image.open(image_path)
        self.orig_w, self.orig_h = self.original_image.size

        scale_w = MAX_WIDTH / self.orig_w
        scale_h = MAX_HEIGHT / self.orig_h
        self.scale = min(scale_w, scale_h, 1.0)

        self.disp_w = int(self.orig_w * self.scale)
        self.disp_h = int(self.orig_h * self.scale)
        self.display_image = self.original_image.resize((self.disp_w, self.disp_h))
        self.photo = ImageTk.PhotoImage(self.display_image)

        self.canvas = tk.Canvas(root, width=self.disp_w, height=self.disp_h, bg="black")
        self.canvas.pack()
        self.canvas.create_image(0, 0, anchor="nw", image=self.photo)

        self.info = tk.Label(root, text="드래그해서 ROI 선택 | c: 마지막 삭제 | q: 종료", font=("맑은 고딕", 10))
        self.info.pack(fill="x")

        self.start_x = None
        self.start_y = None
        self.current_rect = None
        self.boxes = []
        self.labels = []

        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

        self.root.bind("c", self.on_delete_last)
        self.root.bind("q", self.on_quit)
        self.root.bind("<Escape>", self.on_quit)

    def to_original(self, x, y):
        ox = int(round(x / self.scale))
        oy = int(round(y / self.scale))
        return ox, oy

    def on_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        if self.current_rect is not None:
            self.canvas.delete(self.current_rect)
            self.current_rect = None

    def on_drag(self, event):
        if self.start_x is None or self.start_y is None:
            return

        if self.current_rect is not None:
            self.canvas.delete(self.current_rect)

        self.current_rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, event.x, event.y,
            outline="yellow", width=2
        )

    def on_release(self, event):
        if self.start_x is None or self.start_y is None:
            return

        x1, y1 = self.start_x, self.start_y
        x2, y2 = event.x, event.y

        left = min(x1, x2)
        top = min(y1, y2)
        right = max(x1, x2)
        bottom = max(y1, y2)

        ox1, oy1 = self.to_original(left, top)
        ox2, oy2 = self.to_original(right, bottom)

        ow = ox2 - ox1
        oh = oy2 - oy1

        if ow > 0 and oh > 0:
            rect_id = self.canvas.create_rectangle(left, top, right, bottom, outline="cyan", width=2)
            text = f"{len(self.boxes)+1}: ({ox1}, {oy1}, {ow}, {oh})"
            text_id = self.canvas.create_text(left, max(10, top - 10), anchor="sw", text=text, fill="cyan", font=("맑은 고딕", 10, "bold"))
            self.boxes.append((rect_id, text_id, (ox1, oy1, ow, oh)))
            print(f"ROI {len(self.boxes)} = ({ox1}, {oy1}, {ow}, {oh})")

        if self.current_rect is not None:
            self.canvas.delete(self.current_rect)
            self.current_rect = None

        self.start_x = None
        self.start_y = None

    def on_delete_last(self, event=None):
        if not self.boxes:
            return
        rect_id, text_id, _ = self.boxes.pop()
        self.canvas.delete(rect_id)
        self.canvas.delete(text_id)
        print("마지막 ROI 삭제")

    def on_quit(self, event=None):
        if self.boxes:
            print("\n=== 최종 ROI 목록 ===")
            for i, (_, _, roi) in enumerate(self.boxes, 1):
                print(f"{i}: {roi}")
        self.root.destroy()


def main():
    if not os.path.exists(IMAGE_PATH):
        print("이미지 없음:", IMAGE_PATH)
        return

    root = tk.Tk()
    app = RoiTool(root, IMAGE_PATH)
    root.mainloop()


if __name__ == "__main__":
    main()
