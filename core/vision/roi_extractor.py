class ROIExtractor:
    def extract(self, frame, roi_box):
        if frame is None or roi_box is None:
            return None

        try:
            x1_ratio, y1_ratio, x2_ratio, y2_ratio = roi_box
        except Exception:
            return None

        h, w = frame.shape[:2]

        x1 = int(w * x1_ratio)
        y1 = int(h * y1_ratio)

        # support both [x1, y1, x2, y2] and [x, y, width, height]
        if x2_ratio <= x1_ratio or y2_ratio <= y1_ratio:
            x2 = int(w * min(1.0, x1_ratio + x2_ratio))
            y2 = int(h * min(1.0, y1_ratio + y2_ratio))
        else:
            x2 = int(w * x2_ratio)
            y2 = int(h * y2_ratio)

        x1 = max(0, min(w, x1))
        x2 = max(0, min(w, x2))
        y1 = max(0, min(h, y1))
        y2 = max(0, min(h, y2))

        if x2 <= x1 or y2 <= y1:
            return None

        roi = frame[y1:y2, x1:x2]

        if roi.size == 0:
            return None

        return roi.copy()