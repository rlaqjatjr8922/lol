from .blue_anim import ease_in_out
from .team_block import draw_team_block
from .center_graph import draw_center_pentagon


def draw_blue_content(surface, area_w, area_h, stage, state):
    left_team_w = int(area_w * 0.42)
    center_w = int(area_w * 0.16)
    right_team_w = area_w - left_team_w - center_w

    left_x = 0
    center_x = left_x + left_team_w
    right_x = center_x + center_w

    draw_progress = ease_in_out(state.progress) if state.is_animating else state.progress
    highlight_big_count = 2 if stage == 3 else 0

    draw_team_block(surface=surface, team_x=left_x, team_y=0, team_w=left_team_w, team_h=area_h, ap_ratio=state.left_ap_ratio, reverse_top=False, progress=draw_progress, is_animating=state.is_animating, mode=state.mode, highlight_big_count=highlight_big_count)
    draw_team_block(surface=surface, team_x=right_x, team_y=0, team_w=right_team_w, team_h=area_h, ap_ratio=state.right_ap_ratio, reverse_top=True, progress=draw_progress, is_animating=state.is_animating, mode=state.mode, highlight_big_count=highlight_big_count)
    draw_center_pentagon(surface=surface, center_x=center_x, y=0, center_w=center_w, h=area_h, ally_stats=state.ally_stats, enemy_stats=state.enemy_stats)
