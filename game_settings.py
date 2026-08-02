# Настройки производительности, графики и геймплея (значения по умолчанию)
DEFAULT_FPS_LIMIT = 60
DEFAULT_VSYNC = True
DEFAULT_QUALITY = "medium"  # low | medium | high
DEFAULT_PARTICLES = True
DEFAULT_SCREEN_EFFECTS = True
DEFAULT_SHOW_FPS = False
DEFAULT_FULLSCREEN = True
DEFAULT_MUTE_ALL = False
DEFAULT_MUSIC_ENABLED = True
DEFAULT_SFX_ENABLED = True
DEFAULT_UI_SCALE = 1.0
DEFAULT_CAMERA_SHAKE = True
DEFAULT_SHAKE_INTENSITY = 1.0
DEFAULT_DAMAGE_NUMBERS = True
DEFAULT_SHOW_MINIMAP = True
DEFAULT_WEATHER = True
DEFAULT_NIGHT_OVERLAY = True
DEFAULT_DAY_SPEED = 1.0
DEFAULT_ENEMY_PUSH = True
DEFAULT_SHOW_HINTS = True
DEFAULT_BRIGHTNESS = 1.0
DEFAULT_AUTO_RESOLUTION = True

FPS_OPTIONS = [30, 60, 120, 0]
DAY_SPEED_OPTIONS = [0.5, 1.0, 1.5, 2.0]
UI_SCALE_OPTIONS = [0.85, 1.0, 1.15, 1.3]

QUALITY_PRESETS = {
    "low": {
        "particles": False,
        "screen_effects": False,
        "separation_iterations": 1,
        "particle_multiplier": 0.0,
        "weather": False,
    },
    "medium": {
        "particles": True,
        "screen_effects": True,
        "separation_iterations": 1,
        "particle_multiplier": 0.55,
        "weather": True,
    },
    "high": {
        "particles": True,
        "screen_effects": True,
        "separation_iterations": 2,
        "particle_multiplier": 1.0,
        "weather": True,
    },
}

QUALITY_LABELS = {"low": "Низкое", "medium": "Среднее", "high": "Высокое"}
FPS_LABELS = {30: "30", 60: "60", 120: "120", 0: "Без лимита"}
DAY_SPEED_LABELS = {0.5: "×0.5", 1.0: "×1", 1.5: "×1.5", 2.0: "×2"}
UI_SCALE_LABELS = {0.85: "85%", 1.0: "100%", 1.15: "115%", 1.3: "130%"}

SETTINGS_TABS = [
    ("audio", "Звук"),
    ("graphics", "Графика"),
    ("gameplay", "Игра"),
    ("interface", "Интерфейс"),
]

RESOLUTIONS = [
    (800, 600), (1024, 768), (1280, 720), (1600, 900),
    (1920, 1080), (2560, 1440), (3840, 2160),
]

# Базовый список популярных разрешений (16:9, 16:10, 4:3, ultrawide)
BASE_RESOLUTIONS = [
    (640, 480), (720, 480), (800, 600), (1024, 768),
    (1152, 864), (1280, 720), (1280, 800), (1280, 960), (1280, 1024),
    (1360, 768), (1366, 768), (1440, 900), (1600, 900), (1680, 1050),
    (1920, 1080), (1920, 1200), (2048, 1152), (2560, 1080), (2560, 1440),
    (2560, 1600), (3440, 1440), (3840, 2160), (3840, 2400),
    (5120, 1440), (5120, 2160),
]


def build_resolution_list():
    """Собирает список разрешений: базовые + режимы монитора."""
    import pygame

    resolutions = list(BASE_RESOLUTIONS)
    try:
        info = pygame.display.Info()
        if info.current_w >= 640 and info.current_h >= 480:
            resolutions.append((info.current_w, info.current_h))
        modes = pygame.display.list_modes()
        if modes and modes != -1:
            for mode in modes:
                if isinstance(mode, (tuple, list)) and len(mode) >= 2:
                    w, h = int(mode[0]), int(mode[1])
                    if w >= 640 and h >= 480:
                        resolutions.append((w, h))
    except (pygame.error, TypeError, ValueError):
        pass

    seen = set()
    unique = []
    for w, h in resolutions:
        key = (w, h)
        if key not in seen:
            seen.add(key)
            unique.append(key)
    unique.sort(key=lambda r: (r[0] * r[1], r[0]), reverse=True)
    return unique or list(RESOLUTIONS)


def resolve_res_index(resolutions, res_index, res_width=None, res_height=None):
    """Находит индекс сохранённого разрешения или ближайший вариант."""
    if res_width and res_height:
        for i, (w, h) in enumerate(resolutions):
            if w == res_width and h == res_height:
                return i
    if 0 <= res_index < len(resolutions):
        return res_index
    target = (1280, 720)
    best = 0
    best_diff = float("inf")
    for i, (w, h) in enumerate(resolutions):
        diff = abs(w - target[0]) + abs(h - target[1])
        if diff < best_diff:
            best_diff = diff
            best = i
    return best


def format_resolution_label(width, height, desktop_size=None):
    label = f"{width} × {height}"
    if width == 3840 and height == 2160:
        label += " (4K)"
    elif width == 1920 and height == 1080:
        label += " (FHD)"
    elif width == 2560 and height == 1440:
        label += " (QHD)"
    elif desktop_size and (width, height) == desktop_size:
        label += " (экран)"
    return label


def get_desktop_size():
    """Текущее разрешение рабочего стола (или окна до полного экрана)."""
    import pygame

    info = pygame.display.Info()
    return max(640, int(info.current_w)), max(480, int(info.current_h))


def fit_resolution(width, height, desktop_w, desktop_h):
    """Уменьшает разрешение, чтобы оно целиком помещалось на экран."""
    w, h = int(width), int(height)
    if w <= desktop_w and h <= desktop_h:
        return w, h
    scale = min(desktop_w / max(1, w), desktop_h / max(1, h))
    return max(640, int(w * scale)), max(480, int(h * scale))


def pick_best_resolution_index(
    resolutions,
    desktop_w,
    desktop_h,
    prefer_w=None,
    prefer_h=None,
):
    """Подбирает лучшее разрешение под монитор игрока."""
    if not resolutions:
        return 0

    desktop_ar = desktop_w / max(1, desktop_h)
    best_i = 0
    best_score = -1e18
    for i, (w, h) in enumerate(resolutions):
        fw, fh = fit_resolution(w, h, desktop_w, desktop_h)
        if fw < 640 or fh < 480:
            continue
        ar = fw / max(1, fh)
        ar_penalty = abs(ar - desktop_ar) * 1_000_000
        area = fw * fh
        match_bonus = 0
        if prefer_w and prefer_h:
            match_bonus = (
                500_000_000
                - abs(fw - prefer_w) * 1000
                - abs(fh - prefer_h) * 1000
            )
        elif fw == 1280 and fh == 720:
            match_bonus = 50_000_000
        score = area + match_bonus - ar_penalty
        if score > best_score:
            best_score = score
            best_i = i
    return best_i

SETTING_DEFAULTS = {
    "vol_master": 0.8,
    "vol_music": 0.5,
    "vol_sfx": 0.7,
    "res_index": 2,
    "fullscreen": DEFAULT_FULLSCREEN,
    "fps_limit": DEFAULT_FPS_LIMIT,
    "vsync": DEFAULT_VSYNC,
    "quality": DEFAULT_QUALITY,
    "particles_enabled": DEFAULT_PARTICLES,
    "screen_effects_enabled": DEFAULT_SCREEN_EFFECTS,
    "show_fps": DEFAULT_SHOW_FPS,
    "mute_all": DEFAULT_MUTE_ALL,
    "music_enabled": DEFAULT_MUSIC_ENABLED,
    "sfx_enabled": DEFAULT_SFX_ENABLED,
    "ui_scale": DEFAULT_UI_SCALE,
    "camera_shake": DEFAULT_CAMERA_SHAKE,
    "shake_intensity": DEFAULT_SHAKE_INTENSITY,
    "damage_numbers": DEFAULT_DAMAGE_NUMBERS,
    "show_minimap": DEFAULT_SHOW_MINIMAP,
    "weather_enabled": DEFAULT_WEATHER,
    "night_overlay": DEFAULT_NIGHT_OVERLAY,
    "day_speed": DEFAULT_DAY_SPEED,
    "enemy_push": DEFAULT_ENEMY_PUSH,
    "show_hints": DEFAULT_SHOW_HINTS,
    "brightness": DEFAULT_BRIGHTNESS,
    "auto_resolution": DEFAULT_AUTO_RESOLUTION,
}
