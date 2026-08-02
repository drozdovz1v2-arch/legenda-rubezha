import math
import pygame

LORE_PAGES = [
    {
        "title": "Хроники Рубежа",
        "lines": [
            "Древний Рубеж — земля между тремя мирами.",
            "Лес, пустыня и ледяные вершины сходятся",
            "в одном проклятом королевстве.",
        ],
        "accent": (255, 215, 0),
    },
    {
        "title": "Падение границ",
        "lines": [
            "Когда стены между биомами рухнули,",
            "из трещин выползли слаймы, стражи пустыни",
            "и ледяные твари с севера.",
        ],
        "accent": (0, 220, 220),
    },
    {
        "title": "Рыцарь без имени",
        "lines": [
            "Ты — странник в потёртых доспехах.",
            "Старейшина ждёт на площади деревни.",
            "Он знает, с чего начать твой путь.",
        ],
        "accent": (180, 140, 255),
    },
    {
        "title": "Твоя история",
        "lines": [
            "Очисти лес. Победи стражей пустыни.",
            "Покори ледяную вершину.",
            "Стань Стражем Рубежа.",
        ],
        "accent": (120, 220, 255),
    },
    {
        "title": "Пробуждение мира",
        "lines": [
            "Мир дышит циклом дня и ночи.",
            "Ночью пробуждаются элиты и события.",
            "В руинах юго-запада — древняя сила.",
        ],
        "accent": (180, 120, 255),
    },
    {
        "title": "Наследие героя",
        "lines": [
            "Собирай экипировку. Осваивай способности.",
            "Q — огонь, R — щит, 1 — молния.",
            "Стань легендой Рубежа.",
        ],
        "accent": (255, 180, 80),
    },
]

class IntroScreen:
    FADE_SPEED = 6
    CHAR_DELAY = 28

    def __init__(self):
        self.active = False
        self.page_index = 0
        self.fade = 0
        self.elapsed = 0
        self.reveal_chars = 0
        self.font_title = pygame.font.SysFont("Arial", 42, bold=True)
        self.font_sub = pygame.font.SysFont("Arial", 22)
        self.font_hint = pygame.font.SysFont("Arial", 16)
        self.font_chapter = pygame.font.SysFont("Arial", 14, bold=True)
        self._stars = [(0, 0, 1) for _ in range(80)]

    def start(self):
        self.active = True
        self.page_index = 0
        self.fade = 0
        self.elapsed = 0
        self.reveal_chars = 0
        self._build_stars(1280, 720)

    def _build_stars(self, w, h):
        import random
        rng = random.Random(7)
        self._stars = [
            (rng.randint(0, w), rng.randint(0, h), rng.randint(1, 3))
            for _ in range(90)
        ]

    def current_page(self):
        if self.page_index < len(LORE_PAGES):
            return LORE_PAGES[self.page_index]
        return LORE_PAGES[-1]

    def full_text(self):
        page = self.current_page()
        return " ".join(page["lines"])

    def skip(self):
        self.active = False

    def advance(self):
        if self.page_index >= len(LORE_PAGES) - 1:
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
        target = min(total, self.elapsed // 2)
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

        chapter = self.font_chapter.render(f"ГЛАВА {self.page_index + 1} / {len(LORE_PAGES)}", True, page["accent"])
        chapter.set_alpha(alpha)
        screen.blit(chapter, chapter.get_rect(center=(screen_w // 2, screen_h * 0.18)))

        title = self.font_title.render(page["title"], True, accent)
        title.set_alpha(alpha)
        screen.blit(title, title.get_rect(center=(screen_w // 2, screen_h * 0.28)))

        text = self.full_text()[: self.reveal_chars]
        y = screen_h * 0.42
        line_w = int(screen_w * 0.62)
        words = text.split(" ")
        line = ""
        for word in words:
            test = (line + " " + word).strip()
            surf_test = self.font_sub.render(test, True, (230, 230, 240))
            if surf_test.get_width() > line_w and line:
                line_surf = self.font_sub.render(line, True, (230, 230, 240))
                line_surf.set_alpha(alpha)
                screen.blit(line_surf, line_surf.get_rect(center=(screen_w // 2, y)))
                y += 34
                line = word
            else:
                line = test
        if line:
            line_surf = self.font_sub.render(line, True, (230, 230, 240))
            line_surf.set_alpha(alpha)
            screen.blit(line_surf, line_surf.get_rect(center=(screen_w // 2, y)))

        for i in range(len(LORE_PAGES)):
            cx = screen_w // 2 - (len(LORE_PAGES) - 1) * 10 + i * 20
            cy = int(screen_h * 0.72)
            color = accent if i == self.page_index else (80, 80, 90)
            pygame.draw.circle(screen, color, (cx, cy), 5 if i == self.page_index else 3)

        pulse = 0.6 + 0.4 * math.sin(pygame.time.get_ticks() * 0.004)
        hint_text = "Enter / E / клик — далее    ESC — пропустить"
        if self.reveal_chars < len(self.full_text()):
            hint_text = "Enter / E / клик — показать текст"
        hint = self.font_hint.render(hint_text, True, (140, 150, 160))
        hint.set_alpha(int(180 + 60 * pulse))
        screen.blit(hint, hint.get_rect(center=(screen_w // 2, screen_h - 48)))

        skip = self.font_hint.render("Пропустить заставку", True, (100, 110, 120))
        skip_rect = skip.get_rect(topright=(screen_w - 24, 20))
        screen.blit(skip, skip_rect)

    def _draw_background(self, screen, w, h):
        for y in range(h):
            t = y / max(1, h)
            color = (
                int(12 + 18 * t),
                int(14 + 22 * t),
                int(28 + 35 * t),
            )
            pygame.draw.line(screen, color, (0, y), (w, y))

        tick = pygame.time.get_ticks() * 0.0003
        for sx, sy, size in self._stars:
            twinkle = int(120 + 80 * math.sin(tick * 4 + sx * 0.01))
            c = (twinkle, twinkle, min(255, twinkle + 40))
            pygame.draw.circle(screen, c, (sx, sy), size)

        vignette = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(vignette, (0, 0, 0, 100), (0, 0, w, 80))
        pygame.draw.rect(vignette, (0, 0, 0, 140), (0, h - 100, w, 100))
        screen.blit(vignette, (0, 0))

        border = pygame.Rect(30, 30, w - 60, h - 60)
        pygame.draw.rect(screen, (0, 120, 120), border, 1, border_radius=8)
