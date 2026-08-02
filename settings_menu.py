import pygame

from game_settings import (
    QUALITY_LABELS,
    FPS_LABELS,
    FPS_OPTIONS,
    DAY_SPEED_LABELS,
    DAY_SPEED_OPTIONS,
    UI_SCALE_LABELS,
    UI_SCALE_OPTIONS,
    SETTINGS_TABS,
    SETTING_DEFAULTS,
    build_resolution_list,
    resolve_res_index,
    format_resolution_label,
)
from ui_theme import draw_rounded_panel


class SettingsMenu:
    SCROLL_STEP = 36
    DROPDOWN_VISIBLE = 12
    DROPDOWN_ITEM_H = 28

    TAB_HEIGHT = 32
    TAB_GAP = 8
    HEADER_H = 100

    def __init__(self):
        self.tab = "audio"
        self.scroll = 0
        self.active_slider = None
        self.dropdown_open = False
        self.res_dropdown_scroll = 0
        self.buttons = {}
        self.dropdown_rects = []
        self.font_title = pygame.font.SysFont("Arial", 34, bold=True)
        self.font_section = pygame.font.SysFont("Arial", 15, bold=True)
        self.font_label = pygame.font.SysFont("Arial", 14)
        self.font_small = pygame.font.SysFont("Arial", 13)
        self.font_tab = pygame.font.SysFont("Arial", 14, bold=True)
        self._panel = pygame.Rect(0, 0, 0, 0)
        self._layout = {}

    def _make_layout(self, panel):
        inner_w = panel.width - 48
        slider_w = min(300, max(180, inner_w // 2))
        return {
            "label_x": panel.x + 24,
            "slider_x": panel.x + panel.width - slider_w - 24,
            "slider_w": slider_w,
            "toggle_x": panel.right - 50,
            "btn_x": panel.x + panel.width - min(200, inner_w // 2) - 24,
            "btn_w": min(200, inner_w // 2),
            "quality_x": panel.x + 160,
            "quality_btn_w": min(96, max(72, (panel.width - 200) // 3 - 8)),
        }

    def reset_scroll(self):
        self.scroll = 0
        self.dropdown_open = False
        self.res_dropdown_scroll = 0
        self.active_slider = None

    def _desktop_size(self):
        info = pygame.display.Info()
        return (info.current_w, info.current_h)

    def _panel_rect(self, screen_w, screen_h):
        margin = 28
        top = self.HEADER_H + 8
        return pygame.Rect(margin, top, screen_w - margin * 2, screen_h - top - 68)

    def _content_top(self, panel_top):
        return panel_top + 14 - self.scroll

    def _visible_height(self, panel):
        return panel.height - 28

    def _layout_tabs(self, sw):
        tab_y = 58
        count = len(SETTINGS_TABS)
        total_w = sw - 80
        tab_w = max(90, (total_w - (count - 1) * self.TAB_GAP) // count)
        row_w = tab_w * count + self.TAB_GAP * (count - 1)
        start_x = (sw - row_w) // 2
        rects = []
        for i, (tab_id, label) in enumerate(SETTINGS_TABS):
            rect = pygame.Rect(start_x + i * (tab_w + self.TAB_GAP), tab_y, tab_w, self.TAB_HEIGHT)
            rects.append((tab_id, label, rect))
        return rects

    def draw(self, screen, game):
        sw, sh = screen.get_size()
        mouse = pygame.mouse.get_pos()
        self.buttons = {}

        screen.fill((22, 20, 30))
        title = self.font_title.render("НАСТРОЙКИ", True, (0, 220, 210))
        screen.blit(title, title.get_rect(center=(sw // 2, 30)))

        for tab_id, label, rect in self._layout_tabs(sw):
            active = self.tab == tab_id
            fill = (0, 110, 110) if active else (40, 38, 52)
            border = (0, 220, 210) if active else (80, 80, 95)
            draw_rounded_panel(screen, rect, fill, border, radius=6, alpha=230)
            tab_surf = self.font_tab.render(label, True, (255, 255, 255) if active else (180, 180, 190))
            screen.blit(tab_surf, tab_surf.get_rect(center=rect.center))
            self.buttons[f"tab_{tab_id}"] = rect

        panel = self._panel_rect(sw, sh)
        self._panel = panel
        self._layout = self._make_layout(panel)
        draw_rounded_panel(screen, panel, (18, 20, 28), (60, 70, 90), radius=10, alpha=220)

        clip = screen.get_clip()
        screen.set_clip(panel.inflate(0, -4))
        y = self._content_top(panel.y)
        if self.tab == "audio":
            y = self._draw_audio(screen, game, y)
        elif self.tab == "graphics":
            y = self._draw_graphics(screen, game, y)
        elif self.tab == "gameplay":
            y = self._draw_gameplay(screen, game, y)
        elif self.tab == "interface":
            y = self._draw_interface(screen, game, y)
        self._content_height = y - self._content_top(panel.y)
        screen.set_clip(clip)

        max_scroll = max(0, getattr(self, "_content_height", 0) - self._visible_height(panel))
        self.scroll = max(0, min(self.scroll, max_scroll))
        if max_scroll > 0:
            bar_h = max(30, int(panel.height * panel.height / (panel.height + max_scroll)))
            bar_y = panel.y + int((panel.height - bar_h) * self.scroll / max_scroll)
            pygame.draw.rect(screen, (50, 55, 70), (panel.right - 8, panel.y, 4, panel.height), border_radius=2)
            pygame.draw.rect(screen, (0, 180, 180), (panel.right - 8, bar_y, 4, bar_h), border_radius=2)

        back_rect = pygame.Rect(sw // 2 - 110, sh - 48, 220, 34)
        self.buttons["back"] = back_rect
        hovered = back_rect.collidepoint(mouse)
        draw_rounded_panel(
            screen, back_rect,
            (50, 45, 60) if hovered else (38, 35, 48),
            (0, 200, 200), radius=8, alpha=240,
        )
        back_txt = self.font_label.render("НАЗАД", True, (255, 255, 255) if hovered else (180, 180, 190))
        screen.blit(back_txt, back_txt.get_rect(center=back_rect.center))

        hint = self.font_small.render("Esc — назад   ·   Колёсико — прокрутка", True, (110, 115, 130))
        screen.blit(hint, hint.get_rect(center=(sw // 2, sh - 14)))

        if self.dropdown_open:
            self._draw_resolution_dropdown(screen, game, mouse)

    def _section(self, screen, text, y):
        surf = self.font_section.render(text, True, (0, 200, 195))
        screen.blit(surf, (self._layout["label_x"], y))
        return y + 28

    def _slider(self, screen, label, y, value, slider_id, fmt=None):
        layout = self._layout
        x_start = layout["slider_x"]
        slider_w = layout["slider_w"]
        track = pygame.Rect(x_start, y + 10, slider_w, 6)
        pygame.draw.rect(screen, (55, 58, 70), track, border_radius=3)
        handle_x = x_start + int(max(0.0, min(1.0, value)) * slider_w)
        handle = (handle_x, y + 13)
        active = self.active_slider == slider_id
        color = (0, 255, 230) if active else (190, 195, 205)
        pygame.draw.circle(screen, color, handle, 8)
        if fmt:
            val_text = fmt(value)
        else:
            val_text = f"{int(value * 100)}%"
        lbl = self.font_label.render(f"{label}: {val_text}", True, (235, 235, 240))
        screen.blit(lbl, (layout["label_x"], y))
        self.buttons[slider_id] = pygame.Rect(x_start, y, slider_w, 24)
        return y + 34

    def _toggle(self, screen, label, y, enabled, toggle_id):
        lbl = self.font_label.render(label, True, (235, 235, 240))
        screen.blit(lbl, (self._layout["label_x"], y + 2))
        box = pygame.Rect(self._layout["toggle_x"], y, 26, 26)
        self.buttons[toggle_id] = box
        fill = (0, 100, 100) if enabled else (45, 42, 55)
        border = (0, 220, 210) if enabled else (90, 90, 100)
        draw_rounded_panel(screen, box, fill, border, radius=5, alpha=240)
        if enabled:
            pygame.draw.line(screen, (255, 255, 255), (box.x + 6, box.centery), (box.centerx, box.bottom - 6), 2)
            pygame.draw.line(screen, (255, 255, 255), (box.centerx, box.bottom - 6), (box.right - 5, box.y + 6), 2)
        return y + 34

    def _cycle_button(self, screen, label, y, value_text, button_id):
        lbl = self.font_label.render(label, True, (235, 235, 240))
        screen.blit(lbl, (self._layout["label_x"], y + 4))
        rect = pygame.Rect(self._layout["btn_x"], y, self._layout["btn_w"], 28)
        self.buttons[button_id] = rect
        draw_rounded_panel(screen, rect, (45, 42, 58), (0, 180, 180), radius=6, alpha=230)
        val = self.font_label.render(value_text, True, (255, 255, 255))
        screen.blit(val, val.get_rect(center=rect.center))
        return y + 36

    def _quality_buttons(self, screen, game, y):
        lbl = self.font_label.render("Качество:", True, (235, 235, 240))
        screen.blit(lbl, (self._layout["label_x"], y + 4))
        keys = ["low", "medium", "high"]
        btn_w = self._layout["quality_btn_w"]
        gap = 8
        start_x = self._layout["quality_x"]
        for i, key in enumerate(keys):
            rect = pygame.Rect(start_x + i * (btn_w + gap), y, btn_w, 28)
            active = game.quality == key
            fill = (0, 110, 110) if active else (45, 42, 58)
            draw_rounded_panel(screen, rect, fill, (0, 200, 200) if active else (80, 80, 95), radius=6, alpha=230)
            txt = self.font_small.render(QUALITY_LABELS[key], True, (255, 255, 255))
            screen.blit(txt, txt.get_rect(center=rect.center))
            self.buttons[f"quality_{key}"] = rect
        return y + 36

    def _draw_audio(self, screen, game, y):
        y = self._section(screen, "ГРОМКОСТЬ", y)
        y = self._slider(screen, "Общая", y, game.vol_master, "master")
        y = self._slider(screen, "Музыка", y, game.vol_music, "music")
        y = self._slider(screen, "Эффекты", y, game.vol_sfx, "sfx")
        y += 8
        y = self._section(screen, "КАНАЛЫ", y)
        y = self._toggle(screen, "Включить музыку", y, game.music_enabled, "music_toggle")
        y = self._toggle(screen, "Включить звуки", y, game.sfx_enabled, "sfx_toggle")
        y = self._toggle(screen, "Полное отключение звука", y, game.mute_all, "mute_toggle")
        return y

    def _draw_graphics(self, screen, game, y):
        y = self._section(screen, "КАЧЕСТВО И FPS", y)
        y = self._quality_buttons(screen, game, y)
        y = self._cycle_button(
            screen, "Лимит FPS", y,
            FPS_LABELS.get(game.fps_limit, str(game.fps_limit)), "fps_cycle",
        )
        y = self._toggle(screen, "VSync", y, game.vsync, "vsync_toggle")
        y = self._toggle(screen, "Полноэкранный режим", y, game.fullscreen, "fullscreen_toggle")
        y += 8
        y = self._section(screen, "ЭФФЕКТЫ", y)
        y = self._toggle(screen, "Частицы", y, game.particles_enabled, "particles_toggle")
        y = self._toggle(screen, "Эффекты экрана", y, game.screen_effects_enabled, "effects_toggle")
        y = self._toggle(screen, "Погода (дождь/песок)", y, game.weather_enabled, "weather_toggle")
        y = self._toggle(screen, "Ночное затемнение", y, game.night_overlay, "night_toggle")
        y = self._slider(
            screen, "Яркость", y, (game.brightness - 0.6) / 0.8,
            "brightness", fmt=lambda v: f"{int(60 + v * 80)}%",
        )
        y += 8
        y = self._section(screen, "РАЗРЕШЕНИЕ", y)
        if 0 <= game.res_index < len(game.resolutions):
            cur = game.resolutions[game.res_index]
        else:
            cur = (game.current_w, game.current_h)
        res_label = format_resolution_label(cur[0], cur[1], self._desktop_size())
        if game.fullscreen:
            res_label += " · полный экран"
        y = self._cycle_button(screen, "Разрешение экрана", y, res_label, "dropdown_toggle")
        hint = self.font_small.render(
            f"Доступно {len(game.resolutions)} режимов · колёсико в списке",
            True,
            (110, 115, 130),
        )
        screen.blit(hint, (self._layout["label_x"], y))
        return y + 22

    def _draw_gameplay(self, screen, game, y):
        y = self._section(screen, "КАМЕРА", y)
        y = self._toggle(screen, "Тряска камеры", y, game.camera_shake, "shake_toggle")
        y = self._slider(
            screen, "Сила тряски", y, (game.shake_intensity - 0.3) / 1.2, "shake_intensity",
            fmt=lambda v: f"{int(30 + v * 120)}%",
        )
        y += 8
        y = self._section(screen, "МИР", y)
        y = self._cycle_button(
            screen, "Скорость дня/ночи", y,
            DAY_SPEED_LABELS.get(game.day_speed, f"×{game.day_speed}"), "day_speed_cycle",
        )
        y = self._toggle(screen, "Отталкивание от врагов", y, game.enemy_push, "push_toggle")
        y = self._toggle(screen, "Цифры урона по врагам", y, game.damage_numbers, "dmgnums_toggle")
        return y

    def _draw_interface(self, screen, game, y):
        y = self._section(screen, "HUD", y)
        y = self._toggle(screen, "Миникарта", y, game.show_minimap, "minimap_toggle")
        y = self._toggle(screen, "Показывать FPS", y, game.show_fps, "fps_toggle")
        y = self._toggle(screen, "Подсказки [E]", y, game.show_hints, "hints_toggle")
        y = self._cycle_button(
            screen, "Масштаб интерфейса", y,
            UI_SCALE_LABELS.get(game.ui_scale, f"{int(game.ui_scale * 100)}%"), "ui_scale_cycle",
        )
        y += 8
        y = self._section(screen, "СБРОС", y)
        y = self._cycle_button(screen, "Сбросить настройки", y, "По умолчанию", "reset_defaults")
        return y

    def _draw_resolution_dropdown(self, screen, game, mouse):
        btn = self.buttons.get("dropdown_toggle")
        if not btn:
            return
        resolutions = game.resolutions
        if not resolutions:
            return
        self.dropdown_rects = []
        visible_count = min(self.DROPDOWN_VISIBLE, len(resolutions))
        max_scroll = max(0, len(resolutions) - visible_count)
        self.res_dropdown_scroll = max(0, min(self.res_dropdown_scroll, max_scroll))
        list_h = visible_count * self.DROPDOWN_ITEM_H
        list_rect = pygame.Rect(btn.x, btn.bottom + 2, btn.width, list_h)
        pygame.draw.rect(screen, (25, 22, 32), list_rect)
        pygame.draw.rect(screen, (0, 180, 180), list_rect, 1)
        desktop = self._desktop_size()
        for row, idx in enumerate(range(self.res_dropdown_scroll, self.res_dropdown_scroll + visible_count)):
            res = resolutions[idx]
            item = pygame.Rect(btn.x, btn.bottom + 2 + row * self.DROPDOWN_ITEM_H, btn.width, self.DROPDOWN_ITEM_H)
            self.dropdown_rects.append((idx, item))
            if item.collidepoint(mouse):
                pygame.draw.rect(screen, (0, 120, 120), item)
            elif idx == game.res_index:
                pygame.draw.rect(screen, (40, 70, 70), item)
            label = format_resolution_label(res[0], res[1], desktop)
            screen.blit(self.font_small.render(label, True, (255, 255, 255)), (item.x + 10, item.y + 6))
        if max_scroll > 0:
            bar_x = btn.right - 6
            bar_h = max(16, int(list_h * visible_count / len(resolutions)))
            bar_y = list_rect.y + int((list_h - bar_h) * self.res_dropdown_scroll / max_scroll)
            pygame.draw.rect(screen, (50, 55, 70), (bar_x, list_rect.y, 3, list_h), border_radius=2)
            pygame.draw.rect(screen, (0, 180, 180), (bar_x, bar_y, 3, bar_h), border_radius=2)

    def _update_slider(self, game, slider_id, mouse_x):
        layout = self._layout
        x_start = layout["slider_x"]
        slider_w = layout["slider_w"]
        val = max(0.0, min(1.0, (mouse_x - x_start) / slider_w))
        if slider_id == "master":
            game.vol_master = val
        elif slider_id == "music":
            game.vol_music = val
        elif slider_id == "sfx":
            game.vol_sfx = val
        elif slider_id == "brightness":
            game.brightness = 0.6 + val * 0.8
        elif slider_id == "shake_intensity":
            game.shake_intensity = 0.3 + val * 1.2
        game.apply_audio_settings()

    def handle_event(self, event, game):
        sw, sh = game.current_w, game.current_h

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.dropdown_open = False
            game.save_settings_only()
            return "back"

        if event.type == pygame.MOUSEWHEEL:
            panel = self._panel_rect(sw, sh)
            if self.dropdown_open:
                resolutions = game.resolutions
                max_scroll = max(0, len(resolutions) - min(self.DROPDOWN_VISIBLE, len(resolutions)))
                self.res_dropdown_scroll = max(
                    0,
                    min(max_scroll, self.res_dropdown_scroll - event.y * 3),
                )
                return None
            max_scroll = max(0, getattr(self, "_content_height", 0) - self._visible_height(panel))
            self.scroll = max(0, min(max_scroll, self.scroll - event.y * self.SCROLL_STEP))
            return None

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            if self.dropdown_open:
                for idx, item in self.dropdown_rects:
                    if item.collidepoint(pos):
                        game.res_index = idx
                        game.apply_display_mode()
                        self.dropdown_open = False
                        game.save_settings_only()
                        return None
                if not self.buttons.get("dropdown_toggle", pygame.Rect(0, 0, 0, 0)).collidepoint(pos):
                    self.dropdown_open = False
                    return None

            for tab_id, _ in SETTINGS_TABS:
                btn = self.buttons.get(f"tab_{tab_id}")
                if btn and btn.collidepoint(pos):
                    self.tab = tab_id
                    self.reset_scroll()
                    return None

            if self.buttons.get("back") and self.buttons["back"].collidepoint(pos):
                game.save_settings_only()
                return "back"

            if self.buttons.get("dropdown_toggle") and self.buttons["dropdown_toggle"].collidepoint(pos):
                self.dropdown_open = not self.dropdown_open
                if self.dropdown_open:
                    game.resolutions = build_resolution_list()
                    if 0 <= game.res_index < len(game.resolutions):
                        selected = game.res_index
                    else:
                        selected = 0
                    visible = min(self.DROPDOWN_VISIBLE, len(game.resolutions))
                    max_scroll = max(0, len(game.resolutions) - visible)
                    self.res_dropdown_scroll = max(0, min(max_scroll, selected - visible // 2))
                return None

            for key in ["low", "medium", "high"]:
                btn = self.buttons.get(f"quality_{key}")
                if btn and btn.collidepoint(pos):
                    game.apply_quality_preset(key)
                    game.save_settings_only()
                    return None

            toggles = {
                "vsync_toggle": ("vsync", lambda g, v: g.apply_vsync(v)),
                "fullscreen_toggle": ("fullscreen", lambda g, v: g.apply_fullscreen(v)),
                "particles_toggle": ("particles_enabled", lambda g, v: g.apply_particles(v)),
                "effects_toggle": ("screen_effects_enabled", lambda g, v: g.apply_screen_effects(v)),
                "weather_toggle": ("weather_enabled", lambda g, v: g.apply_weather(v)),
                "night_toggle": ("night_overlay", lambda g, v: setattr(g, "night_overlay", v)),
                "fps_toggle": ("show_fps", lambda g, v: setattr(g, "show_fps", v)),
                "music_toggle": ("music_enabled", lambda g, v: g.apply_music_enabled(v)),
                "sfx_toggle": ("sfx_enabled", lambda g, v: g.apply_sfx_enabled(v)),
                "mute_toggle": ("mute_all", lambda g, v: g.apply_mute_all(v)),
                "shake_toggle": ("camera_shake", lambda g, v: setattr(g, "camera_shake", v)),
                "push_toggle": ("enemy_push", lambda g, v: setattr(g, "enemy_push", v)),
                "dmgnums_toggle": ("damage_numbers", lambda g, v: setattr(g, "damage_numbers", v)),
                "minimap_toggle": ("show_minimap", lambda g, v: setattr(g, "show_minimap", v)),
                "hints_toggle": ("show_hints", lambda g, v: setattr(g, "show_hints", v)),
            }
            for btn_id, (attr, apply_fn) in toggles.items():
                btn = self.buttons.get(btn_id)
                if btn and btn.collidepoint(pos):
                    apply_fn(game, not getattr(game, attr))
                    game.save_settings_only()
                    return None

            cycles = {
                "fps_cycle": game.cycle_fps_limit,
                "day_speed_cycle": game.cycle_day_speed,
                "ui_scale_cycle": game.cycle_ui_scale,
                "reset_defaults": game.reset_settings_defaults,
            }
            for btn_id, fn in cycles.items():
                btn = self.buttons.get(btn_id)
                if btn and btn.collidepoint(pos):
                    fn()
                    game.save_settings_only()
                    return None

            for slider_id in ["master", "music", "sfx", "brightness", "shake_intensity"]:
                btn = self.buttons.get(slider_id)
                if btn and btn.collidepoint(pos):
                    self.active_slider = slider_id
                    self._update_slider(game, slider_id, pos[0])
                    return None

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.active_slider:
                game.save_settings_only()
            self.active_slider = None

        elif event.type == pygame.MOUSEMOTION and self.active_slider:
            self._update_slider(game, self.active_slider, event.pos[0])

        return None

    @staticmethod
    def apply_dict(game, data):
        for key, default in SETTING_DEFAULTS.items():
            setattr(game, key, data.get(key, default))
        if game.fps_limit in FPS_OPTIONS:
            game.fps_index = FPS_OPTIONS.index(game.fps_limit)
        if game.day_speed in DAY_SPEED_OPTIONS:
            game.day_speed_index = DAY_SPEED_OPTIONS.index(game.day_speed)
        else:
            game.day_speed_index = 1
        if game.ui_scale in UI_SCALE_OPTIONS:
            game.ui_scale_index = UI_SCALE_OPTIONS.index(game.ui_scale)
        else:
            game.ui_scale_index = 1
        game.resolutions = build_resolution_list()
        game.res_index = resolve_res_index(
            game.resolutions,
            game.res_index,
            data.get("res_width"),
            data.get("res_height"),
        )
        if 0 <= game.res_index < len(game.resolutions):
            game.current_w, game.current_h = game.resolutions[game.res_index]
