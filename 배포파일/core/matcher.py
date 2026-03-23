import cv2
import os

def load_refs(folder="refs"):
    refs = {}
    for file in os.listdir(folder):
        if file.endswith(".png"):
            name = file.replace(".png", "")
            img = cv2.imread(os.path.join(folder, file))
            refs[name] = img
    return refs

def match_icon(crop, refs):
    best_name = "unknown"
    best_score = 0

    for name, ref in refs.items():
        ref_resized = cv2.resize(ref, (crop.shape[1], crop.shape[0]))
        result = cv2.matchTemplate(crop, ref_resized, cv2.TM_CCOEFF_NORMED)
        score = result.max()

        if score > best_score:
            best_score = score
            best_name = name

    return best_name, best_score
