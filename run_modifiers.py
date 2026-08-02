"""Модификаторы забега — выбор перед стартом (как ascension)."""

import random
import pygame

from ui_theme import draw_rounded_panel

MODIFIERS = {
    "none": {
        "name": "Обычный",
        "desc": "Без модификаторов",
        "color": (180, 190, 200),
        "enemy_mult": 1.0,
        "player_hp_mult": 1.0,
        "gold_mult": 1.0,
        "soul_mult": 1.0,
        "elite_bonus": 0.0,
    },
    "hard": {
        "name": "Жёсткий",
        "desc": "Враги +25% HP и урона",
        "color": (255, 140, 80),
        "enemy_mult": 1.25,
        "player_hp_mult": 1.0,
        "gold_mult": 1.15,
        "soul_mult": 1.20,
        "elite_bonus": 0.04,
    },
    "nightmare": {
        "name": "Кошмар",
        "desc": "Враги +45%, игрок −15% HP",
        "color": (255, 80, 100),
        "enemy_mult": 1.45,
        "player_hp_mult": 0.85,
        "gold_mult": 1.30,
        "soul_mult": 1.45,
        "elite_bonus": 0.08,
    },
    "glass": {
        "name": "Стекло",
        "desc": "Ты +35% урона, −30% HP",
        "color": (200, 120, 255),
        "enemy_mult": 1.0,
        "player_hp_mult": 0.70,
        "player_dmg_mult": 1.35,
        "gold_mult": 1.0,
        "soul_mult": 1.15,
    },
    "greed": {
        "name": "Жадность",
        "desc": "+60% золота, +20% элит",
        "color": (255, 215, 0),
        "enemy_mult": 1.10,
        "gold_mult": 1.60,
        "soul_mult": 0.90,
        "elite_bonus": 0.10,
    },
    "swarm": {
        "name": "Рой",
        "desc": "+40% лимит врагов, быстрый респавн",
        "color": (120, 255, 160),
        "enemy_cap_mult": 1.40,
        "respawn_mult": 1.35,
        "soul_mult": 1.25,
    },
    "cursed": {
        "name": "Проклятый",
        "desc": "50% шанс проклятия при левел-апе",
        "color": (180, 60, 120),
        "curse_chance": 0.50,
        "soul_mult": 1.35,
        "gold_mult": 1.20,
    },
    "iron": {
        "name": "Железный",
        "desc": "+20% HP, −20% урона",
        "color": (160, 170, 190),
        "player_hp_mult": 1.20,
        "player_dmg_mult": 0.80,
        "soul_mult": 1.10,
    },
    "speedrun": {
        "name": "Бешеный",
        "desc": "День/ночь ×2, враги +15% скорости",
        "color": (100, 200, 255),
        "day_speed_mult": 2.0,
        "enemy_speed_mult": 1.15,
        "soul_mult": 1.30,
    },
    "legend": {
        "name": "Легенда",
        "desc": "Всё сложнее, ×2 душ",
        "color": (255, 215, 120),
        "enemy_mult": 1.35,
        "player_hp_mult": 0.90,
        "elite_bonus": 0.06,
        "gold_mult": 1.25,
        "soul_mult": 2.0,
    },
}


class RunModifierManager:
    def __init__(self):
        self.active_id = "none"

    def reset(self):
        self.active_id = "none"

    @property
    def active(self):
        return MODIFIERS.get(self.active_id, MODIFIERS["none"])

    def apply_to_player(self, player):
        spec = self.active
        hp_mult = spec.get("player_hp_mult", 1.0)
        if hp_mult != 1.0:
            player.max_hp_skill_bonus += int((player.max_hp - player.max_hp_skill_bonus) * (hp_mult - 1.0))
            player.recalc_max_hp()
            player.hp = min(player.hp, player.max_hp)
        dmg_mult = spec.get("player_dmg_mult", 1.0)
        if dmg_mult != 1.0:
            player.skill_attack_bonus += int(player.weapon_base_damage * (dmg_mult - 1.0))
            player.recalc_attack_damage()

    def apply_to_difficulty(self, difficulty):
        spec = self.active
        difficulty.run_enemy_mult = spec.get("enemy_mult", 1.0)

    def to_dict(self):
        return {"active_id": self.active_id}

    def load_dict(self, data):
        if not data:
            return
        aid = data.get("active_id", "none")
        if aid in MODIFIERS:
            self.active_id = aid


class ModifierPicker:
    ORDER = ["none", "hard", "nightmare", "glass", "greed", "swarm", "cursed", "iron", "speedrun", "legend"]

    def __init__(self):
        self.active = False
        self.selected = 0
        self._rects = []
        self.font_title = pygame.font.SysFont("Arial", 32, bold=True)
        self.font_name = pygame.font.SysFont("Arial", 18, bold=True)
        self.font_desc = pygame.font.SysFont("Arial", 14)
        self.font_hint = pygame.font.SysFont("Arial", 14)

    def open(self):
        self.active = True
        self.selected = 0
        self._rects = []

    def close(self):
        self.active = False

    def confirm(self, run_mods):
        mod_id = self.ORDER[self.selected]
        run_mods.active_id = mod_id
        self.close()
        return mod_id

    def handle_event(self, event, run_mods):
        if not self.active:
            return False
        n = len(self.ORDER)
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_LEFT, pygame.K_a):
                self.selected = (self.selected - 1) % n
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self.selected = (self.selected + 1) % n
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                return self.confirm(run_mods)
            elif event.key == pygame.K_ESCAPE:
                self.close()
                return "cancel"
            return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for idx, rect in self._rects:
                if rect.collidepoint(event.pos):
                    self.selected = idx
                    return self.confirm(run_mods)
        if event.type == pygame.MOUSEMOTION:
            for idx, rect in self._rects:
                if rect.collidepoint(event.pos):
                    self.selected = idx
        return True

    def draw(self, screen, w, h):
        if not self.active:
            return
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        title = self.font_title.render("МОДИФИКАТОРЫ ЗАБЕГА", True, (255, 215, 0))
        screen.blit(title, title.get_rect(center=(w // 2, int(h * 0.12))))
        sub = self.font_hint.render("Выбери испытание — награды растут с риском", True, (180, 200, 210))
        screen.blit(sub, sub.get_rect(center=(w // 2, int(h * 0.18))))
        cols = 5
        rows = 2
        card_w, card_h = 200, 110
        gap = 14
        grid_w = cols * card_w + (cols - 1) * gap
        start_x = (w - grid_w) // 2
        start_y = int(h * 0.28)
        self._rects = []
        mouse = pygame.mouse.get_pos()
        for i, mod_id in enumerate(self.ORDER):
            row, col = divmod(i, cols)
            rect = pygame.Rect(start_x + col * (card_w + gap), start_y + row * (card_h + gap), card_w, card_h)
            self._rects.append((i, rect))
            mod = MODIFIERS[mod_id]
            sel = i == self.selected
            hover = rect.collidepoint(mouse)
            panel = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
            bg = (*mod["color"], 50) if sel else (25, 28, 38, 220)
            pygame.draw.rect(panel, bg, panel.get_rect(), border_radius=10)
            border = mod["color"] if sel or hover else (70, 80, 90)
            pygame.draw.rect(panel, (*border, 255), panel.get_rect(), 3 if sel else 1, border_radius=10)
            screen.blit(panel, rect.topleft)
            name = self.font_name.render(mod["name"], True, (255, 255, 255))
            screen.blit(name, name.get_rect(midtop=(rect.centerx, rect.y + 10)))
            desc_lines = mod["desc"].split(", ")
            ty = rect.y + 36
            for line in desc_lines[:3]:
                ds = self.font_desc.render(line, True, (200, 205, 215))
                screen.blit(ds, ds.get_rect(midtop=(rect.centerx, ty)))
                ty += 18
            soul = mod.get("soul_mult", 1.0)
            if soul != 1.0:
                sm = self.font_desc.render(f"Души ×{soul:.2f}", True, (180, 140, 255))
                screen.blit(sm, sm.get_rect(midbottom=(rect.centerx, rect.bottom - 8)))
        hint = self.font_hint.render("← → / клик — выбрать   ·   Enter — начать", True, (130, 140, 150))
        screen.blit(hint, hint.get_rect(center=(w // 2, h - 36)))
