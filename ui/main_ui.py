import threading
import pygame

from controller.pregame_controller import PregameController

from ui.layout.layout import build_layout
from ui.components.stage_bar import draw_stage_bar

from ui.state.ui_state import UIState
from ui.panels.blue.blue_state import BlueState
from ui.panels.blue.blue_ui import BlueUI
from ui.panels.green.green_ui import GreenUI
from ui.panels.red.red_ui import draw_red


SCREEN_WIDTH = 1400
SCREEN_HEIGHT = 850

RIGHT_PANEL_WIDTH = 420
BOTTOM_PANEL_HEIGHT = 300
STAGE_BAR_HEIGHT = 90

FPS = 60


def run_ui(app_state):
    pygame.init()

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("LOL Pregame UI")

    clock = pygame.time.Clock()

    ui_state = UIState()
    blue_state = BlueState()

    blue_ui = BlueUI(blue_state)
    green_ui = GreenUI()

    controller_thread = None
    controller_running = False
    controller_error = None

    font = pygame.font.SysFont("malgungothic", 22, bold=True)
    small_font = pygame.font.SysFont("malgungothic", 16)

    def start_controller():
        nonlocal controller_thread, controller_running, controller_error

        if controller_running:
            return

        controller_running = True
        controller_error = None

        def worker():
            nonlocal controller_running, controller_error
            try:
                controller = PregameController(app_state)
                controller.run()
            except Exception as e:
                controller_error = str(e)
            finally:
                controller_running = False

        controller_thread = threading.Thread(target=worker, daemon=True)
        controller_thread.start()

    def draw_status_overlay():
        status_rect = pygame.Rect(16, 16, 420, 150)
        pygame.draw.rect(screen, (245, 245, 245), status_rect, border_radius=10)
        pygame.draw.rect(screen, (0, 0, 0), status_rect, 2, border_radius=10)

        lines = [
            f"controller: {'RUNNING' if controller_running else 'STOP'}",
            f"stage: {app_state.stage}",
            f"gpt_stage: {app_state.gpt_stage}",
            f"my_turn: {app_state.is_my_turn}",
            f"pick_order: {app_state.pick_order}",
        ]

        y = status_rect.y + 10
        for line in lines:
            text = small_font.render(line, True, (0, 0, 0))
            screen.blit(text, (status_rect.x + 12, y))
            y += 24

        if controller_error:
            err = small_font.render(f"ERROR: {controller_error[:40]}", True, (180, 0, 0))
            screen.blit(err, (status_rect.x + 12, y))

    def draw_start_button():
        button_rect = pygame.Rect(460, 24, 160, 48)

        if controller_running:
            color = (170, 170, 170)
            text = "실행 중"
        else:
            color = (90, 180, 110)
            text = "시작"

        pygame.draw.rect(screen, color, button_rect, border_radius=10)
        pygame.draw.rect(screen, (0, 0, 0), button_rect, 2, border_radius=10)

        text_surf = font.render(text, True, (0, 0, 0))
        text_rect = text_surf.get_rect(center=button_rect.center)
        screen.blit(text_surf, text_rect)

        return button_rect

    running = True

    while running:
        red_rect, blue_rect, stage_bar_rect, green_rect = build_layout(
            SCREEN_WIDTH,
            SCREEN_HEIGHT,
            RIGHT_PANEL_WIDTH,
            BOTTOM_PANEL_HEIGHT,
            STAGE_BAR_HEIGHT,
        )

        current_stage = app_state.stage
        ui_state.current_stage = current_stage

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            start_button_rect = pygame.Rect(460, 24, 160, 48)

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if start_button_rect.collidepoint(event.pos):
                    start_controller()

                stage_buttons = draw_stage_bar(
                    screen,
                    stage_bar_rect.x,
                    stage_bar_rect.y,
                    stage_bar_rect.width,
                    stage_bar_rect.height,
                    ui_state.current_stage,
                )

                for idx, button in enumerate(stage_buttons):
                    if button.collidepoint(event.pos):
                        app_state.stage = idx
                        ui_state.current_stage = idx
                        blue_ui.sync_stage_layout(idx)

            blue_ui.handle_event(event, blue_rect)
            green_ui.handle_event(event, green_rect)

        blue_ui.update()

        screen.fill((30, 30, 30))

        draw_red(screen, red_rect)
        blue_ui.draw(screen, blue_rect, ui_state.current_stage)
        green_ui.draw(screen, green_rect, ui_state.current_stage)

        draw_stage_bar(
            screen,
            stage_bar_rect.x,
            stage_bar_rect.y,
            stage_bar_rect.width,
            stage_bar_rect.height,
            ui_state.current_stage,
        )

        draw_status_overlay()
        draw_start_button()

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()