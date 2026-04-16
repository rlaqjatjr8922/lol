import math
import pygame


def draw_center_pentagon(surface, center_x, y, center_w, h, ally_stats, enemy_stats):
    cx = center_x + center_w // 2
    cy = y + h // 2

    outer_radius = int(min(center_w, h) * 0.33)
    levels = 4

    labels = ["CC", "초반", "후반", "딜", "탱"]

    angles = [
        -math.pi / 2,
        -math.pi / 2 + (2 * math.pi / 5),
        -math.pi / 2 + (4 * math.pi / 5),
        -math.pi / 2 + (6 * math.pi / 5),
        -math.pi / 2 + (8 * math.pi / 5),
    ]

    for level in range(1, levels + 1):
        r = outer_radius * (level / levels)
        points = []
        for angle in angles:
            px = cx + math.cos(angle) * r
            py = cy + math.sin(angle) * r
            points.append((px, py))
        color = (220, 220, 220) if level == levels else (180, 180, 180)
        pygame.draw.polygon(surface, color, points, 1)

    for angle in angles:
        px = cx + math.cos(angle) * outer_radius
        py = cy + math.sin(angle) * outer_radius
        pygame.draw.line(surface, (170, 170, 170), (cx, cy), (px, py), 1)

    outer_points = []
    for angle in angles:
        px = cx + math.cos(angle) * outer_radius
        py = cy + math.sin(angle) * outer_radius
        outer_points.append((px, py))
    pygame.draw.polygon(surface, (240, 240, 240), outer_points, 2)

    label_font = pygame.font.SysFont("malgungothic", 16)
    for label, angle in zip(labels, angles):
        lx = cx + math.cos(angle) * (outer_radius + 22)
        ly = cy + math.sin(angle) * (outer_radius + 22)
        text = label_font.render(label, True, (255, 255, 255))
        text_rect = text.get_rect(center=(int(lx), int(ly)))
        surface.blit(text, text_rect)

    ally_values = [
        ally_stats["cc"],
        ally_stats["early"],
        ally_stats["late"],
        ally_stats["damage"],
        ally_stats["tank"],
    ]
    ally_points = build_stat_polygon(cx, cy, outer_radius, angles, ally_values)

    enemy_values = [
        enemy_stats["cc"],
        enemy_stats["early"],
        enemy_stats["late"],
        enemy_stats["damage"],
        enemy_stats["tank"],
    ]
    enemy_points = build_stat_polygon(cx, cy, outer_radius, angles, enemy_values)

    pygame.draw.polygon(surface, (255, 90, 90), enemy_points)
    pygame.draw.polygon(surface, (140, 20, 20), enemy_points, 2)

    pygame.draw.polygon(surface, (80, 140, 255), ally_points)
    pygame.draw.polygon(surface, (20, 40, 120), ally_points, 2)

    for px, py in enemy_points:
        pygame.draw.circle(surface, (255, 220, 220), (int(px), int(py)), 4)
        pygame.draw.circle(surface, (120, 20, 20), (int(px), int(py)), 1)

    for px, py in ally_points:
        pygame.draw.circle(surface, (220, 235, 255), (int(px), int(py)), 4)
        pygame.draw.circle(surface, (20, 40, 120), (int(px), int(py)), 1)

    pygame.draw.circle(surface, (240, 240, 240), (cx, cy), 4)

    legend_font = pygame.font.SysFont("malgungothic", 14)

    ally_legend_rect = pygame.Rect(cx - 48, cy + outer_radius + 28, 16, 16)
    enemy_legend_rect = pygame.Rect(cx + 18, cy + outer_radius + 28, 16, 16)

    pygame.draw.rect(surface, (80, 140, 255), ally_legend_rect)
    pygame.draw.rect(surface, (20, 40, 120), ally_legend_rect, 1)
    ally_text = legend_font.render("아군", True, (255, 255, 255))
    surface.blit(ally_text, (ally_legend_rect.right + 6, ally_legend_rect.y - 1))

    pygame.draw.rect(surface, (255, 90, 90), enemy_legend_rect)
    pygame.draw.rect(surface, (140, 20, 20), enemy_legend_rect, 1)
    enemy_text = legend_font.render("적군", True, (255, 255, 255))
    surface.blit(enemy_text, (enemy_legend_rect.right + 6, enemy_legend_rect.y - 1))


def build_stat_polygon(cx, cy, outer_radius, angles, values):
    points = []
    for angle, value in zip(angles, values):
        ratio = max(0.0, min(1.0, value / 10.0))
        r = outer_radius * ratio
        px = cx + math.cos(angle) * r
        py = cy + math.sin(angle) * r
        points.append((px, py))
    return points