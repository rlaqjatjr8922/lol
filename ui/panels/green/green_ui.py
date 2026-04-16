import pygame


class GreenUI:
    def __init__(self):
        self.scroll_y = 0
        self.scroll_speed = 40

        self.champions = [
            {"name": "아리", "tags": ["라인전강함", "카운터"]},
            {"name": "제드", "tags": ["암살", "캐리"]},
            {"name": "가렌", "tags": ["탱", "쉬움"]},
            {"name": "이즈리얼", "tags": ["포킹", "원딜"]},
            {"name": "카직스", "tags": ["암살", "정글"]},
            {"name": "럭스", "tags": ["포킹", "서포터"]},
            {"name": "레오나", "tags": ["이니시", "탱"]},
            {"name": "야스오", "tags": ["캐리", "근접"]},
            {"name": "징크스", "tags": ["후반", "원딜"]},
            {"name": "오리아나", "tags": ["한타", "메이지"]},
            {"name": "리신", "tags": ["정글", "초반강함"]},
            {"name": "베인", "tags": ["후반", "하이퍼캐리"]},
        ]

        self.padding = 12
        self.card_gap = 12
        self.card_height = 120

        self.rune_data = {
            "main_title": "룬 추천",
            "sub_title": "아리 미드 기준",
            "primary": {
                "name": "지배",
                "keystone": "감전",
                "slots": ["비열한 한 방", "사냥의 증표", "궁극의 사냥꾼"],
            },
            "secondary": {
                "name": "마법",
                "slots": ["마나순환 팔찌", "깨달음"],
            },
            "shards": ["적응형", "적응형", "체력"],
        }

    def handle_event(self, event, rect):
        if event.type == pygame.MOUSEWHEEL:
            mouse_x, mouse_y = pygame.mouse.get_pos()

            if rect.collidepoint(mouse_x, mouse_y):
                content_h = self._get_content_height(rect.width)
                self.scroll_y -= event.y * self.scroll_speed

                max_scroll = max(0, content_h - rect.height)
                self.scroll_y = max(0, min(self.scroll_y, max_scroll))

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
        bg_color = self._get_bg_color(stage)

        pygame.draw.rect(screen, bg_color, rect)
        pygame.draw.rect(screen, (0, 0, 0), rect, 3)

        if stage == 0:
            self._draw_stage0(screen, rect)
            return rect

        if stage == 4:
            self._draw_rune_recommend(screen, rect)
            pygame.draw.rect(screen, (0, 0, 0), rect, 3)
            return rect

        content_h = self._get_content_height(rect.width)

        content_surface = pygame.Surface((rect.width, content_h))
        content_surface.fill(bg_color)

        self._draw_cards(content_surface, rect.width)

        screen.blit(
            content_surface,
            rect.topleft,
            area=pygame.Rect(0, self.scroll_y, rect.width, rect.height)
        )

        pygame.draw.rect(screen, (0, 0, 0), rect, 3)
        self._draw_scrollbar(screen, rect, content_h)

        return rect

    def _draw_stage0(self, screen, rect):
        title_font = pygame.font.SysFont("malgungothic", 30, bold=True)
        sub_font = pygame.font.SysFont("malgungothic", 18)

        title_text = title_font.render("추천 준비중", True, (255, 255, 255))
        sub_text = sub_font.render("라인 감지 후 추천을 표시합니다", True, (235, 235, 235))

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
                portrait_size
            )

            pygame.draw.rect(surface, (200, 60, 60), portrait_rect)
            pygame.draw.rect(surface, (0, 0, 0), portrait_rect, 2)

            text_x = portrait_rect.right + 10
            text_y = card_rect.y + 10

            name_text = font_name.render(champ["name"], True, (0, 0, 0))
            surface.blit(name_text, (text_x, text_y))

            tag_x = text_x
            tag_y = text_y + 30

            for tag in champ["tags"]:
                tag_surface = font_tag.render(tag, True, (0, 0, 0))
                tag_rect = tag_surface.get_rect()

                bg_rect = pygame.Rect(
                    tag_x,
                    tag_y,
                    tag_rect.width + 10,
                    tag_rect.height + 6
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
            rect.height - track_margin * 2
        )

        pygame.draw.rect(screen, (180, 180, 180), track_rect, border_radius=5)
        pygame.draw.rect(screen, (0, 0, 0), track_rect, 1, border_radius=5)

        handle_height = max(
            40,
            int(track_rect.height * (rect.height / content_h))
        )

        max_scroll = content_h - rect.height
        scroll_ratio = self.scroll_y / max_scroll if max_scroll > 0 else 0

        handle_y = track_rect.y + int((track_rect.height - handle_height) * scroll_ratio)

        handle_rect = pygame.Rect(
            track_rect.x,
            handle_y,
            track_rect.width,
            handle_height
        )

        pygame.draw.rect(screen, (110, 110, 110), handle_rect, border_radius=5)
        pygame.draw.rect(screen, (0, 0, 0), handle_rect, 1, border_radius=5)

    def _draw_rune_recommend(self, screen, rect):
        title_font = pygame.font.SysFont("malgungothic", 30, bold=True)
        sub_font = pygame.font.SysFont("malgungothic", 18)
        rune_font = pygame.font.SysFont("malgungothic", 20, bold=True)
        text_font = pygame.font.SysFont("malgungothic", 16)

        inner = rect.inflate(-24, -24)

        panel_rect = pygame.Rect(inner.x, inner.y, inner.width, inner.height)
        pygame.draw.rect(screen, (235, 245, 235), panel_rect, border_radius=12)
        pygame.draw.rect(screen, (0, 0, 0), panel_rect, 2, border_radius=12)

        title = title_font.render(self.rune_data["main_title"], True, (20, 40, 20))
        subtitle = sub_font.render(self.rune_data["sub_title"], True, (40, 70, 40))
        screen.blit(title, (panel_rect.x + 16, panel_rect.y + 14))
        screen.blit(subtitle, (panel_rect.x + 18, panel_rect.y + 52))

        section_y = panel_rect.y + 95
        section_gap = 16
        section_h = 180
        section_w = (panel_rect.width - 16 * 3) // 2

        primary_rect = pygame.Rect(
            panel_rect.x + 16,
            section_y,
            section_w,
            section_h
        )
        secondary_rect = pygame.Rect(
            primary_rect.right + 16,
            section_y,
            section_w,
            section_h
        )

        self._draw_rune_section(
            screen,
            primary_rect,
            self.rune_data["primary"]["name"],
            [self.rune_data["primary"]["keystone"]] + self.rune_data["primary"]["slots"],
            (220, 190, 120)
        )

        self._draw_rune_section(
            screen,
            secondary_rect,
            self.rune_data["secondary"]["name"],
            self.rune_data["secondary"]["slots"],
            (160, 190, 255)
        )

        shard_rect = pygame.Rect(
            panel_rect.x + 16,
            primary_rect.bottom + section_gap,
            panel_rect.width - 32,
            110
        )

        pygame.draw.rect(screen, (245, 245, 245), shard_rect, border_radius=10)
        pygame.draw.rect(screen, (0, 0, 0), shard_rect, 2, border_radius=10)

        shard_title = rune_font.render("파편", True, (0, 0, 0))
        screen.blit(shard_title, (shard_rect.x + 14, shard_rect.y + 12))

        chip_x = shard_rect.x + 16
        chip_y = shard_rect.y + 52

        for shard in self.rune_data["shards"]:
            chip = text_font.render(shard, True, (0, 0, 0))
            chip_rect = pygame.Rect(
                chip_x,
                chip_y,
                chip.get_width() + 18,
                chip.get_height() + 10
            )

            pygame.draw.rect(screen, (215, 215, 215), chip_rect, border_radius=8)
            pygame.draw.rect(screen, (0, 0, 0), chip_rect, 1, border_radius=8)
            screen.blit(chip, (chip_rect.x + 9, chip_rect.y + 5))

            chip_x += chip_rect.width + 10

    def _draw_rune_section(self, screen, rect, title, items, accent_color):
        title_font = pygame.font.SysFont("malgungothic", 20, bold=True)
        text_font = pygame.font.SysFont("malgungothic", 16)

        pygame.draw.rect(screen, (245, 245, 245), rect, border_radius=10)
        pygame.draw.rect(screen, accent_color, rect, 3, border_radius=10)

        title_surf = title_font.render(title, True, (0, 0, 0))
        screen.blit(title_surf, (rect.x + 14, rect.y + 12))

        y = rect.y + 52
        for item in items:
            icon_rect = pygame.Rect(rect.x + 14, y, 22, 22)
            pygame.draw.ellipse(screen, accent_color, icon_rect)
            pygame.draw.ellipse(screen, (0, 0, 0), icon_rect, 1)

            text_surf = text_font.render(item, True, (0, 0, 0))
            screen.blit(text_surf, (icon_rect.right + 10, y + 1))
            y += 30