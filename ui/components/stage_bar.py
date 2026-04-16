import pygame


def draw_stage_bar(screen, x, y, width, height, current_stage):
    bar_rect = pygame.Rect(x, y, width, height)

    pygame.draw.rect(screen, (35, 35, 35), bar_rect)
    pygame.draw.rect(screen, (0, 0, 0), bar_rect, 3)

    button_count = 5
    gap = 8

    # width 기준 자동 계산
    button_width = (width - (button_count + 1) * gap) // button_count
    button_height = int(height * 0.6)

    # 너무 작아지는 거 방지
    if button_width < 40:
        button_width = 40

    if button_height < 28:
        button_height = 28

    total_width = button_count * button_width + (button_count - 1) * gap
    start_x = x + (width - total_width) // 2
    start_y = y + (height - button_height) // 2

    font_size = max(18, int(button_height * 0.55))
    font = pygame.font.SysFont("malgungothic", font_size, bold=True)

    buttons = []

    for i in range(button_count):
        bx = start_x + i * (button_width + gap)
        by = start_y

        rect = pygame.Rect(bx, by, button_width, button_height)
        buttons.append(rect)

        if i == current_stage:
            color = (70, 130, 220)
        else:
            color = (220, 220, 220)

        pygame.draw.rect(screen, color, rect, border_radius=8)
        pygame.draw.rect(screen, (0, 0, 0), rect, 2, border_radius=8)

        text = font.render(str(i), True, (0, 0, 0))
        text_rect = text.get_rect(center=rect.center)
        screen.blit(text, text_rect)

    return buttons