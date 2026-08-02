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
}
