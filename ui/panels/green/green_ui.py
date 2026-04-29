import pygame


class GreenUI:
    def __init__(self):
        self.scroll_y = 0
        self.scroll_speed = 40

        self.gpt_stage = 0
        self.gpt_parsed = {}
        self.champions = []

        self.padding = 12
        self.card_gap = 12
        self.card_height = 120

    def handle_event(self, event, rect):
        if event.type == pygame.MOUSEWHEEL:
            mouse_x, mouse_y = pygame.mouse.get_pos()

            if rect.collidepoint(mouse_x, mouse_y):
                content_h = self._get_content_height(rect.width)
                self.scroll_y -= event.y * self.scroll_speed

                max_scroll = max(0, content_h - rect.height)
                self.scroll_y = max(0, min(self.scroll_y, max_scroll))

    def _sync_gpt_to_champions(self):
        gpt_data = self.gpt_parsed or {}

        if not isinstance(gpt_data, dict):
            self.champions = []
            return

        self.champions = [
            {
                "name": champ,
                "tags": tags if isinstance(tags, list) else [str(tags)],
            }
            for champ, tags in gpt_data.items()
        ]

    def _get_bg_color(self, stage):
        if stage == 0:
            return (55, 120, 80)
        if stage == 1:
            return (40, 140, 70)
        if stage == 2:
            return (120, 220, 150)
        if stage == 3:
            return (70, 180, 100)
        if stage == 4:
            return (85, 170, 115)
        return (70, 180, 100)

    def _get_content_height(self, width):
        total_cards_h = len(self.champions) * self.card_height
        total_gaps_h = max(0, len(self.champions) - 1) * self.card_gap
        total_padding_h = self.padding * 2
        return total_cards_h + total_gaps_h + total_padding_h

    def draw(self, screen, rect, stage):
        self._sync_gpt_to_champions()

        bg_color = self._get_bg_color(stage)

        pygame.draw.rect(screen, bg_color, rect)
        pygame.draw.rect(screen, (0, 0, 0), rect, 3)

        if self.gpt_stage == 2:
            self._draw_wait(screen, rect)
            return rect

        if not self.champions:
            self._draw_empty(screen, rect)
            return rect

        content_h = self._get_content_height(rect.width)

        content_surface = pygame.Surface((rect.width, content_h))
        content_surface.fill(bg_color)

        self._draw_cards(content_surface, rect.width)

        screen.blit(
            content_surface,
            rect.topleft,
            area=pygame.Rect(0, self.scroll_y, rect.width, rect.height),
        )

        pygame.draw.rect(screen, (0, 0, 0), rect, 3)
        self._draw_scrollbar(screen, rect, content_h)

        return rect

    def _draw_empty(self, screen, rect):
        title_font = pygame.font.SysFont("malgungothic", 30, bold=True)
        sub_font = pygame.font.SysFont("malgungothic", 18)

        title_text = title_font.render("추천 준비중", True, (255, 255, 255))
        sub_text = sub_font.render("GPT 추천 결과를 기다리는 중", True, (235, 235, 235))

        title_rect = title_text.get_rect(center=(rect.centerx, rect.centery - 18))
        sub_rect = sub_text.get_rect(center=(rect.centerx, rect.centery + 18))

        screen.blit(title_text, title_rect)
        screen.blit(sub_text, sub_rect)

    def _draw_wait(self, screen, rect):
        title_font = pygame.font.SysFont("malgungothic", 30, bold=True)
        sub_font = pygame.font.SysFont("malgungothic", 18)

        title_text = title_font.render("추천 대기중", True, (255, 255, 255))
        sub_text = sub_font.render("GPT 분석 중...", True, (235, 235, 235))

        title_rect = title_text.get_rect(center=(rect.centerx, rect.centery - 18))
        sub_rect = sub_text.get_rect(center=(rect.centerx, rect.centery + 18))

        screen.blit(title_text, title_rect)
        screen.blit(sub_text, sub_rect)

    def _draw_cards(self, surface, width):
        font_name = pygame.font.SysFont("malgungothic", 20)
        font_tag = pygame.font.SysFont("malgungothic", 16)

        card_width = width - self.padding * 2
        y = self.padding

        for champ in self.champions:
            card_rect = pygame.Rect(self.padding, y, card_width, self.card_height)

            pygame.draw.rect(surface, (240, 240, 240), card_rect, border_radius=8)
            pygame.draw.rect(surface, (0, 0, 0), card_rect, 2, border_radius=8)

            portrait_size = self.card_height - 20
            portrait_rect = pygame.Rect(
                card_rect.x + 10,
                card_rect.y + 10,
                portrait_size,
                portrait_size,
            )

            pygame.draw.rect(surface, (200, 60, 60), portrait_rect)
            pygame.draw.rect(surface, (0, 0, 0), portrait_rect, 2)

            text_x = portrait_rect.right + 10
            text_y = card_rect.y + 10

            name_text = font_name.render(str(champ["name"]), True, (0, 0, 0))
            surface.blit(name_text, (text_x, text_y))

            tag_x = text_x
            tag_y = text_y + 30

            for tag in champ["tags"]:
                tag_surface = font_tag.render(str(tag), True, (0, 0, 0))
                tag_rect = tag_surface.get_rect()

                bg_rect = pygame.Rect(
                    tag_x,
                    tag_y,
                    tag_rect.width + 10,
                    tag_rect.height + 6,
                )

                pygame.draw.rect(surface, (200, 200, 200), bg_rect, border_radius=6)
                pygame.draw.rect(surface, (0, 0, 0), bg_rect, 1, border_radius=6)

                surface.blit(tag_surface, (tag_x + 5, tag_y + 3))
                tag_x += bg_rect.width + 6

            y += self.card_height + self.card_gap

    def _draw_scrollbar(self, screen, rect, content_h):
        if content_h <= rect.height:
            return

        track_margin = 6
        track_width = 10

        track_rect = pygame.Rect(
            rect.right - track_width - track_margin,
            rect.y + track_margin,
            track_width,
            rect.height - track_margin * 2,
        )

        pygame.draw.rect(screen, (180, 180, 180), track_rect, border_radius=5)
        pygame.draw.rect(screen, (0, 0, 0), track_rect, 1, border_radius=5)

        handle_height = max(40, int(track_rect.height * (rect.height / content_h)))

        max_scroll = content_h - rect.height
        scroll_ratio = self.scroll_y / max_scroll if max_scroll > 0 else 0

        handle_y = track_rect.y + int(
            (track_rect.height - handle_height) * scroll_ratio
        )

        handle_rect = pygame.Rect(
            track_rect.x,
            handle_y,
            track_rect.width,
            handle_height,
        )

        pygame.draw.rect(screen, (110, 110, 110), handle_rect, border_radius=5)
        pygame.draw.rect(screen, (0, 0, 0), handle_rect, 1, border_radius=5)