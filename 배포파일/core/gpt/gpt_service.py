from core.gpt.prompt_builder import (
    normalize_lane_ui_to_gpt,
    build_blind_pick_prompt,
    build_counter_pick_prompt,
    build_fixed_pick_prompt,
    build_ingame_prompt,
)
from core.gpt.response_parser import (
    parse_pick_result,
    parse_build_result,
    parse_ingame_tips,
)
from gpt.chatgpt_web_bridge import ask_chatgpt


def ask_blind_pick(lane_ko: str):
    lane = normalize_lane_ui_to_gpt(lane_ko)
    prompt = build_blind_pick_prompt(lane)
    answer = ask_chatgpt(prompt)
    return parse_pick_result(answer)


def ask_counter_pick(enemy_champ_en: str, lane_ko: str):
    lane = normalize_lane_ui_to_gpt(lane_ko)
    prompt = build_counter_pick_prompt(enemy_champ_en, lane)
    answer = ask_chatgpt(prompt)
    return parse_pick_result(answer)


def ask_build(my_champ_en: str, enemy_champ_en: str, lane_ko: str):
    lane = normalize_lane_ui_to_gpt(lane_ko)
    prompt = build_fixed_pick_prompt(my_champ_en, enemy_champ_en, lane)
    answer = ask_chatgpt(prompt)
    return parse_build_result(answer)


def ask_ingame_coach(game_time: str, team_kills: str, enemy_kills: str, kda: str):
    prompt = build_ingame_prompt(game_time, team_kills, enemy_kills, kda)
    answer = ask_chatgpt(prompt)
    return parse_ingame_tips(answer)