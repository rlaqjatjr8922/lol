from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SlotMatch:
    name: str = ""
    score: float = 0.0
    is_empty: bool = False


@dataclass
class DraftState:
    phase: str = "unknown"          # ban / pick / unknown
    current_team: Optional[str] = None   # team1 / team2
    my_team: Optional[str] = None        # team1 / team2
    is_my_turn: bool = False
    step_index: int = -1


@dataclass
class BanPickSnapshot:
    ally_bans: list[SlotMatch] = field(default_factory=list)
    enemy_bans: list[SlotMatch] = field(default_factory=list)
    ally_picks: list[SlotMatch] = field(default_factory=list)
    enemy_picks: list[SlotMatch] = field(default_factory=list)
    hover_pick: Optional[SlotMatch] = None
    state: DraftState = field(default_factory=DraftState)