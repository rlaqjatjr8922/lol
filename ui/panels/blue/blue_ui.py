import pygame

from .blue_anim import update_swap_animation
from .blue_stage import (
    trigger_swap_to_stage2,
    trigger_swap_to_stage3,
    sync_stage_layout,
)
from .blue_stage0 import draw_blue_stage0
from .blue_content import draw_blue_content
from .blue_scroll import apply_wheel_scroll
from .blue_scrollbar import draw_horizontal_scrollbar, handle_scrollbar_event


class BlueUI:
    def __init__(self, state):
        self.state = state

    def trigger_swap_to_stage2(self):
        trigger_swap_to_stage2(self.state)

    def trigger_swap_to_stage3(self):
        trigger_swap_to_stage3(self.state)

    def sync_stage_layout(self, stage):
        sync_stage_layout(self.state, stage)

    def update(self):
        self.state.progress, self.state.is_animating = update_swap_animation(
            self.state.progress,
            self.state.speed,
            self.state.is_animating,
        )

        if not self.state.is_animating:
            self.state.mode = self.state.animation_target_mode
            self.state.progress = 0.0 if self.state.mode == "original" else 1.0

    def handle_event(self, event, rect):
        self.state.scroll_x = apply_wheel_scroll(
            event=event,
            rect=rect,
            scroll_x=self.state.scroll_x,
            scroll_speed=self.state.scroll_speed,
            content_width=self.state.content_width,
        )

        (
            self.state.scroll_x,
            self.state.is_dragging_scrollbar,
            self.state.scrollbar_drag_offset_x,
            _,
        ) = handle_scrollbar_event(
            event=event,
            panel_rect=rect,
            content_width=self.state.content_width,
            scroll_x=self.state.scroll_x,
            is_dragging=self.state.is_dragging_scrollbar,
            drag_offset_x=self.state.scrollbar_drag_offset_x,
        )

    def draw(self, screen, rect, stage):
        pygame.draw.rect(screen, (70, 120, 220), rect)
        pygame.draw.rect(screen, (0, 0, 0), rect, 3)

        if stage == 0:
            draw_blue_stage0(screen, rect)
            return

        self.state.content_width = int(rect.width * 1.8)

        content_surface = pygame.Surface((self.state.content_width, rect.height))
        content_surface.fill((70, 120, 220))

        draw_blue_content(
            surface=content_surface,
            area_w=self.state.content_width,
            area_h=rect.height,
            stage=stage,
            state=self.state,
        )

        screen.blit(
            content_surface,
            rect.topleft,
            area=pygame.Rect(self.state.scroll_x, 0, rect.width, rect.height),
        )

        pygame.draw.rect(screen, (0, 0, 0), rect, 3)

        draw_horizontal_scrollbar(
            screen=screen,
            panel_rect=rect,
            content_width=self.state.content_width,
            scroll_x=self.state.scroll_x,
        )