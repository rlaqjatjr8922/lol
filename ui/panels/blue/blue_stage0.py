import pygame


def draw_blue_stage0(screen, rect):
    title_font = pygame.font.SysFont("malgungothic", 34, bold=True)
    sub_font = pygame.font.SysFont("malgungothic", 20)
    title_text = title_font.render("라인 감지중...", True, (255, 255, 255))
    sub_text = sub_font.render("게임 화면을 확인하고 있습니다", True, (230, 230, 230))
    title_rect = title_text.get_rect(center=(rect.centerx, rect.centery - 20))
    sub_rect = sub_text.get_rect(center=(rect.centerx, rect.centery + 18))
    screen.blit(title_text, title_rect)
    screen.blit(sub_text, sub_rect)
