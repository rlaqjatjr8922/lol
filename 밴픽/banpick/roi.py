from .config import BASE_WIDTH, BASE_HEIGHT

ROI_CONFIG = {
    "ally_bans": [
        (113, 19, 71, 71),
        (199, 19, 71, 71),
        (285, 19, 71, 71),
        (372, 19, 71, 71),
        (459, 19, 71, 71),
    ],
    "enemy_bans": [
        (1811, 19, 71, 71),
        (1725, 19, 71, 71),
        (1639, 19, 71, 71),
        (1552, 19, 71, 71),
        (1466, 19, 71, 71),
    ],
    "ally_picks": [
        (113, 109, 71, 71),
        (199, 109, 71, 71),
        (285, 109, 71, 71),
        (372, 109, 71, 71),
        (459, 109, 71, 71),
    ],
    "enemy_picks": [
        (1811, 109, 71, 71),
        (1725, 109, 71, 71),
        (1639, 109, 71, 71),
        (1552, 109, 71, 71),
        (1466, 109, 71, 71),
    ],
    "hover_pick": (286, 245, 116, 116),

    # 예시
    "turn_lights_team1": [
        (620, 120, 20, 20),
        (620, 180, 20, 20),
        (620, 240, 20, 20),
        (620, 300, 20, 20),
        (620, 360, 20, 20),
    ],
    "turn_lights_team2": [
        (1408, 120, 20, 20),
        (1408, 180, 20, 20),
        (1408, 240, 20, 20),
        (1408, 300, 20, 20),
        (1408, 360, 20, 20),
    ],
}


def scale_box(box, w, h, base_w=BASE_WIDTH, base_h=BASE_HEIGHT):
    x, y, bw, bh = box
    sx = w / base_w
    sy = h / base_h
    return (
        int(round(x * sx)),
        int(round(y * sy)),
        int(round(bw * sx)),
        int(round(bh * sy)),
    )


def get_scaled_rois(image_shape):
    h, w = image_shape[:2]
    out = {}
    for key, value in ROI_CONFIG.items():
        if isinstance(value, list):
            out[key] = [scale_box(v, w, h) for v in value]
        else:
            out[key] = scale_box(value, w, h)
    return out