"""Экран итогов забега + меню мета-талантов."""

import pygame

from ui_theme import draw_rounded_panel
from meta_progression import TALENTS, MetaProgression


def build_run_stats(game):
    return {
        "level": game.player.level,
        "kills": game.session_kills,
        "wave": game.difficulty.wave,
        "gold": game.player.gold,
        "relics": len(game.relics.collected),
        "quests_done": len(game.quests.completed),
        "combo_peak": game.combo.peak,
        "modifier": game.run_mods.active.get("name", "Обычный"),
        "synergies": len(game.synergies.active),
        "time_min": game.difficulty.play_time_frames // 3600,
    }


def draw_run_summary(screen, game, fonts, souls_earned):
    w, h = screen.get_size()
    font_lg, font_md, font_sm = fonts
    overlay = pygame.Surface((w, h))
    overlay.fill((12, 8, 18))
    overlay.set_alpha(220)
    screen.blit(overlay, (0, 0))
    stats = build_run_stats(game)
    title = font_lg.render("ЗАБЕГ ОКОНЧЕН", True, (220, 60, 70))
    screen.blit(title, title.get_rect(center=(w // 2, h * 0.10)))
    mod_txt = font_sm.render(f"Модификатор: {stats['modifier']}", True, (180, 170, 200))
    screen.blit(mod_txt, mod_txt.get_rect(center=(w // 2, h * 0.15)))
    panel = pygame.Rect(w // 2 - 280, int(h * 0.20), 560, 320)
    draw_rounded_panel(screen, panel, (18, 22, 32), (120, 80, 160), radius=14, alpha=235)
    lines = [
        f"Уровень: {stats['level']}",
        f"Убийств: {stats['kills']}",
        f"Волна угрозы: {stats['wave']}",
        f"Золото: {stats['gold']}",
        f"Реликвий: {stats['relics']}",
        f"Квестов: {stats['quests_done']}",
        f"Лучшее комбо: x{stats['combo_peak']}" if stats["combo_peak"] >= 2 else "Лучшее комбо: —",
        f"Синергий: {stats['synergies']}",
        f"Время: {stats['time_min']} мин",
        "",
        f"★ Душ получено: +{souls_earned}",
        f"Всего душ: {game.meta.souls}",
    ]
    y = panel.y + 20
    for line in lines:
        if not line:
            y += 8
            continue
        color = (255, 200, 120) if line.startswith("★") else (210, 210, 220)
        if line.startswith("Всего"):
            color = (180, 140, 255)
        surf = font_md.render(line, True, color) if line.startswith("★") else font_sm.render(line, True, color)
        screen.blit(surf, (panel.x + 24, y))
        y += 24 if line.startswith("★") else 22
    if game.relics.collected:
        relic_line = "Реликвии: " + ", ".join(
            game.relics.collected[:4]
        ) + ("..." if len(game.relics.collected) > 4 else "")
        rs = font_sm.render(relic_line[:60], True, (160, 200, 255))
        screen.blit(rs, (panel.x + 24, panel.bottom - 36))
    return panel.bottom


class MetaMenu:
    def __init__(self):
        self.active = False
        self.selected = 0
        self.scroll = 0
        self._rects = []
        self.font_title = pygame.font.SysFont("Arial", 30, bold=True)
        self.font_name = pygame.font.SysFont("Arial", 17, bold=True)
        self.font_desc = pygame.font.SysFont("Arial", 14)
        self.font_hint = pygame.font.SysFont("Arial", 14)
        self.talent_ids = list(TALENTS.keys())

    def open(self):
        self.active = True
        self.selected = 0
        self.scroll = 0

    def close(self):
        self.active = False

    def handle_event(self, event, meta):
        if not self.active:
            return False
        n = len(self.talent_ids)
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.selected = (self.selected - 1) % n
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.selected = (self.selected + 1) % n
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                tid = self.talent_ids[self.selected]
                if meta.buy_talent(tid):
                    return "bought"
            elif event.key == pygame.K_ESCAPE:
                self.close()
                return "close"
            return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for idx, rect in self._rects:
                if rect.collidepoint(event.pos):
                    self.selected = idx
                    if meta.buy_talent(self.talent_ids[idx]):
                        return "bought"
        return True

    def draw(self, screen, w, h, meta):
        if not self.active:
            return
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190))
        screen.blit(overlay, (0, 0))
        title = self.font_title.render("ДРЕВО ДУШ", True, (180, 140, 255))
        screen.blit(title, title.get_rect(center=(w // 2, 40)))
        souls = self.font_name.render(f"Душ: {meta.souls}  ·  Забегов: {meta.lifetime_runs}", True, (255, 220, 140))
        screen.blit(souls, souls.get_rect(center=(w // 2, 72)))
        panel = pygame.Rect(w // 2 - 300, 100, 600, h - 180)
        draw_rounded_panel(screen, panel, (16, 18, 28), (100, 80, 160), radius=12, alpha=240)
        self._rects = []
        y = panel.y + 12
        for i, tid in enumerate(self.talent_ids):
            talent = TALENTS[tid]
            rank = meta.talent_rank(tid)
            rect = pygame.Rect(panel.x + 12, y, panel.width - 24, 52)
            self._rects.append((i, rect))
            sel = i == self.selected
            bg = (40, 30, 60) if sel else (25, 28, 38)
            pygame.draw.rect(screen, bg, rect, border_radius=8)
            if sel:
                pygame.draw.rect(screen, (160, 120, 255), rect, 2, border_radius=8)
            can = meta.can_buy(tid)
            name_c = (255, 255, 255) if can or rank > 0 else (140, 140, 150)
            name = self.font_name.render(
                f"{talent['name']}  [{rank}/{talent['max_rank']}]", True, name_c
            )
            screen.blit(name, (rect.x + 10, rect.y + 6))
            desc = self.font_desc.render(talent["desc"], True, (170, 175, 185))
            screen.blit(desc, (rect.x + 10, rect.y + 28))
            cost = self.font_desc.render(f"{talent['cost']} душ", True, (255, 200, 100) if can else (100, 100, 110))
            screen.blit(cost, cost.get_rect(right=rect.right - 10, centery=rect.centery))
            y += 56
            if y > panel.bottom - 60:
                break
        hint = self.font_hint.render("↑↓ — выбор  ·  Enter — купить  ·  Esc — назад", True, (120, 130, 145))
        screen.blit(hint, hint.get_rect(center=(w // 2, h - 30)))
