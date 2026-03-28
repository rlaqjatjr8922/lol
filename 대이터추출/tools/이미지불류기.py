import os
import json
import shutil
import math
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk, ImageOps

import torch
import torch.nn as nn
from torchvision import transforms, models


# =========================
# 경로 설정
# =========================
SOURCE_DIR = r"C:\Users\gimbe\OneDrive\Desktop\lol_project\dataset\test"
TARGET_DIR = r"C:\Users\gimbe\OneDrive\Desktop\lol_project\dataset\champion"
MAP_PATH = r"C:\Users\gimbe\OneDrive\Desktop\lol_project\대이터추출\champion_map.json"
STATE_MODEL_PATH = r"C:\Users\gimbe\OneDrive\Desktop\lol_project\dataset\state_classifier.pt"

IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp", ".bmp")

MAX_W = 700
MAX_H = 700

STATE_IMAGE_SIZE = 96
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# 비어있음 미리보기 썸네일 크기
THUMB_SIZE = 120
THUMB_COLS = 5


def 상태모델_불러오기():
    model = models.resnet18(weights=None)
    model.fc = nn.Linear(model.fc.in_features, 2)
    model.load_state_dict(torch.load(STATE_MODEL_PATH, map_location=DEVICE))
    model = model.to(DEVICE)
    model.eval()
    return model


def 픽됨_예측(model, image_path):
    tf = transforms.Compose([
        transforms.Resize((STATE_IMAGE_SIZE, STATE_IMAGE_SIZE)),
        transforms.ToTensor(),
    ])

    image = Image.open(image_path).convert("RGB")
    x = tf(image).unsqueeze(0).to(DEVICE)

    with torch.no_grad():
        out = model(x)
        probs = torch.softmax(out, dim=1)[0]
        pred = out.argmax(dim=1).item()

    # 0=비어있음, 1=픽됨
    비어있음확률 = float(probs[0])
    픽됨확률 = float(probs[1])

    return pred == 1, 비어있음확률, 픽됨확률


class 비어있음확인창:
    def __init__(self, root, 비어있음목록):
        self.root = root
        self.비어있음목록 = 비어있음목록
        self.결정 = None
        self.썸네일들 = []

        self.window = tk.Toplevel(root)
        self.window.title("비어있음 이미지 확인")
        self.window.geometry("900x780")
        self.window.grab_set()

        상단 = tk.Frame(self.window)
        상단.pack(fill="x", padx=10, pady=10)

        설명 = tk.Label(
            상단,
            text=f"비어있음으로 예측된 이미지 {len(비어있음목록)}개\n확인 후 한 번에 삭제하거나 유지할 수 있습니다.",
            justify="left",
            font=("맑은 고딕", 11, "bold"),
            anchor="w"
        )
        설명.pack(anchor="w")

        본문 = tk.Frame(self.window)
        본문.pack(fill="both", expand=True, padx=10, pady=10)

        canvas = tk.Canvas(본문)
        scrollbar = tk.Scrollbar(본문, orient="vertical", command=canvas.yview)
        self.scroll_frame = tk.Frame(canvas)

        self.scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.썸네일_채우기()

        하단 = tk.Frame(self.window)
        하단.pack(fill="x", padx=10, pady=10)

        유지버튼 = tk.Button(
            하단,
            text="삭제 안 함",
            command=self.유지,
            font=("맑은 고딕", 10)
        )
        유지버튼.pack(side="left")

        삭제버튼 = tk.Button(
            하단,
            text="비어있음 전부 삭제",
            command=self.삭제,
            font=("맑은 고딕", 10, "bold"),
            bg="#d9534f",
            fg="white"
        )
        삭제버튼.pack(side="right")

        self.window.protocol("WM_DELETE_WINDOW", self.유지)

    def 썸네일_채우기(self):
        for idx, item in enumerate(self.비어있음목록):
            path = item["path"]
            file_name = os.path.basename(path)

            try:
                pil = Image.open(path).convert("RGB")
                pil = ImageOps.contain(pil, (THUMB_SIZE, THUMB_SIZE))
                photo = ImageTk.PhotoImage(pil)
                self.썸네일들.append(photo)

                cell = tk.Frame(self.scroll_frame, bd=1, relief="solid", padx=5, pady=5)
                r = idx // THUMB_COLS
                c = idx % THUMB_COLS
                cell.grid(row=r, column=c, padx=6, pady=6, sticky="n")

                img_label = tk.Label(cell, image=photo)
                img_label.pack()

                txt = tk.Label(
                    cell,
                    text=f"{file_name}\n비어있음={item['empty_prob']:.3f}\n픽됨={item['picked_prob']:.3f}",
                    justify="left",
                    font=("맑은 고딕", 8),
                    wraplength=140
                )
                txt.pack()
            except Exception as e:
                cell = tk.Frame(self.scroll_frame, bd=1, relief="solid", padx=5, pady=5)
                r = idx // THUMB_COLS
                c = idx % THUMB_COLS
                cell.grid(row=r, column=c, padx=6, pady=6, sticky="n")
                txt = tk.Label(cell, text=f"{file_name}\n미리보기 실패\n{e}", font=("맑은 고딕", 8))
                txt.pack()

    def 삭제(self):
        self.결정 = "삭제"
        self.window.destroy()

    def 유지(self):
        self.결정 = "유지"
        self.window.destroy()


class 챔피언분류기UI:
    def __init__(self, root):
        self.root = root
        self.root.title("챔피언 분류기")
        self.root.geometry("1100x850")

        self.상태모델 = self.상태모델_준비()
        self.영한맵 = self.맵_불러오기()  # 영어 -> 한국어
        self.한영맵 = {kor: eng for eng, kor in self.영한맵.items()}  # 한국어 -> 영어
        self.한글이름목록 = sorted(self.한영맵.keys())

        self.삭제된개수 = 0
        self.비어있음후보목록 = []
        self.파일목록 = self.이미지목록_불러오기_및_비픽분리()
        self.비어있음_일괄확인_및_삭제()

        self.현재인덱스 = 0
        self.tk이미지 = None

        self.UI_만들기()

        if not self.파일목록:
            messagebox.showinfo(
                "안내",
                f"표시할 픽 이미지가 없습니다.\n삭제된 비어있음 이미지 수: {self.삭제된개수}"
            )
        else:
            self.현재이미지_표시()

    def 상태모델_준비(self):
        if not os.path.exists(STATE_MODEL_PATH):
            messagebox.showerror("오류", f"상태 모델 파일 없음:\n{STATE_MODEL_PATH}")
            self.root.destroy()
            raise SystemExit
        return 상태모델_불러오기()

    def 맵_불러오기(self):
        if not os.path.exists(MAP_PATH):
            messagebox.showerror("오류", f"맵 파일 없음:\n{MAP_PATH}")
            self.root.destroy()
            raise SystemExit

        with open(MAP_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    def 이미지목록_불러오기_및_비픽분리(self):
        if not os.path.exists(SOURCE_DIR):
            os.makedirs(SOURCE_DIR, exist_ok=True)
            return []

        전체파일 = []
        for name in os.listdir(SOURCE_DIR):
            if name.lower().endswith(IMAGE_EXTS):
                전체파일.append(os.path.join(SOURCE_DIR, name))
        전체파일.sort()

        남길파일 = []

        for path in 전체파일:
            try:
                픽됨, 비어있음확률, 픽됨확률 = 픽됨_예측(self.상태모델, path)

                if 픽됨:
                    남길파일.append(path)
                else:
                    self.비어있음후보목록.append({
                        "path": path,
                        "empty_prob": 비어있음확률,
                        "picked_prob": 픽됨확률
                    })
            except Exception as e:
                print(f"[예측 실패] {os.path.basename(path)} | {e}")

        return 남길파일

    def 비어있음_일괄확인_및_삭제(self):
        if not self.비어있음후보목록:
            return

        확인창 = 비어있음확인창(self.root, self.비어있음후보목록)
        self.root.wait_window(확인창.window)

        if 확인창.결정 == "삭제":
            for item in self.비어있음후보목록:
                path = item["path"]
                if os.path.exists(path):
                    try:
                        os.remove(path)
                        self.삭제된개수 += 1
                        print(
                            f"[삭제] {os.path.basename(path)} | "
                            f"비어있음={item['empty_prob']:.4f}, 픽됨={item['picked_prob']:.4f}"
                        )
                    except Exception as e:
                        print(f"[삭제 실패] {os.path.basename(path)} | {e}")
        else:
            print("[안내] 비어있음 이미지 삭제 안 함")

    def UI_만들기(self):
        상단프레임 = tk.Frame(self.root)
        상단프레임.pack(fill="x", padx=10, pady=10)

        self.상태라벨 = tk.Label(
            상단프레임,
            text="대기 중",
            font=("맑은 고딕", 12, "bold"),
            anchor="w"
        )
        self.상태라벨.pack(fill="x")

        본문프레임 = tk.Frame(self.root)
        본문프레임.pack(fill="both", expand=True, padx=10, pady=10)

        # 왼쪽 이미지 영역
        이미지프레임 = tk.Frame(본문프레임)
        이미지프레임.pack(side="left", fill="both", expand=True)

        self.파일명라벨 = tk.Label(
            이미지프레임,
            text="파일명",
            font=("맑은 고딕", 11, "bold")
        )
        self.파일명라벨.pack(pady=(0, 10))

        self.이미지라벨 = tk.Label(
            이미지프레임,
            text="이미지 없음",
            bg="#222222",
            fg="white",
            width=80,
            height=40
        )
        self.이미지라벨.pack(fill="both", expand=True)

        # 오른쪽 선택 영역
        우측프레임 = tk.Frame(본문프레임, width=320)
        우측프레임.pack(side="right", fill="y", padx=(15, 0))
        우측프레임.pack_propagate(False)

        설명라벨 = tk.Label(
            우측프레임,
            text="챔피언 선택",
            font=("맑은 고딕", 12, "bold")
        )
        설명라벨.pack(anchor="w", pady=(0, 8))

        self.검색변수 = tk.StringVar()
        self.검색변수.trace_add("write", self.리스트필터)

        검색엔트리 = tk.Entry(
            우측프레임,
            textvariable=self.검색변수,
            font=("맑은 고딕", 11)
        )
        검색엔트리.pack(fill="x", pady=(0, 8))
        검색엔트리.focus()

        리스트프레임 = tk.Frame(우측프레임)
        리스트프레임.pack(fill="both", expand=True)

        스크롤바 = tk.Scrollbar(리스트프레임)
        스크롤바.pack(side="right", fill="y")

        self.리스트박스 = tk.Listbox(
            리스트프레임,
            font=("맑은 고딕", 11),
            yscrollcommand=스크롤바.set,
            exportselection=False
        )
        self.리스트박스.pack(side="left", fill="both", expand=True)
        스크롤바.config(command=self.리스트박스.yview)

        for 이름 in self.한글이름목록:
            self.리스트박스.insert("end", 이름)

        버튼프레임 = tk.Frame(우측프레임)
        버튼프레임.pack(fill="x", pady=(10, 0))

        이동버튼 = tk.Button(
            버튼프레임,
            text="선택한 챔피언으로 이동",
            command=self.선택이동,
            font=("맑은 고딕", 10, "bold"),
            bg="#4CAF50",
            fg="white"
        )
        이동버튼.pack(fill="x", pady=(0, 8))

        건너뛰기버튼 = tk.Button(
            버튼프레임,
            text="건너뛰기",
            command=self.건너뛰기,
            font=("맑은 고딕", 10)
        )
        건너뛰기버튼.pack(fill="x", pady=(0, 8))

        이전버튼 = tk.Button(
            버튼프레임,
            text="이전 이미지",
            command=self.이전이미지,
            font=("맑은 고딕", 10)
        )
        이전버튼.pack(fill="x")

        안내라벨 = tk.Label(
            우측프레임,
            text=f"목록은 한국어 표시\n선택하면 영어 폴더로 이동\n비어있음은 먼저 전부 보여준 뒤 일괄 삭제 ({self.삭제된개수}개 삭제)",
            justify="left",
            fg="gray30",
            font=("맑은 고딕", 9)
        )
        안내라벨.pack(anchor="w", pady=(10, 0))

        self.리스트박스.bind("<Double-Button-1>", lambda e: self.선택이동())
        self.root.bind("<Return>", lambda e: self.선택이동())
        self.root.bind("<Right>", lambda e: self.건너뛰기())
        self.root.bind("<Left>", lambda e: self.이전이미지())

    def 리스트필터(self, *args):
        검색어 = self.검색변수.get().strip().lower()

        self.리스트박스.delete(0, "end")
        for 이름 in self.한글이름목록:
            if 검색어 in 이름.lower():
                self.리스트박스.insert("end", 이름)

    def 현재이미지_표시(self):
        if not self.파일목록:
            self.상태라벨.config(
                text=f"표시할 픽 이미지가 없습니다. 삭제된 비어있음 이미지: {self.삭제된개수}개"
            )
            self.파일명라벨.config(text="완료")
            self.이미지라벨.config(image="", text="모든 이미지 처리 완료")
            return

        if self.현재인덱스 < 0:
            self.현재인덱스 = 0
        if self.현재인덱스 >= len(self.파일목록):
            self.현재인덱스 = len(self.파일목록) - 1

        이미지경로 = self.파일목록[self.현재인덱스]
        파일명 = os.path.basename(이미지경로)

        self.상태라벨.config(
            text=f"진행: {self.현재인덱스 + 1} / {len(self.파일목록)} | 삭제된 비어있음: {self.삭제된개수}개"
        )
        self.파일명라벨.config(text=파일명)

        pil = Image.open(이미지경로).convert("RGB")
        w, h = pil.size

        배율 = min(MAX_W / w, MAX_H / h, 1.0)
        새크기 = (int(w * 배율), int(h * 배율))
        pil = pil.resize(새크기)

        self.tk이미지 = ImageTk.PhotoImage(pil)
        self.이미지라벨.config(image=self.tk이미지, text="")

    def 선택가져오기(self):
        선택 = self.리스트박스.curselection()
        if not 선택:
            return None
        return self.리스트박스.get(선택[0])

    def 선택이동(self):
        if not self.파일목록:
            return

        한글이름 = self.선택가져오기()
        if 한글이름 is None:
            messagebox.showwarning("안내", "챔피언을 먼저 선택하세요.")
            return

        영어이름 = self.한영맵.get(한글이름)
        if 영어이름 is None:
            messagebox.showerror("오류", f"맵에 없는 챔피언입니다:\n{한글이름}")
            return

        원본경로 = self.파일목록[self.현재인덱스]
        파일명 = os.path.basename(원본경로)

        대상폴더 = os.path.join(TARGET_DIR, 영어이름)
        os.makedirs(대상폴더, exist_ok=True)

        대상경로 = os.path.join(대상폴더, 파일명)

        shutil.move(원본경로, 대상경로)

        del self.파일목록[self.현재인덱스]

        if self.현재인덱스 >= len(self.파일목록) and self.현재인덱스 > 0:
            self.현재인덱스 -= 1

        self.현재이미지_표시()

    def 건너뛰기(self):
        if not self.파일목록:
            return

        self.현재인덱스 += 1
        if self.현재인덱스 >= len(self.파일목록):
            self.현재인덱스 = 0
        self.현재이미지_표시()

    def 이전이미지(self):
        if not self.파일목록:
            return

        self.현재인덱스 -= 1
        if self.현재인덱스 < 0:
            self.현재인덱스 = len(self.파일목록) - 1
        self.현재이미지_표시()


def main():
    root = tk.Tk()
    챔피언분류기UI(root)
    root.mainloop()


if __name__ == "__main__":
    main()