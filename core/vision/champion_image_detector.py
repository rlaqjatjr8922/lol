from pathlib import Path
import cv2


class ChampionImageDetector:
    def __init__(self):
        self.last_debug = None

    def detect(self, roi, stage_config):  # 🔥 여기 변경
        self.last_debug = {
            "roi_steps": [],
            "matched_template_steps": [],
            "scores": [],
            "best_name": None,
            "best_score": -1.0,
        }

        if roi is None:
            return None

        template_dir = Path(stage_config["template_dir"])
        threshold = stage_config["threshold"]

        self.last_debug["roi_steps"].append(("original", roi.copy()))

        roi_resized = cv2.resize(roi, (64, 64))
        self.last_debug["roi_steps"].append(("resized", roi_resized.copy()))

        roi_gray = cv2.cvtColor(roi_resized, cv2.COLOR_BGR2GRAY)
        self.last_debug["roi_steps"].append(("gray", roi_gray.copy()))

        best_name = None
        best_score = -1.0
        best_template = None

        for template_file in sorted(template_dir.glob("*.png")):
            template_img = cv2.imread(str(template_file))
            if template_img is None:
                continue

            template_resized = cv2.resize(template_img, (64, 64))
            template_gray = cv2.cvtColor(template_resized, cv2.COLOR_BGR2GRAY)

            score = cv2.matchTemplate(
                roi_gray,
                template_gray,
                cv2.TM_CCOEFF_NORMED
            )[0][0]

            score = float(score)
            self.last_debug["scores"].append((template_file.stem, score))

            if score > best_score:
                best_score = score
                best_name = template_file.stem
                best_template = template_img

        self.last_debug["best_name"] = best_name
        self.last_debug["best_score"] = best_score

        if best_template is not None:
            self.last_debug["matched_template_steps"].append(
                ("best_template", best_template.copy())
            )

        print(f"[ChampionImageDetector] best_name = {best_name}")
        print(f"[ChampionImageDetector] best_score = {best_score}")

        if best_score >= threshold:
            return best_name

        return "unknown"