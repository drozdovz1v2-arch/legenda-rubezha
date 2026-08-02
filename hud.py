import math
import pygame
from config import WORLD_WIDTH, WORLD_HEIGHT, TILE_SIZE, TILE_COLORS


def _draw_rounded_panel(surface, rect, fill, border, radius=10, border_width=2, alpha=210):
    panel = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(panel, (*fill, alpha), (0, 0, rect.width, rect.height), border_radius=radius)
    pygame.draw.rect(panel, (*border, 255), (0, 0, rect.width, rect.height), border_width, border_radius=radius)
    pygame.draw.line(panel, (255, 255, 255, 28), (8, 2), (rect.width - 8, 2), 1)
    surface.blit(panel, rect.topleft)


def _draw_bar(screen, x, y, width, height, ratio, colors, radius=5):
    ratio = max(0.0, min(1.0, ratio))
    track_rect = pygame.Rect(x, y, width, height)
    pygame.draw.rect(screen, colors["track"], track_rect, border_radius=radius)
    pygame.draw.rect(screen, colors["border"], track_rect, 1, border_radius=radius)

    fill_width = max(0, int((width - 4) * ratio))
    if fill_width > 0:
        fill_rect = pygame.Rect(x + 2, y + 2, fill_width, height - 4)
        pygame.draw.rect(screen, colors["fill"], fill_rect, border_radius=max(2, radius - 2))
        shine = pygame.Rect(fill_rect.x, fill_rect.y, fill_rect.width, max(2, fill_rect.height // 3))
        pygame.draw.rect(screen, colors["shine"], shine, border_radius=max(1, radius - 3))


def _draw_heart(surface, cx, cy, size, color):
    points = []
    for deg in range(0, 360, 8):
        rad = math.radians(deg)
        x = 16 * (math.sin(rad) ** 3)
        y = -(13 * math.cos(rad) - 5 * math.cos(2 * rad) - 2 * math.cos(3 * rad) - math.cos(4 * rad))
        points.append((int(cx + x * size / 16), int(cy + y * size / 16)))
    if len(points) >= 3:
        pygame.draw.polygon(surface, color, points)
        pygame.draw.polygon(surface, (255, 255, 255, 80), points, 1)


def _draw_star(surface, cx, cy, radius, color):
    points = []
    for i in range(10):
        angle = math.radians(-90 + i * 36)
        r = radius if i % 2 == 0 else radius * 0.45
        points.append((cx + math.cos(angle) * r, cy + math.sin(angle) * r))
    pygame.draw.polygon(surface, color, points)


def _draw_coin(surface, cx, cy, radius):
    pygame.draw.circle(surface, (255, 210, 60), (cx, cy), radius)
    pygame.draw.circle(surface, (180, 130, 20), (cx, cy), radius, 2)
    pygame.draw.circle(surface, (255, 240, 160), (cx - radius // 3, cy - radius // 3), max(1, radius // 4))


_COIN_FONT = None


def _coin_font(radius):
    global _COIN_FONT
    size = max(8, radius)
    if _COIN_FONT is None or _COIN_FONT.get_height() != size:
        _COIN_FONT = pygame.font.SysFont("Arial", size, bold=True)
    return _COIN_FONT


def _draw_potion_icon(surface, cx, cy, filled=True):
    neck = pygame.Rect(cx - 3, cy - 10, 6, 5)
    pygame.draw.rect(surface, (180, 180, 200), neck, border_radius=2)
    pygame.draw.rect(surface, (120, 70, 30), (cx - 3, cy - 10, 6, 2))
    pygame.draw.ellipse(surface, (190, 195, 215), (cx - 7, cy - 5, 14, 16))
    if filled:
        pygame.draw.ellipse(surface, (220, 40, 90), (cx - 5, cy - 1, 10, 10))
        pygame.draw.circle(surface, (255, 255, 255), (cx - 3, cy), 2)


def _hp_color(ratio):
    if ratio > 0.55:
        t = (ratio - 0.55) / 0.45
        return (
            int(80 + 40 * t),
            int(200 + 55 * t),
            int(70 + 30 * t),
        )
    t = ratio / 0.55
    return (int(200 + 55 * (1 - t)), int(70 + 90 * t), int(60 + 20 * t))


class GameHUD:
    MARGIN = 14
    STATS_W = 304
    ABILITIES_H = 52
    ABILITIES_MARGIN = 16
    INTERACT_H = 26
    FEED_LINE_H = 22

    def __init__(self):
        self.font_title = pygame.font.SysFont("Arial", 17, bold=True)
        self.font_value = pygame.font.SysFont("Arial", 15, bold=True)
        self.font_label = pygame.font.SysFont("Arial", 13)
        self.font_hint = pygame.font.SysFont("Arial", 12)
        self.font_quest = pygame.font.SysFont("Arial", 14, bold=True)
        self.show_quest_log = False
        self.hp_flash = 0
        self.last_damage = 0
        self._minimap_base = None
        self._minimap_seed = None
        self._minimap_size = 130
        self._coin_icon = pygame.Surface((18, 18), pygame.SRCALPHA)
        _draw_coin(self._coin_icon, 9, 9, 7)
        coin_font = _coin_font(7)
        label = coin_font.render("G", True, (120, 80, 10))
        self._coin_icon.blit(label, label.get_rect(center=(9, 10)))
        self._potion_icon_full = pygame.Surface((20, 20), pygame.SRCALPHA)
        _draw_potion_icon(self._potion_icon_full, 10, 12, filled=True)
        self._potion_icon_empty = pygame.Surface((20, 20), pygame.SRCALPHA)
        _draw_potion_icon(self._potion_icon_empty, 10, 12, filled=False)
        self._stats_panel_bg = None
        self._cached_gold = -1
        self._cached_potions = -1
        self._gold_text = self.font_value.render("0", True, (255, 225, 90))
        self._potion_text = self.font_value.render("x0", True, (255, 150, 190))

    def invalidate_minimap_cache(self):
        self._minimap_base = None
        self._minimap_seed = None

    def ping_damage(self, amount):
        self.last_damage = int(amount)
        self.hp_flash = 22

    def update(self):
        if self.hp_flash > 0:
            self.hp_flash -= 1

    def _bottom_layout(self, sh, interact_hint=None):
        abilities_top = sh - self.ABILITIES_MARGIN - self.ABILITIES_H
        interact_top = None
        if interact_hint:
            interact_top = abilities_top - 8 - self.INTERACT_H
        feed_bottom = (interact_top - 8) if interact_top is not None else (abilities_top - 8)
        return abilities_top, interact_top, feed_bottom

    def draw(
        self, screen, player, quest_manager=None, tilemap=None, enemies_group=None,
        npcs_group=None, chests_group=None, camera=None, shrines_group=None,
        daynight=None, abilities=None, equipment=None, world_events=None,
        achievements=None, difficulty=None, interact_hint=None, combo_tracker=None,
        show_minimap=True, ui_scale=1.0, relics=None, synergies=None, run_mods=None,
    ):
        sw, sh = screen.get_size()
        scale = max(0.75, min(1.4, ui_scale))
        mx = int(self.MARGIN * scale)
        my = int(self.MARGIN * scale)
        _, interact_top, feed_bottom = self._bottom_layout(sh, interact_hint)
        left_max_y = feed_bottom - 10

        content_y = self._draw_stats_panel(screen, player, difficulty, mx, my)
        if content_y < left_max_y:
            content_y = self._draw_quest_strip(screen, quest_manager, mx, content_y, left_max_y)
        if content_y < left_max_y:
            content_y = self._draw_skill_strip(screen, player, mx, content_y, left_max_y)
        if content_y < left_max_y:
            content_y = self._draw_equipment_strip(screen, equipment, mx, content_y, left_max_y)
        if content_y < left_max_y:
            content_y = self._draw_status_strip(screen, player, mx, content_y, left_max_y)
        if content_y < left_max_y:
            content_y = self._draw_relic_strip(screen, relics, mx, content_y, left_max_y)
        if content_y < left_max_y:
            content_y = self._draw_synergy_strip(screen, synergies, mx, content_y, left_max_y)
        if run_mods and run_mods.active_id != "none" and content_y < left_max_y - 18:
            mod = run_mods.active
            mod_bg = pygame.Rect(mx, content_y, self.STATS_W, 18)
            _draw_rounded_panel(screen, mod_bg, (28, 22, 18), mod.get("color", (180, 190, 200)), radius=5, alpha=180)
            mod_txt = self.font_hint.render(f"Мод: {mod['name']}", True, mod.get("color", (200, 200, 210)))
            screen.blit(mod_txt, (mx + 8, content_y + 2))

        if show_minimap and tilemap and player:
            self._draw_minimap(screen, player, tilemap, enemies_group, npcs_group, chests_group, shrines_group)
        if show_minimap and daynight:
            mm_size = 130
            self._draw_daynight_clock(screen, daynight, sw - mm_size - self.MARGIN, my + mm_size + 6)

        self._draw_top_banners(screen, world_events)
        self._draw_notification_feed(
            screen, quest_manager, achievements, combo_tracker, mx, feed_bottom,
        )
        self.draw_interact_prompt(screen, interact_hint, sw, interact_top)
        self.draw_abilities(screen, abilities, player)

        if self.show_quest_log and quest_manager:
            self._draw_quest_log(screen, quest_manager, player)

    def _draw_stats_panel(self, screen, player, difficulty, x, y):
        panel_h = 132
        panel_rect = pygame.Rect(x, y, self.STATS_W, panel_h)
        _draw_rounded_panel(screen, panel_rect, (18, 22, 30), (0, 170, 170))

        hp_ratio = max(0.0, min(1.0, player.hp / player.max_hp))
        bar_x = x + 14
        bar_w = self.STATS_W - 28

        level_badge = pygame.Rect(x + 12, y + 10, 50, 26)
        badge_surf = pygame.Surface((level_badge.width, level_badge.height), pygame.SRCALPHA)
        pygame.draw.rect(badge_surf, (0, 120, 120, 180), badge_surf.get_rect(), border_radius=8)
        pygame.draw.rect(badge_surf, (0, 220, 220), badge_surf.get_rect(), 1, border_radius=8)
        badge_surf.blit(self.font_hint.render("LV", True, (160, 255, 255)), (8, 4))
        badge_surf.blit(self.font_title.render(str(player.level), True, (255, 255, 255)), (26, 1))
        screen.blit(badge_surf, level_badge.topleft)

        hp_label = self.font_label.render("HP", True, (190, 210, 220))
        hp_value = self.font_value.render(f"{int(player.hp)} / {player.max_hp}", True, (245, 245, 245))
        screen.blit(hp_label, (x + 72, y + 10))
        screen.blit(hp_value, (x + 72, y + 26))

        if difficulty is not None:
            threat_colors = {
                "I — Кровавый старт": (120, 220, 160),
                "II — Охота": (255, 210, 90),
                "III — Мясорубка": (255, 140, 80),
                "IV — Ад": (255, 90, 90),
                "V — Безумие": (255, 60, 120),
                "VI — Невозможно": (255, 40, 160),
            }
            threat = difficulty.threat_label
            threat_color = threat_colors.get(threat, (200, 200, 200))
            threat_bg = pygame.Rect(x + self.STATS_W - 112, y + 10, 100, 22)
            _draw_rounded_panel(screen, threat_bg, (28, 18, 24), threat_color, radius=6, alpha=210)
            wave_txt = self.font_hint.render(f"У{difficulty.wave}", True, threat_color)
            screen.blit(wave_txt, wave_txt.get_rect(center=(threat_bg.centerx, threat_bg.centery - 1)))

        if player.title:
            title_surf = self.font_hint.render(player.title[:18], True, (255, 215, 120))
            screen.blit(title_surf, (x + 72, y + 42))

        hp_colors = {
            "track": (35, 28, 32),
            "border": (120, 80, 80),
            "fill": _hp_color(hp_ratio),
            "shine": _hp_color(hp_ratio),
        }
        if self.hp_flash > 0:
            pulse = self.hp_flash / 22.0
            hp_colors["fill"] = (
                int(200 + 55 * pulse),
                int(60 + 40 * (1 - pulse)),
                int(60 + 30 * (1 - pulse)),
            )
        _draw_bar(screen, bar_x, y + 58, bar_w, 13, hp_ratio, hp_colors)

        if self.hp_flash > 0 and self.last_damage > 0:
            dmg_txt = self.font_hint.render(f"-{self.last_damage}", True, (255, 100, 100))
            screen.blit(dmg_txt, (bar_x + bar_w - dmg_txt.get_width(), y + 42))

        exp_ratio = max(0.0, min(1.0, player.exp / player.max_exp))
        exp_colors = {
            "track": (28, 22, 38),
            "border": (100, 70, 150),
            "fill": (130, 60, 210),
            "shine": (190, 130, 255),
        }
        _draw_bar(screen, bar_x, y + 78, bar_w, 11, exp_ratio, exp_colors, radius=4)
        exp_caption = self.font_hint.render(f"EXP {player.exp}/{player.max_exp}", True, (200, 175, 240))
        screen.blit(exp_caption, (bar_x, y + 90))
        remaining = max(0, player.max_exp - player.exp)
        lvl_hint = self.font_hint.render(
            f"до ур. {player.level + 1}: {remaining} exp", True, (160, 150, 190)
        )
        screen.blit(lvl_hint, (bar_x, y + 104))

        row_y = y + panel_h - 24
        screen.blit(self._coin_icon, (x + 14, row_y - 1))
        if self._cached_gold != player.gold:
            self._cached_gold = player.gold
            self._gold_text = self.font_value.render(str(player.gold), True, (255, 225, 90))
        screen.blit(self._gold_text, (x + 36, row_y - 2))

        potion_icon = self._potion_icon_full if player.potions_count > 0 else self._potion_icon_empty
        screen.blit(potion_icon, (x + 110, row_y - 2))
        if self._cached_potions != player.potions_count:
            self._cached_potions = player.potions_count
            self._potion_text = self.font_value.render(
                f"x{player.potions_count}", True, (255, 150, 190)
            )
        screen.blit(self._potion_text, (x + 132, row_y - 2))

        if player.spawn_protected:
            sec = max(1, player.spawn_iframes // 60)
            shield_txt = self.font_hint.render(f"Щит {sec}с", True, (120, 255, 200))
            screen.blit(shield_txt, (x + 190, row_y - 1))

        if hp_ratio <= 0.35:
            pulse = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() * 0.012)
            warn = pygame.Surface((bar_w, 2), pygame.SRCALPHA)
            warn.fill((255, 60, 60, int(80 + 100 * pulse)))
            screen.blit(warn, (bar_x, y + 56))

        return y + panel_h + 8

    def _draw_quest_strip(self, screen, quest_manager, x, y, max_y):
        if not quest_manager or not quest_manager.active_quest or self.show_quest_log:
            return y
        q_text = quest_manager.active_progress_text()
        if not q_text:
            return y
        if y + 24 > max_y:
            return y
        q_surf = self.font_quest.render(q_text, True, (255, 220, 120))
        bg_w = min(self.STATS_W, q_surf.get_width() + 20)
        q_bg = pygame.Rect(x, y, bg_w, 24)
        _draw_rounded_panel(screen, q_bg, (30, 28, 18), (180, 140, 40), radius=6, alpha=200)
        screen.blit(q_surf, (x + 10, y + 4))
        return y + 30

    def _draw_skill_strip(self, screen, player, x, y, max_y):
        from skills import SKILLS
        from assets import get_skill_icon
        if not player.skill_stacks:
            return y
        if y + 28 > max_y:
            return y
        lbl = self.font_hint.render("Скиллы", True, (140, 160, 180))
        bg = pygame.Rect(x, y, self.STATS_W, 28)
        _draw_rounded_panel(screen, bg, (16, 20, 28), (80, 100, 130), radius=6, alpha=190)
        screen.blit(lbl, (x + 8, y + 7))
        cx = x + 62
        icon_size = 20
        for skill_id, count in sorted(player.skill_stacks.items()):
            skill = SKILLS.get(skill_id)
            if not skill:
                continue
            icon = get_skill_icon(skill_id, icon_size)
            iy = y + 4
            screen.blit(icon, (cx, iy))
            if count > 1:
                badge = self.font_hint.render(str(count), True, (255, 255, 255))
                pygame.draw.circle(screen, skill["color"], (cx + icon_size - 2, iy + icon_size - 2), 6)
                screen.blit(badge, badge.get_rect(center=(cx + icon_size - 2, iy + icon_size - 2)))
            cx += icon_size + 6
        return y + 34

    def _draw_equipment_strip(self, screen, equipment, x, y, max_y):
        if not equipment:
            return y
        lines = equipment.summary_lines()
        if not lines:
            return y
        if y + 22 > max_y:
            return y
        text = " · ".join(line[:16] for line in lines[:2])
        bg = pygame.Rect(x, y, self.STATS_W, 22)
        _draw_rounded_panel(screen, bg, (16, 18, 28), (120, 90, 180), radius=6, alpha=190)
        screen.blit(self.font_hint.render(f"Экип: {text}", True, (200, 180, 255)), (x + 8, y + 4))
        return y + 28

    def _draw_status_strip(self, screen, player, x, y, max_y):
        labels = player.status.active_labels()
        if not labels:
            return y
        if y + 22 > max_y:
            return y
        parts = [label for label, _color, _dur in labels[:3]]
        text = " · ".join(parts)
        bg = pygame.Rect(x, y, self.STATS_W, 22)
        _draw_rounded_panel(screen, bg, (24, 16, 20), (200, 100, 100), radius=6, alpha=190)
        screen.blit(self.font_hint.render(text, True, (255, 180, 180)), (x + 8, y + 4))
        return y + 28

    def _draw_relic_strip(self, screen, relics, x, y, max_y):
        if not relics or not relics.collected:
            return y
        if y + 22 > max_y:
            return y
        from relics import RELICS
        names = [RELICS[rid]["name"][:10] for rid in relics.collected[:5]]
        suffix = f" +{len(relics.collected) - 5}" if len(relics.collected) > 5 else ""
        text = " · ".join(names) + suffix
        bg = pygame.Rect(x, y, self.STATS_W, 22)
        _draw_rounded_panel(screen, bg, (20, 18, 28), (160, 120, 255), radius=6, alpha=190)
        screen.blit(self.font_hint.render(f"Релик: {text}", True, (200, 180, 255)), (x + 8, y + 4))
        return y + 28

    def _draw_synergy_strip(self, screen, synergies, x, y, max_y):
        if not synergies or not synergies.active:
            return y
        if y + 22 > max_y:
            return y
        from skill_synergies import SYNERGIES
        names = []
        for syn in SYNERGIES:
            if syn["id"] in synergies.active:
                names.append(syn["name"][:12])
        if not names:
            return y
        text = " · ".join(names[:3])
        if len(names) > 3:
            text += "..."
        bg = pygame.Rect(x, y, self.STATS_W, 22)
        _draw_rounded_panel(screen, bg, (18, 24, 28), (80, 200, 220), radius=6, alpha=190)
        screen.blit(self.font_hint.render(f"⚡ {text}", True, (160, 230, 255)), (x + 8, y + 4))
        return y + 28

    def _draw_notification_feed(self, screen, quest_manager, achievements, combo_tracker, x, feed_bottom):
        notes = []
        if combo_tracker and combo_tracker.count >= 2:
            combo_txt = combo_tracker.bonus_text()
            if combo_txt:
                notes.append((combo_txt, 255, (255, 180, 80), True))
        if quest_manager:
            for note in quest_manager.notifications[-4:]:
                notes.append((note["text"], note["timer"], (230, 225, 190), False))
        if achievements and achievements.toast:
            notes.append((
                achievements.toast["text"],
                achievements.toast.get("timer", 120),
                (255, 220, 140),
                False,
            ))

        if not notes:
            return

        line_h = self.FEED_LINE_H
        feed_h = min(len(notes), 5) * line_h + 8
        feed_y = feed_bottom - feed_h
        feed_rect = pygame.Rect(x, feed_y, self.STATS_W + 40, feed_h)
        _draw_rounded_panel(screen, feed_rect, (14, 16, 22), (80, 90, 110), radius=8, alpha=200)

        cy = feed_y + 5
        for text, timer, color, is_combo in reversed(notes[-5:]):
            alpha = 255 if is_combo else min(255, max(80, timer * 3))
            surf = self.font_hint.render(text[:46], True, color)
            surf.set_alpha(alpha)
            screen.blit(surf, (x + 10, cy))
            cy += line_h

    def draw_interact_prompt(self, screen, hint, sw, interact_top):
        if not hint or interact_top is None:
            return
        surf = self.font_quest.render(hint, True, (255, 240, 180))
        bg = pygame.Rect(sw // 2 - surf.get_width() // 2 - 14, interact_top, surf.get_width() + 28, self.INTERACT_H)
        _draw_rounded_panel(screen, bg, (28, 24, 14), (255, 210, 80), radius=8, alpha=215)
        screen.blit(surf, surf.get_rect(center=bg.center))

    def _draw_top_banners(self, screen, world_events):
        if not world_events or not world_events.active:
            return
        text = world_events.banner_text()
        if not text:
            return
        sw, _ = screen.get_size()
        color = world_events.banner_color()
        desc = world_events.event_desc()
        banner_h = 42 if desc else 24
        surf = self.font_quest.render(text, True, color)
        bg = pygame.Rect(sw // 2 - surf.get_width() // 2 - 14, 8, surf.get_width() + 28, banner_h)
        _draw_rounded_panel(screen, bg, (30, 10, 20), color, radius=8, alpha=200)
        screen.blit(surf, surf.get_rect(center=(bg.centerx, bg.y + 12)))
        if desc:
            desc_surf = self.font_hint.render(desc, True, (210, 210, 220))
            screen.blit(desc_surf, desc_surf.get_rect(center=(bg.centerx, bg.y + 30)))

    def _draw_daynight_clock(self, screen, daynight, x, y):
        text = daynight.clock_text()
        surf = self.font_hint.render(text, True, (180, 200, 220) if not daynight.is_night else (180, 160, 255))
        bg = pygame.Rect(x, y, max(90, surf.get_width() + 16), 22)
        border = (120, 100, 180) if daynight.is_night else (0, 140, 140)
        _draw_rounded_panel(screen, bg, (20, 18, 30), border, radius=6, alpha=180)
        screen.blit(surf, (bg.x + 8, bg.y + 3))

    def draw_abilities(self, screen, abilities, player):
        from abilities import ABILITIES
        if not abilities:
            return
        sw, sh = screen.get_size()
        bar_w = 280
        bar_h = self.ABILITIES_H
        x = sw // 2 - bar_w // 2
        y = sh - self.ABILITIES_MARGIN - bar_h
        _draw_rounded_panel(screen, pygame.Rect(x, y, bar_w, bar_h), (16, 18, 28), (0, 160, 160), radius=10, alpha=210)
        slot_w = bar_w // 3
        inner_h = bar_h - 16
        for i, (aid, spec) in enumerate(ABILITIES.items()):
            sx = x + i * slot_w + 8
            slot_rect = pygame.Rect(sx, y + 8, slot_w - 16, inner_h)
            unlocked = abilities.is_unlocked(aid, player)
            ready = abilities.is_ready(aid, player)
            bg_color = (30, 30, 40) if unlocked else (20, 20, 25)
            if abilities.shield_active and aid == "arcane_shield":
                bg_color = (40, 70, 120)
            pygame.draw.rect(screen, bg_color, slot_rect, border_radius=8)
            border = spec["color"] if ready else (80, 80, 90)
            pygame.draw.rect(screen, border, slot_rect, 1, border_radius=8)
            name = self.font_hint.render(spec["key_hint"], True, spec["color"] if unlocked else (90, 90, 100))
            label = spec["name"][:10]
            lbl = self.font_hint.render(label, True, (200, 200, 210) if unlocked else (100, 100, 110))
            gap = 2
            text_h = name.get_height() + gap + lbl.get_height()
            text_top = slot_rect.y + (slot_rect.height - text_h) // 2
            screen.blit(name, (slot_rect.x + 8, text_top))
            screen.blit(lbl, (slot_rect.x + 8, text_top + name.get_height() + gap))
            if unlocked and abilities.cooldowns[aid] > 0:
                cd = self.font_hint.render(str(abilities.cooldowns[aid] // 10), True, (255, 100, 100))
                screen.blit(cd, (slot_rect.right - cd.get_width() - 6, slot_rect.y + 4))

    def _build_minimap_base(self, tilemap, size):
        surf = pygame.Surface((size, size))
        surf.fill((12, 16, 24))
        scale_x = size / WORLD_WIDTH
        scale_y = size / WORLD_HEIGHT
        sample_step = 5
        for gy in range(0, len(tilemap.matrix), sample_step):
            for gx in range(0, len(tilemap.matrix[0]), sample_step):
                tile_type = tilemap.matrix[gy][gx]
                color = TILE_COLORS.get(tile_type, (40, 40, 40))
                px = int(gx * TILE_SIZE * scale_x)
                py = int(gy * TILE_SIZE * scale_y)
                pw = max(1, int(TILE_SIZE * scale_x * sample_step) + 1)
                ph = max(1, int(TILE_SIZE * scale_y * sample_step) + 1)
                pygame.draw.rect(surf, color, (px, py, pw, ph))
        return surf

    def _get_minimap_base(self, tilemap):
        if self._minimap_base is None or self._minimap_seed != tilemap.seed:
            self._minimap_base = self._build_minimap_base(tilemap, self._minimap_size)
            self._minimap_seed = tilemap.seed
        return self._minimap_base

    def _draw_minimap(self, screen, player, tilemap, enemies_group, npcs_group, chests_group=None, shrines_group=None):
        sw, sh = screen.get_size()
        size = self._minimap_size
        margin = 14
        mm_rect = pygame.Rect(sw - size - margin, margin, size, size)
        _draw_rounded_panel(screen, mm_rect, (12, 16, 24), (0, 140, 140), radius=8, alpha=220)

        base = self._get_minimap_base(tilemap)
        screen.blit(base, mm_rect.topleft)

        scale_x = size / WORLD_WIDTH
        scale_y = size / WORLD_HEIGHT

        if npcs_group:
            for npc in npcs_group:
                nx = mm_rect.x + int(npc.rect.centerx * scale_x)
                ny = mm_rect.y + int(npc.rect.centery * scale_y)
                pygame.draw.circle(screen, npc.name_color, (nx, ny), 3)

        if chests_group:
            for chest in chests_group:
                if chest.opened:
                    continue
                cx = mm_rect.x + int(chest.rect.centerx * scale_x)
                cy = mm_rect.y + int(chest.rect.centery * scale_y)
                pygame.draw.rect(screen, (255, 200, 60), (cx - 2, cy - 2, 4, 4))

        if shrines_group:
            for shrine in shrines_group:
                if shrine.used:
                    continue
                sx = mm_rect.x + int(shrine.rect.centerx * scale_x)
                sy = mm_rect.y + int(shrine.rect.centery * scale_y)
                pygame.draw.polygon(
                    screen,
                    (190, 120, 255),
                    [(sx, sy - 3), (sx + 3, sy), (sx, sy + 3), (sx - 3, sy)],
                )

        if enemies_group:
            for enemy in enemies_group:
                ex = mm_rect.x + int(enemy.rect.centerx * scale_x)
                ey = mm_rect.y + int(enemy.rect.centery * scale_y)
                if enemy.__class__.__name__ == "IceGuardian":
                    color = (80, 200, 255)
                    radius = 3
                elif enemy.__class__.__name__ == "BlueBoss":
                    color = (80, 120, 255)
                    radius = 3
                elif getattr(enemy, "is_elite", False):
                    color = (255, 190, 60)
                    radius = 3
                elif enemy.__class__.__name__ == "FrostSlime":
                    color = (120, 200, 255)
                    radius = 2
                else:
                    color = (255, 80, 80)
                    radius = 2
                pygame.draw.circle(screen, color, (ex, ey), radius)

        px = mm_rect.x + int(player.rect.centerx * scale_x)
        py = mm_rect.y + int(player.rect.centery * scale_y)
        pygame.draw.circle(screen, (255, 255, 255), (px, py), 4)
        pygame.draw.circle(screen, (0, 255, 220), (px, py), 4, 1)

        lbl = self.font_hint.render("КАРТА", True, (140, 200, 200))
        screen.blit(lbl, (mm_rect.x + 6, mm_rect.bottom - 16))

    def _draw_quest_log(self, screen, quest_manager, player=None):
        from quests import QUESTS
        from skills import SKILLS

        sw, sh = screen.get_size()
        log_w, log_h = 400, 380
        log_rect = pygame.Rect((sw - log_w) // 2, (sh - log_h) // 2, log_w, log_h)
        _draw_rounded_panel(screen, log_rect, (16, 20, 30), (0, 180, 180), radius=12, alpha=235)

        title = self.font_quest.render("ЖУРНАЛ КВЕСТОВ", True, (0, 255, 220))
        screen.blit(title, (log_rect.x + 20, log_rect.y + 16))

        y = log_rect.y + 50
        if quest_manager.active_quest:
            q = QUESTS[quest_manager.active_quest]
            active = self.font_label.render(f"▶ {q['title']}: {quest_manager.progress.get(quest_manager.active_quest, 0)}/{q['target']}", True, (255, 220, 120))
            screen.blit(active, (log_rect.x + 20, y))
            obj = self.font_hint.render(q["objective"], True, (180, 180, 190))
            screen.blit(obj, (log_rect.x + 20, y + 20))
            y += 48

        for qid in quest_manager.completed:
            q = QUESTS[qid]
            done = self.font_label.render(f"✓ {q['title']}", True, (100, 200, 120))
            screen.blit(done, (log_rect.x + 20, y))
            y += 24

        for qid in quest_manager.available_quests():
            q = QUESTS[qid]
            avail = self.font_label.render(f"○ {q['title']}", True, (150, 150, 160))
            screen.blit(avail, (log_rect.x + 20, y))
            y += 22

        if player and player.skill_stacks:
            from assets import get_skill_icon
            y += 8
            sk_title = self.font_quest.render("АКТИВНЫЕ СКИЛЛЫ", True, (190, 130, 255))
            screen.blit(sk_title, (log_rect.x + 20, y))
            y += 28
            for skill_id, count in sorted(player.skill_stacks.items()):
                skill = SKILLS.get(skill_id)
                if not skill:
                    continue
                icon = get_skill_icon(skill_id, 18)
                screen.blit(icon, (log_rect.x + 20, y + 1))
                line = self.font_label.render(
                    f"{skill['name']} ({count}/{skill['max_stacks']})", True, skill["color"]
                )
                screen.blit(line, (log_rect.x + 44, y + 2))
                y += 24

        hint = self.font_hint.render("[Tab — закрыть]", True, (130, 140, 150))
        screen.blit(hint, (log_rect.centerx - hint.get_width() // 2, log_rect.bottom - 28))

    def draw_combo(self, screen, combo_tracker):
        """Сохранено для совместимости — комбо рисуется в draw()."""
        pass

    def draw_enemy_combat_hints(self, screen, camera, enemies_group):
        if not enemies_group:
            return
        for enemy in enemies_group:
            winding_up = (
                getattr(enemy, "lunge_timer", 0) > 14
                or getattr(enemy, "sting_timer", 0) > 11
                or getattr(enemy, "burst_timer", 0) > 0
            )
            if not winding_up:
                continue
            pos = camera.apply(enemy)
            mark = self.font_hint.render("!", True, (255, 70, 70))
            screen.blit(mark, (pos.centerx - mark.get_width() // 2, pos.top - 16))

    @staticmethod
    def _enemy_display_name(enemy):
        elite = getattr(enemy, "is_elite", False)
        names = {
            "Enemy": ("Слайм", "Элитный слайм"),
            "ForestWolf": ("Лесной волк", "Элитный волк"),
            "DesertScorpion": ("Скорпион", "Элитный скорпион"),
            "RuinWraith": ("Призрак руин", "Элитный призрак"),
            "FrostSlime": ("Ледяной слайм", "Элитный ледяной слайм"),
            "BlueBoss": ("Синий страж", "Синий страж"),
            "IceGuardian": ("Ледяной страж", "Ледяной страж"),
            "SandColossus": ("Песчаный колосс", "Песчаный колосс"),
        }
        normal, elite_name = names.get(enemy.__class__.__name__, ("Враг", "Элитный враг"))
        return elite_name if elite else normal

    def _draw_enemy_hp_bar(self, screen, screen_pos, enemy, bar_w=44, bar_h=5, show_elite_tag=False):
        max_hp = getattr(enemy, "max_hp", enemy.hp)
        if max_hp <= 0:
            return screen_pos.top - 14
        ratio = max(0.0, min(1.0, enemy.hp / max_hp))
        bx = screen_pos.centerx - bar_w // 2
        by = screen_pos.top - 14
        if enemy.__class__.__name__ == "IceGuardian":
            fill_color, border = (100, 200, 255), (180, 230, 255)
        elif enemy.__class__.__name__ == "BlueBoss":
            fill_color, border = (80, 120, 255), (140, 180, 255)
        elif enemy.__class__.__name__ == "SandColossus":
            fill_color, border = (200, 150, 80), (255, 210, 120)
        elif getattr(enemy, "is_elite", False):
            fill_color, border = (255, 190, 60), (255, 220, 120)
        else:
            fill_color, border = (220, 80, 80), (255, 140, 140)
        pygame.draw.rect(screen, (30, 30, 35), (bx - 1, by - 1, bar_w + 2, bar_h + 2), border_radius=3)
        pygame.draw.rect(screen, (20, 20, 25), (bx, by, bar_w, bar_h), border_radius=2)
        if ratio > 0:
            pygame.draw.rect(screen, fill_color, (bx, by, max(1, int(bar_w * ratio)), bar_h), border_radius=2)
        pygame.draw.rect(screen, border, (bx, by, bar_w, bar_h), 1, border_radius=2)
        label_y = by - 12
        if show_elite_tag and getattr(enemy, "is_elite", False):
            tag = self.font_hint.render("ЭЛИТА", True, (255, 200, 80))
            screen.blit(tag, (bx + bar_w // 2 - tag.get_width() // 2, label_y))
            label_y -= 12
        return label_y

    def draw_enemy_health_bars(self, screen, camera, enemies_group, mouse_pos=None):
        if not enemies_group:
            return
        hovered = None
        if mouse_pos:
            for enemy in enemies_group:
                screen_pos = camera.apply(enemy)
                if screen_pos.inflate(10, 12).collidepoint(mouse_pos):
                    hovered = enemy
                    break
        for enemy in enemies_group:
            show_bar = (
                enemy.__class__.__name__ in ("BlueBoss", "IceGuardian", "SandColossus")
                or getattr(enemy, "is_elite", False)
            )
            if not show_bar:
                continue
            screen_pos = camera.apply(enemy)
            bar_w = 44 if getattr(enemy, "is_elite", False) else 56
            bar_h = 5 if getattr(enemy, "is_elite", False) else 6
            label_y = self._draw_enemy_hp_bar(
                screen, screen_pos, enemy, bar_w=bar_w, bar_h=bar_h,
                show_elite_tag=enemy is not hovered,
            )
            if enemy is hovered:
                name = self.font_hint.render(self._enemy_display_name(enemy), True, (255, 245, 220))
                screen.blit(name, (screen_pos.centerx - name.get_width() // 2, label_y - 14))
        if hovered and not (
            hovered.__class__.__name__ in ("BlueBoss", "IceGuardian", "SandColossus")
            or getattr(hovered, "is_elite", False)
        ):
            screen_pos = camera.apply(hovered)
            label_y = self._draw_enemy_hp_bar(screen, screen_pos, hovered, bar_w=40, bar_h=4)
            name = self.font_hint.render(self._enemy_display_name(hovered), True, (255, 245, 220))
            screen.blit(name, (screen_pos.centerx - name.get_width() // 2, label_y - 14))
