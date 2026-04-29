import pygame
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[3]
CHAMPION_DIR = BASE_DIR / "assets" / "champions"
_image_cache = {}


def norm_champion_name(name):
    name = str(name).strip().lower()
    name = name.replace(" ", "").replace("'", "")
    return name


def load_champion_image(name, size):
    key = (str(name), size)

    if key in _image_cache:
        return _image_cache[key]

    path = CHAMPION_DIR / f"{norm_champion_name(name)}.png"

    if not path.exists():
        _image_cache[key] = None
        return None

    img = pygame.image.load(str(path)).convert_alpha()
    img = pygame.transform.smoothscale(img, size)

    _image_cache[key] = img
    return img


def draw_team_block(
    surface,
    team_x,
    team_y,
    team_w,
    team_h,
    ap_ratio,
    reverse_top,
    progress,
    is_animating,
    mode,
    highlight_big_count=0,
    small_champions=None,
    big_champions=None,
):
    top_row_h = int(team_h * 0.20)
    square_zone_h = int(team_h * 0.55)

    small_border_color = (255, 60, 60)
    big_border_color = (255, 230, 120)
    empty_fill_color = (0, 0, 0)

    mini_gap = max(4, int(team_w * 0.008))
    row_side_pad = max(10, int(team_w * 0.02))
    bar_gap = max(12, int(team_w * 0.02))

    mini_size = min(top_row_h - 14, int(team_w * 0.09))

    square_gap = max(6, int(team_w * 0.01))
    max_by_width = (team_w - square_gap * 4) // 5
    max_by_height = square_zone_h - 10
    square_size = min(max_by_width, max_by_height)

    mini_total_w = mini_size * 5 + mini_gap * 4
    available_w = team_w - row_side_pad * 2
    bar_w = available_w - mini_total_w - bar_gap

    if bar_w < 70:
        bar_w = 70

    bar_h = max(14, int(mini_size * 0.60))
    row_center_y = team_y + top_row_h // 2
    start_x = team_x + row_side_pad

    square_y = team_y + top_row_h
    center_x = team_x + team_w // 2

    if not reverse_top:
        original_small_start_x = start_x
    else:
        original_small_start_x = team_x + team_w - row_side_pad - mini_total_w

    original_big_total_w = square_size * 5 + square_gap * 4
    original_big_start_x = center_x - original_big_total_w / 2

    original_small_y = team_y + top_row_h // 2 - mini_size // 2
    original_big_y = square_y + (square_zone_h - square_size) // 2

    original_small_size = mini_size
    original_big_size = square_size

    swapped_small_y = original_big_y
    swapped_big_y = original_small_y

    swapped_small_size = square_size
    swapped_big_size = mini_size

    if is_animating:
        if mode == "original":
            small_y = lerp(original_small_y, swapped_small_y, progress)
            big_y = lerp(original_big_y, swapped_big_y, progress)
            small_size = lerp(original_small_size, swapped_small_size, progress)
            big_size = lerp(original_big_size, swapped_big_size, progress)

            small_total_w = small_size * 5 + mini_gap * 4

            small_start_x = lerp(
                original_small_start_x,
                center_x - small_total_w / 2,
                progress,
            )

            big_start_x = lerp(
                original_big_start_x,
                original_small_start_x,
                progress,
            )
        else:
            small_y = lerp(swapped_small_y, original_small_y, progress)
            big_y = lerp(swapped_big_y, original_big_y, progress)
            small_size = lerp(swapped_small_size, original_small_size, progress)
            big_size = lerp(swapped_big_size, original_big_size, progress)

            swapped_small_total_w = swapped_small_size * 5 + mini_gap * 4
            swapped_small_start_x = center_x - swapped_small_total_w / 2

            small_start_x = lerp(
                swapped_small_start_x,
                original_small_start_x,
                progress,
            )

            big_start_x = lerp(
                original_small_start_x,
                original_big_start_x,
                progress,
            )
    else:
        if mode == "original":
            small_y = original_small_y
            big_y = original_big_y
            small_size = original_small_size
            big_size = original_big_size
            small_start_x = original_small_start_x
            big_start_x = original_big_start_x
        else:
            small_y = swapped_small_y
            big_y = swapped_big_y
            small_size = swapped_small_size
            big_size = swapped_big_size

            small_total_w = small_size * 5 + mini_gap * 4
            small_start_x = center_x - small_total_w / 2
            big_start_x = original_small_start_x

    draw_top_bar(
        surface=surface,
        start_x=start_x,
        row_center_y=row_center_y,
        mini_size=mini_size,
        mini_gap=mini_gap,
        bar_gap=bar_gap,
        bar_w=bar_w,
        bar_h=bar_h,
        ap_ratio=ap_ratio,
        reverse_top=reverse_top,
        team_x=team_x,
        team_w=team_w,
        row_side_pad=row_side_pad,
    )

    draw_big_group(
        surface=surface,
        start_x=big_start_x,
        y=big_y,
        size=big_size,
        gap=square_gap,
        border_color=big_border_color,
        fill_color=empty_fill_color,
        highlight_count=highlight_big_count,
        champions=big_champions,
    )

    draw_small_group(
        surface=surface,
        start_x=small_start_x,
        y=small_y,
        size=small_size,
        gap=mini_gap,
        border_color=small_border_color,
        fill_color=empty_fill_color,
        champions=small_champions,
    )

    draw_bottom_circles(
        surface=surface,
        start_x=big_start_x,
        y=big_y,
        size=big_size,
        gap=square_gap,
    )


def lerp(a, b, t):
    return a + (b - a) * t


def draw_top_bar(
    surface,
    start_x,
    row_center_y,
    mini_size,
    mini_gap,
    bar_gap,
    bar_w,
    bar_h,
    ap_ratio,
    reverse_top,
    team_x=None,
    team_w=None,
    row_side_pad=None,
):
    mini_total_w = mini_size * 5 + mini_gap * 4

    if not reverse_top:
        bar_x = start_x + mini_total_w + bar_gap
    else:
        if team_x is not None and team_w is not None and row_side_pad is not None:
            bar_x = team_x + row_side_pad
        else:
            bar_x = start_x

    bar_rect = pygame.Rect(
        int(bar_x),
        int(row_center_y - bar_h // 2),
        int(bar_w),
        int(bar_h),
    )

    draw_ap_ad_bar(surface, bar_rect, ap_ratio)


def draw_small_group(
    surface,
    start_x,
    y,
    size,
    gap,
    border_color,
    fill_color,
    champions=None,
):
    champions = champions or []

    for i in range(5):
        x = start_x + i * (size + gap)
        rect = pygame.Rect(int(x), int(y), int(size), int(size))

        pygame.draw.rect(surface, fill_color, rect)

        if i < len(champions):
            img = load_champion_image(champions[i], (int(size), int(size)))
            if img:
                surface.blit(img, rect.topleft)

        pygame.draw.rect(surface, border_color, rect, 2)


def draw_big_group(
    surface,
    start_x,
    y,
    size,
    gap,
    border_color,
    fill_color,
    highlight_count=0,
    champions=None,
):
    champions = champions or []

    for i in range(5):
        x = start_x + i * (size + gap)
        rect = pygame.Rect(int(x), int(y), int(size), int(size))

        pygame.draw.rect(surface, fill_color, rect)

        if i < len(champions):
            img = load_champion_image(champions[i], (int(size), int(size)))
            if img:
                surface.blit(img, rect.topleft)

        pygame.draw.rect(surface, border_color, rect, 3)

        if i < highlight_count:
            draw_glow_border(surface, rect)


def draw_glow_border(surface, rect):
    glow_outer = rect.inflate(18, 18)
    glow_mid = rect.inflate(10, 10)
    glow_inner = rect.inflate(4, 4)

    pygame.draw.rect(surface, (255, 245, 170), glow_outer, 2, border_radius=10)
    pygame.draw.rect(surface, (255, 240, 120), glow_mid, 3, border_radius=8)
    pygame.draw.rect(surface, (255, 255, 220), glow_inner, 3, border_radius=6)
    pygame.draw.rect(surface, (255, 255, 255), rect, 2, border_radius=4)


def draw_bottom_circles(surface, start_x, y, size, gap):
    radius = max(8, min(size // 7, size // 5))
    circle_center_y = y + size - radius // 2

    for i in range(5):
        cx = start_x + size // 2 + i * (size + gap)
        cy = circle_center_y

        pygame.draw.circle(surface, (235, 235, 235), (int(cx), int(cy)), radius)
        pygame.draw.circle(surface, (0, 0, 0), (int(cx), int(cy)), radius, 2)


def draw_ap_ad_bar(surface, rect, ap_ratio):
    ap_ratio = max(0.0, min(1.0, ap_ratio))

    pygame.draw.rect(surface, (20, 20, 20), rect)
    pygame.draw.rect(surface, (0, 0, 0), rect, 2)

    ap_w = int(rect.width * ap_ratio)
    ad_w = rect.width - ap_w

    if ap_w > 0:
        pygame.draw.rect(
            surface,
            (100, 140, 255),
            pygame.Rect(rect.x, rect.y, ap_w, rect.height),
        )

    if ad_w > 0:
        pygame.draw.rect(
            surface,
            (255, 110, 70),
            pygame.Rect(rect.x + ap_w, rect.y, ad_w, rect.height),
        )

    if 0 < ap_w < rect.width:
        pygame.draw.line(
            surface,
            (0, 0, 0),
            (rect.x + ap_w, rect.y),
            (rect.x + ap_w, rect.y + rect.height),
            2,
        )

    pygame.draw.rect(surface, (0, 0, 0), rect, 2)

    font = pygame.font.SysFont("malgungothic", max(12, rect.height - 2))
    ap_text = font.render("AP", True, (255, 255, 255))
    ad_text = font.render("AD", True, (255, 255, 255))

    ap_text_rect = ap_text.get_rect(
        center=(rect.x + max(ap_w // 2, 12), rect.centery)
    )
    ad_text_rect = ad_text.get_rect(
        center=(rect.x + ap_w + max(ad_w // 2, 12), rect.centery)
    )

    if ap_w >= ap_text_rect.width + 8:
        surface.blit(ap_text, ap_text_rect)

    if ad_w >= ad_text_rect.width + 8:
        surface.blit(ad_text, ad_text_rect)