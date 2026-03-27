import os
import random
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, random_split
from torchvision import datasets, transforms, models


# =========================
# 경로
# =========================
DATASET_DIR = r"C:\Users\gimbe\OneDrive\Desktop\lol_project\dataset\state"
MODEL_OUTPUT = r"C:\Users\gimbe\OneDrive\Desktop\lol_project\dataset\state_classifier.pt"

# 폴더 구조 예시
# dataset/state/
# ├─ empty/
# └─ picked/


# =========================
# 설정
# =========================
IMAGE_SIZE = 96
BATCH_SIZE = 32
EPOCHS = 10
LR = 1e-4
VAL_RATIO = 0.2
SEED = 42

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


def set_seed(seed: int):
    random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def main():
    set_seed(SEED)

    if not os.path.exists(DATASET_DIR):
        print("[오류] 데이터셋 폴더 없음:", DATASET_DIR)
        return

    train_tf = transforms.Compose([
        transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
        transforms.ColorJitter(brightness=0.12, contrast=0.12),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5]),
    ])

    full_dataset = datasets.ImageFolder(DATASET_DIR, transform=train_tf)

    if len(full_dataset) == 0:
        print("[오류] 이미지가 없습니다:", DATASET_DIR)
        return

    class_names = full_dataset.classes
    print("클래스:", class_names)

    total_len = len(full_dataset)
    val_len = max(1, int(total_len * VAL_RATIO))
    train_len = total_len - val_len

    train_set, val_set = random_split(
        full_dataset,
        [train_len, val_len],
        generator=torch.Generator().manual_seed(SEED)
    )

    train_loader = DataLoader(train_set, batch_size=BATCH_SIZE, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_set, batch_size=BATCH_SIZE, shuffle=False, num_workers=0)

    model = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
    in_features = model.fc.in_features
    model.fc = nn.Linear(in_features, len(class_names))
    model = model.to(DEVICE)

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=LR)

    best_acc = 0.0

    for epoch in range(1, EPOCHS + 1):
        model.train()
        train_loss = 0.0
        train_correct = 0
        train_total = 0

        for images, labels in train_loader:
            images = images.to(DEVICE)
            labels = labels.to(DEVICE)

            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            train_loss += loss.item() * images.size(0)
            preds = outputs.argmax(dim=1)
            train_correct += (preds == labels).sum().item()
            train_total += labels.size(0)

        train_loss /= max(1, train_total)
        train_acc = train_correct / max(1, train_total)

        model.eval()
        val_loss = 0.0
        val_correct = 0
        val_total = 0

        with torch.no_grad():
            for images, labels in val_loader:
                images = images.to(DEVICE)
                labels = labels.to(DEVICE)

                outputs = model(images)
                loss = criterion(outputs, labels)

                val_loss += loss.item() * images.size(0)
                preds = outputs.argmax(dim=1)
                val_correct += (preds == labels).sum().item()
                val_total += labels.size(0)

        val_loss /= max(1, val_total)
        val_acc = val_correct / max(1, val_total)

        print(
            f"[{epoch}/{EPOCHS}] "
            f"train_loss={train_loss:.4f} train_acc={train_acc:.4f} "
            f"val_loss={val_loss:.4f} val_acc={val_acc:.4f}"
        )

        if val_acc > best_acc:
            best_acc = val_acc
            torch.save({
                "model_state_dict": model.state_dict(),
                "class_names": class_names,
                "image_size": IMAGE_SIZE,
            }, MODEL_OUTPUT)
            print(f"[저장] 최고 성능 모델 저장: {MODEL_OUTPUT}")

    print()
    print("=== 학습 완료 ===")
    print("best_val_acc =", best_acc)
    print("model_path =", MODEL_OUTPUT)


if __name__ == "__main__":
    main()