import os
import torch
from PIL import Image
from torchvision import transforms, models
import torch.nn as nn


MODEL_PATH = r"C:\Users\gimbe\OneDrive\Desktop\lol_project\dataset\state_classifier.pt"
TEST_DIR = r"C:\Users\gimbe\OneDrive\Desktop\lol_project\dataset\test"

IMAGE_SIZE = 96
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp", ".bmp")


def 모델_불러오기():
    model = models.resnet18(weights=None)
    model.fc = nn.Linear(model.fc.in_features, 2)
    model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE))
    model = model.to(DEVICE)
    model.eval()
    return model


def 하나_예측(model, image_path, tf, class_names):
    image = Image.open(image_path).convert("RGB")
    x = tf(image).unsqueeze(0).to(DEVICE)

    with torch.no_grad():
        out = model(x)
        probs = torch.softmax(out, dim=1)[0]
        pred = out.argmax(dim=1).item()

    return class_names[pred], float(probs[0]), float(probs[1])


def main():
    if not os.path.exists(MODEL_PATH):
        print("[오류] 모델 파일 없음:", MODEL_PATH)
        return

    if not os.path.exists(TEST_DIR):
        print("[오류] test 폴더 없음:", TEST_DIR)
        return

    tf = transforms.Compose([
        transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
        transforms.ToTensor(),
    ])

    class_names = ["비어있음", "픽됨"]
    model = 모델_불러오기()

    files = []
    for name in os.listdir(TEST_DIR):
        if name.lower().endswith(IMAGE_EXTS):
            files.append(os.path.join(TEST_DIR, name))

    files.sort()

    if not files:
        print("[안내] test 폴더에 이미지가 없습니다.")
        return

    print("=== 예측 시작 ===")
    for path in files:
        pred, p_empty, p_picked = 하나_예측(model, path, tf, class_names)
        print(f"{os.path.basename(path)}")
        print(f"  예측 결과: {pred}")
        print(f"  비어있음 확률 = {p_empty:.4f}")
        print(f"  픽됨 확률 = {p_picked:.4f}")
        print()

    print("=== 완료 ===")


if __name__ == "__main__":
    main()