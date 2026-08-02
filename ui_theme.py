"""Общие UI-компоненты: меню, кнопки, фоны."""

import math
import random
import pygame


class AnimatedBackground:
    def __init__(self, seed=7):
        self.phase = 0.0
        rng = random.Random(seed)
        self.stars = [
            (rng.randint(0, 1920), rng.randint(0, 1080), rng.randint(1, 3), rng.random() * 6.28)
            for _ in range(120)
        ]
        self.orbs = [
            (rng.randint(100, 900), rng.randint(80, 500), rng.randint(80, 160), rng.choice([(0, 180, 180), (180, 120, 255), (255, 180, 80)]))
            for _ in range(4)
        ]

    def update(self):
        self.phase += 0.015

    def draw(self, screen, w, h):
        for y in range(0, h, 4):
            t = y / max(1, h)
            color = (
                int(12 + 8 * t),
                int(14 + 12 * t),
                int(24 + 18 * t),
            )
            pygame.draw.rect(screen, color, (0, y, w, 4))

        for x, y, size, twinkle in self.stars:
            sx = (x * w) // 1920
            sy = (y * h) // 1080
            alpha = int(120 + 80 * math.sin(self.phase * 2 + twinkle))
            pygame.draw.circle(screen, (alpha, alpha, min(255, alpha + 40)), (sx, sy), size)

        for ox, oy, radius, color in self.orbs:
            px = ox + int(math.sin(self.phase + ox * 0.01) * 30)
            py = oy + int(math.cos(self.phase * 0.8 + oy * 0.01) * 20)
            px = int(px * w / 1280)
            py = int(py * h / 720)
            r = int(radius * min(w, h) / 900)
            glow = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow, (*color, 18), (r, r), r)
            screen.blit(glow, (px - r, py - r))

        vignette = pygame.Surface((w, h), pygame.SRCALPHA)
        for edge in range(0, 80, 4):
            alpha = int(edge * 0.55)
            pygame.draw.rect(vignette, (0, 0, 0, alpha), (0, edge, w, 4))
            pygame.draw.rect(vignette, (0, 0, 0, alpha), (0, h - edge - 4, w, 4))
            pygame.draw.rect(vignette, (0, 0, 0, alpha), (edge, 0, 4, h))
            pygame.draw.rect(vignette, (0, 0, 0, alpha), (w - edge - 4, 0, 4, h))
        screen.blit(vignette, (0, 0))


def draw_rounded_panel(screen, rect, fill, border=None, radius=10, alpha=230):
    surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(surf, (*fill, alpha), surf.get_rect(), border_radius=radius)
    if border:
        pygame.draw.rect(surf, (*border, min(255, alpha + 25)), surf.get_rect(), 2, border_radius=radius)
    screen.blit(surf, rect.topleft)


def _clip_render(font, text, color, max_width):
    surf = font.render(text, True, color)
    if surf.get_width() <= max_width:
        return surf
    ellipsis = "..."
    trimmed = text
    while trimmed and font.size(trimmed + ellipsis)[0] > max_width:
        trimmed = trimmed[:-1]
    return font.render((trimmed + ellipsis) if trimmed else ellipsis, True, color)


def draw_menu_button(screen, rect, label, font_title, font_sub, selected=False, hovered=False, locked=False, subtitle="", badge=""):
    if locked:
        fill, border, text_color = (32, 30, 38), (65, 68, 78), (95, 98, 108)
        sub_color = (80, 85, 95)
    elif selected:
        fill, border, text_color = (14, 38, 46), (0, 255, 220), (255, 255, 255)
        sub_color = (170, 195, 205)
    elif hovered:
        fill, border, text_color = (18, 34, 42), (0, 200, 195), (240, 248, 255)
        sub_color = (170, 195, 205)
    else:
        fill, border, text_color = (20, 24, 34), (0, 120, 130), (200, 210, 220)
        sub_color = (130, 150, 165)

    alpha = 175 if locked else 225
    draw_rounded_panel(screen, rect, fill, border, radius=12, alpha=alpha)

    if selected and not locked:
        glow = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        pygame.draw.rect(glow, (0, 255, 220, 22), glow.get_rect(), border_radius=12)
        screen.blit(glow, rect.topleft)
        mark_h = max(14, rect.height - 16)
        pygame.draw.rect(screen, (0, 255, 220), (rect.left + 5, rect.centery - mark_h // 2, 3, mark_h), border_radius=2)

    pad_x = 18
    pad_y = 8
    badge_w = 48 if badge and not locked else 0
    max_text_w = max(80, rect.width - pad_x * 2 - badge_w)

    title = _clip_render(font_title, label, text_color, max_text_w)

    if badge and not locked:
        badge_rect = pygame.Rect(rect.right - 56, rect.centery - 11, 44, 22)
        draw_rounded_panel(screen, badge_rect, (40, 34, 18), (255, 200, 80), radius=6, alpha=200)
        badge_surf = font_sub.render(badge, True, (255, 220, 120))
        screen.blit(badge_surf, badge_surf.get_rect(center=badge_rect.center))

    if subtitle:
        sub = _clip_render(font_sub, subtitle, sub_color, max_text_w)
        gap = 2
        block_h = title.get_height() + gap + sub.get_height()
        top = rect.centery - block_h // 2
        top = max(rect.top + pad_y, min(top, rect.bottom - pad_y - block_h))
        screen.blit(title, (rect.left + pad_x, top))
        screen.blit(sub, (rect.left + pad_x, top + title.get_height() + gap))
    else:
        screen.blit(title, title.get_rect(midleft=(rect.left + pad_x, rect.centery)))


def draw_title_header(screen, w, h, title, version, font_large, font_small, tagline=None):
    cx = w // 2
    title_y = max(72, int(h * 0.11))
    pulse = 0.92 + 0.08 * math.sin(pygame.time.get_ticks() * 0.002)

    title_surf = font_large.render(title, True, (255, 220, 80))
    shadow = font_large.render(title, True, (80, 55, 0))
    title_rect = title_surf.get_rect(center=(cx, title_y))
    screen.blit(shadow, title_rect.move(3, 3))
    screen.blit(title_surf, title_rect)

    line_y = title_rect.bottom + 14
    line_w = min(w - 120, title_surf.get_width() + 60)
    pygame.draw.line(screen, (0, 120, 130), (cx - line_w // 2, line_y), (cx - line_w // 4, line_y), 1)
    pygame.draw.line(screen, (0, 220, 210), (cx - line_w // 4, line_y), (cx + line_w // 4, line_y), 2)
    pygame.draw.line(screen, (0, 120, 130), (cx + line_w // 4, line_y), (cx + line_w // 2, line_y), 1)

    ver_text = font_small.render(version, True, (160, 230, 230))
    ver_pad_x, ver_pad_y = 14, 5
    ver_w = ver_text.get_width() + ver_pad_x * 2
    ver_h = ver_text.get_height() + ver_pad_y * 2
    ver_rect = pygame.Rect(cx - ver_w // 2, line_y + 10, ver_w, ver_h)
    draw_rounded_panel(screen, ver_rect, (16, 28, 32), (0, 170, 170), radius=8, alpha=int(210 * pulse))
    screen.blit(ver_text, ver_text.get_rect(center=ver_rect.center))

    if tagline:
        tag = font_small.render(tagline, True, (130, 145, 165))
        screen.blit(tag, tag.get_rect(center=(cx, ver_rect.bottom + 16)))


def draw_meta_chip(screen, rect, souls, runs, font):
    draw_rounded_panel(screen, rect, (22, 18, 32), (160, 120, 255), radius=10, alpha=215)
    text = font.render(f"★ {souls}", True, (255, 220, 140))
    if runs > 0:
        sub = font.render(f"{runs} забегов", True, (150, 140, 180))
        screen.blit(text, (rect.x + 12, rect.y + 7))
        screen.blit(sub, (rect.x + 12, rect.y + 24))
    else:
        screen.blit(text, text.get_rect(center=rect.center))


def draw_menu_panel(screen, rect):
    draw_rounded_panel(screen, rect, (12, 16, 24), (0, 130, 140), radius=16, alpha=195)
    shine = pygame.Surface((rect.width - 24, 2), pygame.SRCALPHA)
    shine.fill((255, 255, 255, 24))
    screen.blit(shine, (rect.x + 12, rect.y + 8))


def draw_menu_footer(screen, w, h, font):
    hint = font.render("↑↓  Enter  ·  мышь", True, (90, 100, 115))
    screen.blit(hint, hint.get_rect(center=(w // 2, h - 22)))


def draw_controls_card(screen, rect, font_title, font_sub, lines):
    draw_rounded_panel(screen, rect, (16, 20, 30), (0, 150, 160), radius=12, alpha=200)
    hdr = font_title.render("УПРАВЛЕНИЕ", True, (0, 255, 220))
    screen.blit(hdr, (rect.x + 16, rect.y + 14))
    y = rect.y + 42
    for key, action in lines:
        key_s = font_sub.render(key, True, (255, 215, 100))
        act_s = font_sub.render(action, True, (170, 180, 195))
        screen.blit(key_s, (rect.x + 16, y))
        screen.blit(act_s, (rect.x + 90, y))
        y += 22


def draw_save_badge(screen, rect, font_sub, player=None):
    if not player:
        return
    text = f"LV {player.level}  ·  {player.gold} G  ·  {player.title or 'Странник'}"
    draw_rounded_panel(screen, rect, (28, 24, 18), (180, 140, 40), radius=8, alpha=210)
    surf = font_sub.render(text, True, (255, 230, 160))
    screen.blit(surf, surf.get_rect(center=rect.center))
