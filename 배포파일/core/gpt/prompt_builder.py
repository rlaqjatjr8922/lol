def normalize_lane_ui_to_gpt(lane_text: str) -> str:
    mapping = {
        "탑": "top",
        "정글": "jungle",
        "미드": "mid",
        "원딜": "dragon",
        "서폿": "support",
    }
    return mapping.get((lane_text or "").strip(), "top")


def build_blind_pick_prompt(lane: str) -> str:
    return "\n".join([
        "Answer for Wild Rift only.",
        "Do not use PC League of Legends information.",
        "Assume latest Wild Rift meta.",
        "Recommend one safe blind-pick champion.",
        "Champion name must be in ENGLISH.",
        "Reason must be in KOREAN and VERY SHORT.",
        "",
        f"Lane: {lane}",
        "",
        "Output exactly in this format:",
        "Champion: ",
        "Reason: ",
    ])


def build_counter_pick_prompt(enemy_champ: str, lane: str) -> str:
    return "\n".join([
        "Answer for Wild Rift only.",
        "Do not use PC League of Legends information.",
        "Assume latest Wild Rift meta.",
        "Recommend one counter-pick champion.",
        "Champion name must be in ENGLISH.",
        "Reason must be in KOREAN and VERY SHORT.",
        "",
        f"Enemy champion: {enemy_champ}",
        f"Lane: {lane}",
        "",
        "Output exactly in this format:",
        "Champion: ",
        "Reason: ",
    ])


def build_fixed_pick_prompt(my_champ: str, enemy_champ: str, lane: str) -> str:
    return "\n".join([
        "Answer for Wild Rift only.",
        "Do not use PC League of Legends information.",
        "Assume latest Wild Rift meta.",

        "STRICT FORMAT.",
        "DO NOT CHANGE KEY NAMES.",

        "Use only real Wild Rift runes, spells, and items.",
        "Champion, rune, spell, and item names must be in ENGLISH.",
        "Description must be in KOREAN and VERY SHORT.",

        "",
        "IMPORTANT RULE FOR First Item:",
        "First Item must be either BOOTS or a FULL CORE ITEM.",
        "Do NOT output component items.",
        "Do NOT output partial items.",
        "If invalid, your answer is wrong.",

        "",
        "IMPORTANT RULE FOR Starting Item:",
        "Starting Item must be a 500 gold component item that builds into First Item.",
        "If multiple valid items exist, choose ONE best item only.",

        "",
        f"My champion: {my_champ}",
        f"Enemy champion: {enemy_champ}",
        f"Lane: {lane}",

        "",
        "Output exactly in this format:",
        "Keystone: ",
        "Primary Tree: ",
        "Rune1: ",
        "Rune2: ",
        "Rune3: ",
        "Secondary Tree: ",
        "Secondary Rune: ",
        "Spells: ",
        "Starting Item: ",
        "First Item: ",
        "Early Game Plan: ",
    ])


def build_ingame_prompt(game_time: str, team_kills: str, enemy_kills: str, kda: str) -> str:
    return "\n".join([
        "Answer for Wild Rift only.",
        "Give short Korean coaching tips.",
        "",
        f"Game time: {game_time}",
        f"Team kills: {team_kills}",
        f"Enemy kills: {enemy_kills}",
        f"My KDA: {kda}",
        "",
        "Output:",
        "Summary:",
        "Tip1:",
        "Tip2:",
        "Tip3:",
    ])
def build_ingame_prompt(game_time: str, team_kills: str, enemy_kills: str, kda: str) -> str:
    return "\n".join([
        "Answer for Wild Rift only.",
        "Give short Korean coaching tips.",
        "",
        f"Game time: {game_time}",
        f"Team kills: {team_kills}",
        f"Enemy kills: {enemy_kills}",
        f"My KDA: {kda}",
        "",
        "Output:",
        "Summary:",
        "Tip1:",
        "Tip2:",
        "Tip3:",
    ])