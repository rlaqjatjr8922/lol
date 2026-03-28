import os
import random

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, random_split
from torchvision import datasets, transforms, models

DATASET_DIR = r"C:\Users\gimbe\OneDrive\Desktop\lol_project\dataset\state"
MODEL_OUTPUT = r"C:\Users\gimbe\OneDrive\Desktop\lol_project\dataset\state_classifier.pt"

IMAGE_SIZE = 96
BATCH_SIZE = 16   # ↓ 데이터 적어서 줄임
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

    transform = transforms.Compose([
        transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
        transforms.ColorJitter(brightness=0.1, contrast=0.1),
        transforms.ToTensor(),
    ])

    dataset = datasets.ImageFolder(DATASET_DIR, transform=transform)

    if len(dataset) == 0:
        print("[오류] 이미지 없음")
        return

    print("클래스:", dataset.classes)

    val_size = int(len(dataset) * VAL_RATIO)
    train_size = len(dataset) - val_size

    train_set, val_set = random_split(dataset, [train_size, val_size])

    train_loader = DataLoader(train_set, batch_size=BATCH_SIZE, shuffle=True)
    val_loader = DataLoader(val_set, batch_size=BATCH_SIZE)

    model = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
    model.fc = nn.Linear(model.fc.in_features, 2)
    model = model.to(DEVICE)

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=LR)

    best_acc = 0

    for epoch in range(EPOCHS):
        model.train()
        correct = 0
        total = 0

        for imgs, labels in train_loader:
            imgs, labels = imgs.to(DEVICE), labels.to(DEVICE)

            optimizer.zero_grad()
            out = model(imgs)
            loss = criterion(out, labels)
            loss.backward()
            optimizer.step()

            pred = out.argmax(1)
            correct += (pred == labels).sum().item()
            total += labels.size(0)

        train_acc = correct / total

        model.eval()
        correct = 0
        total = 0

        with torch.no_grad():
            for imgs, labels in val_loader:
                imgs, labels = imgs.to(DEVICE), labels.to(DEVICE)
                out = model(imgs)
                pred = out.argmax(1)
                correct += (pred == labels).sum().item()
                total += labels.size(0)

        val_acc = correct / total

        print(f"[{epoch+1}] train={train_acc:.3f} val={val_acc:.3f}")

        if val_acc > best_acc:
            best_acc = val_acc
            torch.save(model.state_dict(), MODEL_OUTPUT)
            print("모델 저장됨")

    print("완료, 최고 정확도:", best_acc)


if __name__ == "__main__":
    main()