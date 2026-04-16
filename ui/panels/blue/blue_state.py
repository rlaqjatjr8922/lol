class BlueState:
    def __init__(self):
        self.scroll_x = 0
        self.scroll_speed = 50

        self.left_ap_ratio = 0.35
        self.right_ap_ratio = 0.60

        self.ally_stats = {
            "cc": 7,
            "early": 6,
            "late": 8,
            "damage": 7,
            "tank": 4,
        }

        self.enemy_stats = {
            "cc": 5,
            "early": 8,
            "late": 6,
            "damage": 9,
            "tank": 3,
        }

        self.progress = 0.0
        self.speed = 0.08
        self.is_animating = False

        self.mode = "original"
        self.animation_target_mode = "original"

        self.content_width = 1000

        # 가로 스크롤바 드래그 상태
        self.is_dragging_scrollbar = False
        self.scrollbar_drag_offset_x = 0