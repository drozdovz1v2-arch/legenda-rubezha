"""Финальная катсцена — после квеста «Песчаный титан»."""

import math
import pygame

FINALE_PAGES = [
    {
        "title": "Колосс пал",
        "lines": [
            "Песчаный колосс рассыпался в прах.",
            "Пустыня впервые за века затихла.",
            "Торговые пути снова открыты.",
        ],
        "accent": (255, 190, 80),
    },
    {
        "title": "Пробуждение Рубежа",
        "lines": [
            "Лес, пустыня, лёд и руины —",
            "все границы мира встали на место.",
            "Древнее проклятие ослабло.",
        ],
        "accent": (120, 220, 255),
    },
    {
        "title": "Легенда Рубежа",
        "lines": [
            "Старейшина, разведчик и мистик",
            "склоняют головы перед тобой.",
            "Твоё имя войдёт в хроники.",
        ],
        "accent": (180, 140, 255),
    },
    {
        "title": "Свобода",
        "lines": [
            "Сюжет завершён — но мир жив.",
            "Исследуй, сражайся, собирай реликвии.",
            "Roguelike не прощает смерть.",
        ],
        "accent": (255, 215, 120),
    },
]


class FinaleScreen:
    FADE_SPEED = 7
    CHAR_DELAY = 2

    def __init__(self):
        self.active = False
        self.page_index = 0
        self.fade = 0
        self.elapsed = 0
        self.reveal_chars = 0
        self.font_title = pygame.font.SysFont("Arial", 44, bold=True)
        self.font_sub = pygame.font.SysFont("Arial", 22)
        self.font_hint = pygame.font.SysFont("Arial", 16)
        self.font_chapter = pygame.font.SysFont("Arial", 14, bold=True)
        self._stars = []

    def start(self):
        self.active = True
        self.page_index = 0
        self.fade = 0
        self.elapsed = 0
        self.reveal_chars = 0

    def _build_stars(self, w, h):
        import random
        rng = random.Random(42)
        self._stars = [
            (rng.randint(0, w), rng.randint(0, h), rng.randint(1, 3))
            for _ in range(100)
        ]

    def current_page(self):
        return FINALE_PAGES[min(self.page_index, len(FINALE_PAGES) - 1)]

    def full_text(self):
        return " ".join(self.current_page()["lines"])

    def skip(self):
        self.active = False

    def advance(self):
        if self.page_index >= len(FINALE_PAGES) - 1:
            self.active = False
            return True
        self.page_index += 1
        self.fade = 0
        self.elapsed = 0
        self.reveal_chars = 0
        return False

    def update(self):
        if not self.active:
            return
        self.elapsed += 1
        if self.fade < 255:
            self.fade = min(255, self.fade + self.FADE_SPEED)
        total = len(self.full_text())
        target = min(total, self.elapsed // self.CHAR_DELAY)
        if self.reveal_chars < target:
            self.reveal_chars = target

    def handle_event(self, event):
        if not self.active:
            return None
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.skip()
                return "done"
            if event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_e):
                if self.reveal_chars < len(self.full_text()):
                    self.reveal_chars = len(self.full_text())
                elif self.advance():
                    return "done"
                return "next"
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.reveal_chars < len(self.full_text()):
                self.reveal_chars = len(self.full_text())
            elif self.advance():
                return "done"
            return "next"
        return None

    def draw(self, screen, screen_w, screen_h):
        if not self.active:
            return

        if not self._stars or self._stars[0][0] > screen_w:
            self._build_stars(screen_w, screen_h)

        self._draw_background(screen, screen_w, screen_h)
        page = self.current_page()
        accent = page["accent"]
        alpha = self.fade

        chapter = self.font_chapter.render(
            f"ФИНАЛ {self.page_index + 1} / {len(FINALE_PAGES)}", True, accent
        )
        chapter.set_alpha(alpha)
        screen.blit(chapter, chapter.get_rect(center=(screen_w // 2, screen_h * 0.16)))

        title = self.font_title.render(page["title"], True, accent)
        title.set_alpha(alpha)
        screen.blit(title, title.get_rect(center=(screen_w // 2, screen_h * 0.27)))

        text = self.full_text()[: self.reveal_chars]
        y = screen_h * 0.41
        line_w = int(screen_w * 0.62)
        words = text.split(" ")
        line = ""
        for word in words:
            test = (line + " " + word).strip()
            surf_test = self.font_sub.render(test, True, (235, 235, 245))
            if surf_test.get_width() > line_w and line:
                line_surf = self.font_sub.render(line, True, (235, 235, 245))
                line_surf.set_alpha(alpha)
                screen.blit(line_surf, line_surf.get_rect(center=(screen_w // 2, y)))
                y += 34
                line = word
            else:
                line = test
        if line:
            line_surf = self.font_sub.render(line, True, (235, 235, 245))
            line_surf.set_alpha(alpha)
            screen.blit(line_surf, line_surf.get_rect(center=(screen_w // 2, y)))

        for i in range(len(FINALE_PAGES)):
            cx = screen_w // 2 - (len(FINALE_PAGES) - 1) * 12 + i * 24
            cy = int(screen_h * 0.74)
            color = accent if i == self.page_index else (70, 70, 80)
            pygame.draw.circle(screen, color, (cx, cy), 6 if i == self.page_index else 3)

        pulse = 0.6 + 0.4 * math.sin(pygame.time.get_ticks() * 0.004)
        if self.page_index >= len(FINALE_PAGES) - 1 and self.reveal_chars >= len(self.full_text()):
            hint_text = "Enter — продолжить приключение"
        elif self.reveal_chars < len(self.full_text()):
            hint_text = "Enter / E / клик — показать текст"
        else:
            hint_text = "Enter / E / клик — далее"
        hint = self.font_hint.render(hint_text, True, (150, 160, 175))
        hint.set_alpha(int(180 + 60 * pulse))
        screen.blit(hint, hint.get_rect(center=(screen_w // 2, screen_h - 48)))

    def _draw_background(self, screen, w, h):
        for y in range(h):
            t = y / max(1, h)
            color = (
                int(18 + 12 * t),
                int(12 + 10 * t),
                int(22 + 28 * t),
            )
            pygame.draw.line(screen, color, (0, y), (w, y))

        tick = pygame.time.get_ticks() * 0.00025
        for sx, sy, size in self._stars:
            twinkle = int(130 + 90 * math.sin(tick * 5 + sx * 0.012))
            c = (twinkle, int(twinkle * 0.85), min(255, twinkle + 30))
            pygame.draw.circle(screen, c, (sx, sy), size)

        glow = pygame.Surface((w, h), pygame.SRCALPHA)
        cx, cy = w // 2, int(h * 0.3)
        for radius, alpha in ((280, 18), (180, 28), (90, 40)):
            pygame.draw.circle(glow, (255, 200, 100, alpha), (cx, cy), radius)
        screen.blit(glow, (0, 0))

        vignette = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(vignette, (0, 0, 0, 110), (0, 0, w, 90))
        pygame.draw.rect(vignette, (0, 0, 0, 150), (0, h - 110, w, 110))
        screen.blit(vignette, (0, 0))

        border = pygame.Rect(24, 24, w - 48, h - 48)
        pygame.draw.rect(screen, (255, 190, 80), border, 2, border_radius=10)
