import pygame


class DialogBox:
    def __init__(self):
        self.active = False
        self.speaker = ""
        self.lines = []
        self.line_index = 0
        self.choices = []
        self.choice_index = 0
        self.on_choice = None
        self._box_rect = None
        self._choice_rects = []
        self.font_speaker = pygame.font.SysFont("Arial", 20, bold=True)
        self.font_text = pygame.font.SysFont("Arial", 18)
        self.font_choice = pygame.font.SysFont("Arial", 17)

    def open(self, speaker, lines, choices=None, on_choice=None):
        self.active = True
        self.speaker = speaker
        self.lines = list(lines)
        self.line_index = 0
        self.choices = choices or []
        self.choice_index = 0
        self.on_choice = on_choice
        self._box_rect = None
        self._choice_rects = []

    def close(self):
        self.active = False
        self.lines = []
        self.choices = []
        self.on_choice = None
        self._box_rect = None
        self._choice_rects = []

    def advance(self):
        if self.choices:
            return
        if self.line_index < len(self.lines) - 1:
            self.line_index += 1
        else:
            self.close()

    def select_choice(self, index=None):
        if not self.choices:
            self.advance()
            return
        idx = self.choice_index if index is None else index
        idx = max(0, min(len(self.choices) - 1, idx))
        choice = self.choices[idx]
        callback = self.on_choice
        self.close()
        if callback:
            callback(choice.get("id"), choice)

    def handle_key(self, key):
        if not self.active:
            return False
        if self.choices:
            if key in (pygame.K_UP, pygame.K_w):
                self.choice_index = (self.choice_index - 1) % len(self.choices)
            elif key in (pygame.K_DOWN, pygame.K_s):
                self.choice_index = (self.choice_index + 1) % len(self.choices)
            elif key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_e):
                self.select_choice()
            elif key == pygame.K_ESCAPE:
                self.close()
            else:
                return False
        elif key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_e):
            self.advance()
        elif key == pygame.K_ESCAPE:
            self.close()
        else:
            return False
        return True

    def handle_click(self, pos):
        if not self.active:
            return False
        for idx, rect in self._choice_rects:
            if rect.collidepoint(pos):
                self.choice_index = idx
                self.select_choice(idx)
                return True
        if self._box_rect and self._box_rect.collidepoint(pos) and not self.choices:
            self.advance()
            return True
        if self._box_rect and self._box_rect.collidepoint(pos):
            return True
        return True

    def handle_event(self, event):
        if not self.active:
            return False
        if event.type == pygame.KEYDOWN:
            return self.handle_key(event.key)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.handle_click(event.pos)
        if event.type == pygame.MOUSEMOTION and self.choices:
            for idx, rect in self._choice_rects:
                if rect.collidepoint(event.pos):
                    self.choice_index = idx
                    break
        return event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEMOTION)

    def draw(self, screen, screen_w, screen_h):
        if not self.active:
            return

        mouse_pos = pygame.mouse.get_pos()
        overlay = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 90))
        screen.blit(overlay, (0, 0))

        box_h = 190 if self.choices else 140
        box = pygame.Rect(40, screen_h - box_h - 30, screen_w - 80, box_h)
        self._box_rect = box
        self._choice_rects = []

        panel = pygame.Surface((box.width, box.height), pygame.SRCALPHA)
        pygame.draw.rect(panel, (20, 24, 36, 230), (0, 0, box.width, box.height), border_radius=12)
        pygame.draw.rect(panel, (0, 180, 180, 255), (0, 0, box.width, box.height), 2, border_radius=12)
        screen.blit(panel, box.topleft)

        speaker_surf = self.font_speaker.render(self.speaker, True, (255, 215, 0))
        screen.blit(speaker_surf, (box.x + 20, box.y + 14))

        if self.lines:
            text = self.lines[min(self.line_index, len(self.lines) - 1)]
            text_surf = self.font_text.render(text, True, (230, 230, 240))
            screen.blit(text_surf, (box.x + 20, box.y + 46))

        if self.choices:
            for i, choice in enumerate(self.choices):
                y = box.y + 78 + i * 34
                rect = pygame.Rect(box.x + 16, y - 4, box.width - 32, 30)
                self._choice_rects.append((i, rect))
                selected = i == self.choice_index
                hovered = rect.collidepoint(mouse_pos)
                if selected or hovered:
                    pygame.draw.rect(screen, (0, 90, 90), rect, border_radius=6)
                    pygame.draw.rect(screen, (0, 220, 220), rect, 1, border_radius=6)
                color = (0, 255, 220) if selected else (180, 180, 190)
                prefix = "▶ " if selected else "  "
                label = self.font_choice.render(prefix + choice["label"], True, color)
                screen.blit(label, (rect.x + 8, rect.y + 5))
            hint = self.font_choice.render("[Клик / Enter / E]  ESC — закрыть", True, (130, 140, 150))
            screen.blit(hint, (box.x + 20, box.bottom - 28))
        else:
            hint = self.font_choice.render("[Клик / Enter / E — далее]  ESC — закрыть", True, (130, 140, 150))
            screen.blit(hint, (box.x + 20, box.bottom - 28))
