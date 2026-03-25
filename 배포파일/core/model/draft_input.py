from dataclasses import dataclass


@dataclass
class DraftInput:
    pick_order: str = "선픽"
    lane: str = "탑"
    my_champ: str = ""
    enemy_champ: str = ""