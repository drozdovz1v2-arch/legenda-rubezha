import random

import pygame



from assets import get_skill_icon

from skill_catalog import SKILLS, CURSED_SKILL_IDS, BLESSING_SKILL_IDS

from skill_effects import apply_skill_stack, reapply_all_skill_stacks

from ui_theme import draw_rounded_panel





def apply_skill_to_player(player, skill_id):

    """Применить один стак скилла к игроку."""

    skill = SKILLS.get(skill_id)

    if not skill:

        return False

    stacks = player.skill_stacks.get(skill_id, 0)

    if stacks >= skill["max_stacks"]:

        return False



    player.skill_stacks[skill_id] = stacks + 1

    apply_skill_stack(player, skill)

    return True





def roll_skill_offers(player, count=3, curse_chance=0.35):

    available = []

    for skill_id, skill in SKILLS.items():

        stacks = player.skill_stacks.get(skill_id, 0)

        if stacks < skill["max_stacks"]:

            available.append(skill_id)

    if not available:

        return []



    cursed_pool = [s for s in available if SKILLS[s].get("cursed")]

    bless_pool = [s for s in available if not SKILLS[s].get("cursed")]

    offers = []

    rng = random.Random()



    # Хардкор: ~35% шанс показать проклятие в одном из слотов

    if cursed_pool and rng.random() < curse_chance:

        offers.append(rng.choice(cursed_pool))



    pool = bless_pool if bless_pool else available

    while len(offers) < count and pool:

        pick = rng.choice(pool)

        if pick not in offers:

            offers.append(pick)

        if len(pool) > 1:

            pool = [s for s in pool if s not in offers] or bless_pool or available



    while len(offers) < count:

        rest = [s for s in available if s not in offers]

        if not rest:

            break

        offers.append(rng.choice(rest))



    rng.shuffle(offers)

    return offers[:count]





class SkillPicker:

    def __init__(self):

        self.active = False

        self.offers = []

        self.selected = 0

        self._card_rects = []

        self.font_title = pygame.font.SysFont("Arial", 34, bold=True)

        self.font_name = pygame.font.SysFont("Arial", 20, bold=True)

        self.font_desc = pygame.font.SysFont("Arial", 16)

        self.font_hint = pygame.font.SysFont("Arial", 15)

        self.font_stack = pygame.font.SysFont("Arial", 14)

        self.font_tag = pygame.font.SysFont("Arial", 12, bold=True)



    def open(self, player, curse_chance=0.35):

        self.offers = roll_skill_offers(player, curse_chance=curse_chance)

        self.active = bool(self.offers)

        self.selected = 0

        self._card_rects = []



    def close(self):

        self.active = False

        self.offers = []

        self._card_rects = []



    def confirm(self, player):

        if not self.offers:

            self.close()

            return None

        skill_id = self.offers[self.selected]

        apply_skill_to_player(player, skill_id)

        self.close()

        return skill_id



    def handle_key(self, key):

        if not self.active or not self.offers:

            return False

        n = len(self.offers)

        if key in (pygame.K_LEFT, pygame.K_a):

            self.selected = (self.selected - 1) % n

        elif key in (pygame.K_RIGHT, pygame.K_d):

            self.selected = (self.selected + 1) % n

        elif key in (pygame.K_UP, pygame.K_w):

            self.selected = (self.selected - 1) % n

        elif key in (pygame.K_DOWN, pygame.K_s):

            self.selected = (self.selected + 1) % n

        elif key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_e):

            return "confirm"

        elif key == pygame.K_1 and n >= 1:

            self.selected = 0

            return "confirm"

        elif key == pygame.K_2 and n >= 2:

            self.selected = 1

            return "confirm"

        elif key == pygame.K_3 and n >= 3:

            self.selected = 2

            return "confirm"

        else:

            return False

        return True



    def handle_click(self, pos):

        if not self.active:

            return False

        for idx, rect in self._card_rects:

            if rect.collidepoint(pos):

                self.selected = idx

                return "confirm"

        return True



    def handle_event(self, event):

        if not self.active:

            return False

        if event.type == pygame.KEYDOWN:

            result = self.handle_key(event.key)

            return result if result else True

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:

            return self.handle_click(event.pos) or True

        if event.type == pygame.MOUSEMOTION:

            for idx, rect in self._card_rects:

                if rect.collidepoint(event.pos):

                    self.selected = idx

                    break

        return event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEMOTION)



    def draw(self, screen, screen_w, screen_h, player):

        if not self.active:

            return

        overlay = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)

        overlay.fill((0, 0, 0, 205))

        screen.blit(overlay, (0, 0))

        if not self.offers:

            panel = pygame.Rect(screen_w // 2 - 220, screen_h // 2 - 60, 440, 120)

            draw_rounded_panel(screen, panel, (18, 22, 32), (255, 215, 0), radius=14, alpha=240)

            msg = self.font_desc.render("Все скиллы изучены!", True, (200, 200, 200))

            screen.blit(msg, msg.get_rect(center=panel.center))

            return

        card_w = min(220, max(160, (screen_w - 120) // len(self.offers) - 16))

        card_h = min(220, max(180, screen_h - 280))

        gap = 16

        total_w = len(self.offers) * card_w + (len(self.offers) - 1) * gap

        header_h = 72

        footer_h = 36

        panel_w = min(screen_w - 40, total_w + 48)

        panel_h = header_h + card_h + footer_h + 24

        panel = pygame.Rect((screen_w - panel_w) // 2, (screen_h - panel_h) // 2, panel_w, panel_h)

        draw_rounded_panel(screen, panel, (14, 18, 28), (255, 200, 80), radius=16, alpha=245)

        title = self.font_title.render("НОВЫЙ УРОВЕНЬ", True, (255, 215, 0))

        screen.blit(title, title.get_rect(midtop=(panel.centerx, panel.y + 14)))

        sub = self.font_hint.render(

            f"Уровень {player.level}  •  выбери один скилл",

            True, (180, 200, 210),

        )

        screen.blit(sub, sub.get_rect(midtop=(panel.centerx, panel.y + 48)))

        start_x = panel.x + (panel.width - total_w) // 2

        card_y = panel.y + header_h

        mouse_pos = pygame.mouse.get_pos()

        self._card_rects = []

        for i, skill_id in enumerate(self.offers):

            skill = SKILLS[skill_id]

            rect = pygame.Rect(start_x + i * (card_w + gap), card_y, card_w, card_h)

            self._card_rects.append((i, rect))

            selected = i == self.selected

            hovered = rect.collidepoint(mouse_pos)

            color = skill["color"]

            cursed = skill.get("cursed", False)

            card_panel = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)

            if cursed:

                bg = (60, 18, 28, 230) if selected else (35, 12, 18, 220)

            else:

                bg = (*color, 40) if selected else (30, 32, 45, 220)

            pygame.draw.rect(card_panel, bg, card_panel.get_rect(), border_radius=12)

            border_w = 3 if selected else 1

            border_c = (255, 80, 100) if cursed else (color if selected or hovered else (80, 90, 100))

            pygame.draw.rect(card_panel, (*border_c, 255), card_panel.get_rect(), border_w, border_radius=12)

            screen.blit(card_panel, rect.topleft)

            if selected:

                pygame.draw.rect(screen, border_c, rect, 2, border_radius=12)

            key_hint = self.font_stack.render(f"[{i + 1}]", True, color)

            screen.blit(key_hint, (rect.x + 12, rect.y + 10))

            if cursed:

                tag = self.font_tag.render("ПРОКЛЯТИЕ", True, (255, 120, 130))

                screen.blit(tag, tag.get_rect(midtop=(rect.centerx, rect.y + 8)))

            icon = get_skill_icon(skill_id, min(48, card_h // 5))

            icon_rect = icon.get_rect(midtop=(rect.centerx, rect.y + 26))

            screen.blit(icon, icon_rect)

            name = self.font_name.render(skill["name"], True, (255, 255, 255))

            screen.blit(name, name.get_rect(midtop=(rect.centerx, rect.y + 82)))

            desc_lines = _wrap_text(skill["desc"], self.font_desc, card_w - 24)

            ty = rect.y + 108

            for line in desc_lines[:3]:

                ds = self.font_desc.render(line, True, (210, 210, 220))

                screen.blit(ds, ds.get_rect(midtop=(rect.centerx, ty)))

                ty += 18

            stacks = player.skill_stacks.get(skill_id, 0)

            stack_txt = self.font_stack.render(

                f"Стак: {stacks}/{skill['max_stacks']}", True, (150, 160, 170)

            )

            screen.blit(stack_txt, stack_txt.get_rect(midbottom=(rect.centerx, rect.bottom - 10)))

        hint = self.font_hint.render(

            "← → / 1 2 3 / клик — выбрать",

            True, (130, 140, 150),

        )

        screen.blit(hint, hint.get_rect(midbottom=(panel.centerx, panel.bottom - 12)))





def _wrap_text(text, font, max_width):

    words = text.split()

    lines = []

    line = ""

    for word in words:

        test = (line + " " + word).strip()

        if font.size(test)[0] <= max_width:

            line = test

        else:

            if line:

                lines.append(line)

            line = word

    if line:

        lines.append(line)

    return lines or [text]


