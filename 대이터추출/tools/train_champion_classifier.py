import os
import random
from PIL import Image

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset, random_split
from torchvision import transforms, models


DATASET_DIR = r"C:\Users\gimbe\OneDrive\Desktop\lol_project\dataset\champion"
MODEL_OUTPUT = r"C:\Users\gimbe\OneDrive\Desktop\lol_project\dataset\champion_classifier.pt"

IMAGE_SIZE = 96
BATCH_SIZE = 16
EPOCHS = 12
LR = 1e-4
VAL_RATIO = 0.2
SEED = 42

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp", ".bmp")


def 시드_고정(seed: int):
    random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


class 챔피언데이터셋(Dataset):
    def __init__(self, root_dir, transform=None):
        self.root_dir = root_dir
        self.transform = transform
        self.samples = []
        self.class_names = []

        for class_name in sorted(os.listdir(root_dir)):
            class_path = os.path.join(root_dir, class_name)
            if not os.path.isdir(class_path):
                continue

            image_files = []
            for file_name in os.listdir(class_path):
                if file_name.lower().endswith(IMAGE_EXTS):
                    image_files.append(os.path.join(class_path, file_name))

            if len(image_files) == 0:
                continue

            class_index = len(self.class_names)
            self.class_names.append(class_name)

            for image_path in image_files:
                self.samples.append((image_path, class_index))

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        image_path, label = self.samples[idx]
        image = Image.open(image_path).convert("RGB")

        if self.transform is not None:
            image = self.transform(image)

        return image, label


def 메인():
    시드_고정(SEED)

    if not os.path.exists(DATASET_DIR):
        print("[오류] 데이터셋 폴더 없음:", DATASET_DIR)
        return

    transform = transforms.Compose([
        transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
        transforms.ColorJitter(brightness=0.1, contrast=0.1),
        transforms.ToTensor(),
    ])

    dataset = 챔피언데이터셋(DATASET_DIR, transform=transform)

    if len(dataset) == 0:
        print("[오류] 이미지가 들어있는 챔피언 폴더가 없습니다.")
        return

    print("사용 클래스 목록:", dataset.class_names)
    print("전체 이미지 수:", len(dataset))

    if len(dataset.class_names) < 2:
        print("[오류] 최소 2개 이상의 챔피언 클래스가 필요합니다.")
        return

    val_size = max(1, int(len(dataset) * VAL_RATIO))
    train_size = len(dataset) - val_size

    if train_size <= 0:
        print("[오류] 학습 데이터가 너무 적습니다.")
        return

    train_set, val_set = random_split(
        dataset,
        [train_size, val_size],
        generator=torch.Generator().manual_seed(SEED)
    )

    train_loader = DataLoader(train_set, batch_size=BATCH_SIZE, shuffle=True)
    val_loader = DataLoader(val_set, batch_size=BATCH_SIZE)

    model = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
    model.fc = nn.Linear(model.fc.in_features, len(dataset.class_names))
    model = model.to(DEVICE)

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=LR)

    최고_정확도 = 0.0

    for epoch in range(EPOCHS):
        model.train()
        train_loss = 0.0
        train_correct = 0
        train_total = 0

        for imgs, labels in train_loader:
            imgs = imgs.to(DEVICE)
            labels = labels.to(DEVICE)

            optimizer.zero_grad()
            out = model(imgs)
            loss = criterion(out, labels)
            loss.backward()
            optimizer.step()

            train_loss += loss.item() * imgs.size(0)
            pred = out.argmax(1)
            train_correct += (pred == labels).sum().item()
            train_total += labels.size(0)

        train_loss /= max(1, train_total)
        train_acc = train_correct / max(1, train_total)

        model.eval()
        val_loss = 0.0
        val_correct = 0
        val_total = 0

        with torch.no_grad():
            for imgs, labels in val_loader:
                imgs = imgs.to(DEVICE)
                labels = labels.to(DEVICE)

                out = model(imgs)
                loss = criterion(out, labels)

                val_loss += loss.item() * imgs.size(0)
                pred = out.argmax(1)
                val_correct += (pred == labels).sum().item()
                val_total += labels.size(0)

        val_loss /= max(1, val_total)
        val_acc = val_correct / max(1, val_total)

        print(
            f"[{epoch+1}/{EPOCHS}] "
            f"학습손실={train_loss:.4f} 학습정확도={train_acc:.4f} "
            f"검증손실={val_loss:.4f} 검증정확도={val_acc:.4f}"
        )

        if val_acc > 최고_정확도:
            최고_정확도 = val_acc
            torch.save(
                {
                    "model_state_dict": model.state_dict(),
                    "class_names": dataset.class_names,
                    "image_size": IMAGE_SIZE,
                },
                MODEL_OUTPUT
            )
            print("[저장] 최고 성능 모델 저장:", MODEL_OUTPUT)

    print()
    print("=== 학습 완료 ===")
    print("최고 검증 정확도:", 최고_정확도)
    print("모델 경로:", MODEL_OUTPUT)


if __name__ == "__main__":
    메인()