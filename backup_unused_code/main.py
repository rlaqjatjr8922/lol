import cv2
from config import ALL_SLOTS, COMPONENT_SLOTS_LV2
from matcher import load_refs, match_icon

img = cv2.imread("screenshots/test1.png")

refs = load_refs()

mid_items = []
for (x1, y1, x2, y2) in COMPONENT_SLOTS_LV2:
    crop = img[y1:y2, x1:x2]
    name, score = match_icon(crop, refs)
    if score > 0.6:
        mid_items.append(name)

all_items = []
for (x1, y1, x2, y2) in ALL_SLOTS:
    crop = img[y1:y2, x1:x2]
    name, score = match_icon(crop, refs)
    if score > 0.6:
        all_items.append(name)

if len(mid_items) == 1:
    final = all_items
else:
    final = mid_items

print("결과:", final)
