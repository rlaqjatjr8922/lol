from dataclasses import dataclass


@dataclass
class IngameState:
    game_time: str = "?"
    team_kills: str = "?"
    enemy_kills: str = "?"
    my_kills: str = "?"
    my_deaths: str = "?"
    my_assists: str = "?"
    raw_time_text: str = ""
    raw_score_text: str = ""
    raw_kda_text: str = ""
    last_error: str = ""