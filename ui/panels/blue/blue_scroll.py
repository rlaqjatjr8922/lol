import pygame


def get_max_scroll(content_width, viewport_width):
    return max(0, int(content_width - viewport_width))


def clamp_scroll(scroll_x, content_width, viewport_width):
    max_scroll = get_max_scroll(content_width, viewport_width)
    return max(0, min(int(scroll_x), max_scroll))


def apply_wheel_scroll(event, rect, scroll_x, scroll_speed, content_width):
    if event.type != pygame.MOUSEWHEEL:
        return scroll_x

    mouse_x, mouse_y = pygame.mouse.get_pos()
    if not rect.collidepoint(mouse_x, mouse_y):
        return scroll_x

    new_scroll_x = scroll_x - event.y * scroll_speed
    return clamp_scroll(new_scroll_x, content_width, rect.width)


def scroll_ratio_to_x(ratio, content_width, viewport_width):
    max_scroll = get_max_scroll(content_width, viewport_width)
    if max_scroll <= 0:
        return 0
    ratio = max(0.0, min(1.0, ratio))
    return int(max_scroll * ratio)


def scroll_x_to_ratio(scroll_x, content_width, viewport_width):
    max_scroll = get_max_scroll(content_width, viewport_width)
    if max_scroll <= 0:
        return 0.0
    return max(0.0, min(1.0, scroll_x / max_scroll))


def viewport_x_to_scroll_x(mouse_x, track_rect, handle_width, content_width, viewport_width):
    max_scroll = get_max_scroll(content_width, viewport_width)
    movable_w = max(1, track_rect.width - handle_width)

    local_x = mouse_x - track_rect.x
    local_x = max(0, min(local_x, movable_w))

    ratio = local_x / movable_w
    return int(max_scroll * ratio)