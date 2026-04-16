import pygame

from .blue_scroll import (
    clamp_scroll,
    get_max_scroll,
    viewport_x_to_scroll_x,
)


def get_scrollbar_rect(panel_rect):
    track_margin_x = 16
    track_margin_bottom = 10
    track_height = 14

    return pygame.Rect(
        panel_rect.x + track_margin_x,
        panel_rect.bottom - track_height - track_margin_bottom,
        panel_rect.width - track_margin_x * 2,
        track_height,
    )


def get_handle_rect(panel_rect, content_width, scroll_x):
    track_rect = get_scrollbar_rect(panel_rect)
    max_scroll = get_max_scroll(content_width, panel_rect.width)

    if max_scroll <= 0:
        return track_rect.copy()

    visible_ratio = panel_rect.width / content_width
    handle_width = max(60, int(track_rect.width * visible_ratio))
    handle_width = min(handle_width, track_rect.width)

    movable_w = max(1, track_rect.width - handle_width)
    scroll_ratio = scroll_x / max_scroll if max_scroll > 0 else 0.0
    handle_x = track_rect.x + int(movable_w * scroll_ratio)

    return pygame.Rect(
        handle_x,
        track_rect.y,
        handle_width,
        track_rect.height,
    )


def draw_horizontal_scrollbar(screen, panel_rect, content_width, scroll_x):
    if content_width <= panel_rect.width:
        return

    track_rect = get_scrollbar_rect(panel_rect)
    handle_rect = get_handle_rect(panel_rect, content_width, scroll_x)

    pygame.draw.rect(screen, (35, 35, 35), track_rect, border_radius=7)
    pygame.draw.rect(screen, (0, 0, 0), track_rect, 2, border_radius=7)

    pygame.draw.rect(screen, (210, 210, 210), handle_rect, border_radius=7)
    pygame.draw.rect(screen, (0, 0, 0), handle_rect, 2, border_radius=7)


def handle_scrollbar_event(
    event,
    panel_rect,
    content_width,
    scroll_x,
    is_dragging,
    drag_offset_x,
):
    if content_width <= panel_rect.width:
        return 0, False, 0, False

    track_rect = get_scrollbar_rect(panel_rect)
    handle_rect = get_handle_rect(panel_rect, content_width, scroll_x)

    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        if handle_rect.collidepoint(event.pos):
            new_offset = event.pos[0] - handle_rect.x
            return scroll_x, True, new_offset, True

        if track_rect.collidepoint(event.pos):
            new_scroll_x = _jump_handle_to_mouse(
                mouse_x=event.pos[0],
                panel_rect=panel_rect,
                content_width=content_width,
                current_scroll_x=scroll_x,
            )
            new_handle_rect = get_handle_rect(panel_rect, content_width, new_scroll_x)
            new_offset = event.pos[0] - new_handle_rect.x
            return new_scroll_x, True, new_offset, True

    elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
        if is_dragging:
            return scroll_x, False, 0, True

    elif event.type == pygame.MOUSEMOTION and is_dragging:
        new_scroll_x = _drag_handle(
            mouse_x=event.pos[0],
            panel_rect=panel_rect,
            content_width=content_width,
            drag_offset_x=drag_offset_x,
        )
        return new_scroll_x, True, drag_offset_x, True

    return scroll_x, is_dragging, drag_offset_x, False


def _jump_handle_to_mouse(mouse_x, panel_rect, content_width, current_scroll_x):
    track_rect = get_scrollbar_rect(panel_rect)
    handle_rect = get_handle_rect(panel_rect, content_width, current_scroll_x)

    target_left = mouse_x - handle_rect.width // 2
    local_left = target_left - track_rect.x
    local_left = max(0, min(local_left, track_rect.width - handle_rect.width))

    target_mouse_x = track_rect.x + local_left
    new_scroll_x = viewport_x_to_scroll_x(
        mouse_x=target_mouse_x,
        track_rect=track_rect,
        handle_width=handle_rect.width,
        content_width=content_width,
        viewport_width=panel_rect.width,
    )
    return clamp_scroll(new_scroll_x, content_width, panel_rect.width)


def _drag_handle(mouse_x, panel_rect, content_width, drag_offset_x):
    track_rect = get_scrollbar_rect(panel_rect)
    current_handle_rect = get_handle_rect(panel_rect, content_width, 0)
    handle_width = current_handle_rect.width

    handle_left = mouse_x - drag_offset_x
    local_left = handle_left - track_rect.x
    local_left = max(0, min(local_left, track_rect.width - handle_width))

    target_mouse_x = track_rect.x + local_left
    new_scroll_x = viewport_x_to_scroll_x(
        mouse_x=target_mouse_x,
        track_rect=track_rect,
        handle_width=handle_width,
        content_width=content_width,
        viewport_width=panel_rect.width,
    )
    return clamp_scroll(new_scroll_x, content_width, panel_rect.width)