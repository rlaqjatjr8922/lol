import pygame


def build_layout(screen_width, screen_height, right_panel_width, bottom_panel_height, stage_bar_height):
    left_width = screen_width - right_panel_width

    blue_rect = pygame.Rect(0, screen_height - bottom_panel_height, left_width, bottom_panel_height)
    red_rect = pygame.Rect(0, 0, left_width, screen_height - bottom_panel_height)
    stage_bar_rect = pygame.Rect(left_width, 0, right_panel_width, stage_bar_height)
    green_rect = pygame.Rect(left_width, stage_bar_height, right_panel_width, screen_height - stage_bar_height)

    return red_rect, blue_rect, stage_bar_rect, green_rect
