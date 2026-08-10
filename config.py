# Название и версия игры (отображаются в меню и заголовке окна)
GAME_TITLE = "Легенда Рубежа"
GAME_VERSION = "beta 0.0.0.9"

# Размеры экрана по умолчанию и FPS
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60

# Размеры объектов (в пикселях)
TILE_SIZE = 32
PLAYER_SIZE = 32

# Размеры всей карты в блоках (150×150 — ~4800×4800 px)
MAP_WIDTH = 150
MAP_HEIGHT = 150

WORLD_WIDTH = MAP_WIDTH * TILE_SIZE
WORLD_HEIGHT = MAP_HEIGHT * TILE_SIZE

# Центральная площадь (без препятствий, старт игрока)
PLAZA_MIN = 63
PLAZA_MAX = 87
SPAWN_EXCLUDE_MIN = 57
SPAWN_EXCLUDE_MAX = 93

# Скорость игрока
PLAYER_SPEED = 4

# Границы биомов (в тайлах): лес | пустыня по X, снег по Y (север), руины — юго-запад
BIOME_BOUNDARY_X = 75
SNOW_BOUNDARY_Y = 38
RUINS_BOUNDARY_X = 45
RUINS_BOUNDARY_Y = 105

# Хитбоксы сущностей: (смещение X, смещение Y, ширина, высота) от sprite.rect
PLAYER_COLLISION_INSET = (8, 14, 16, 12)
ENEMY_COLLISION_INSET = (6, 12, 20, 16)

# Цикл день/ночь (кадры; ~4 мин при 60 FPS)
DAY_CYCLE_LENGTH = 14400
NIGHT_START = 0.55
DAWN_START = 0.82

# Коды тайлов
TILE_FLOOR = 0   # Трава
TILE_WALL = 1    # Стена
TILE_TREE = 2    # Дерево
TILE_SAND = 3    # Песок пустыни
TILE_CACTUS = 4  # Кактус
TILE_SNOW = 5    # Снег
TILE_ICE = 6     # Ледяная глыба (препятствие)
TILE_RUINS = 7   # Камни руин
TILE_RUINS_PILLAR = 8  # Колонна руин
TILE_RUINS_SPIKE = 9   # Шипы руин (препятствие)

TILE_COLORS = {
    TILE_FLOOR: (42, 128, 58),
    TILE_WALL: (88, 90, 98),
    TILE_TREE: (28, 118, 44),
    TILE_SAND: (228, 196, 148),
    TILE_CACTUS: (28, 118, 48),
    TILE_SNOW: (236, 244, 255),
    TILE_ICE: (130, 200, 235),
    TILE_RUINS: (62, 58, 74),
    TILE_RUINS_PILLAR: (118, 112, 132),
    TILE_RUINS_SPIKE: (168, 78, 120),
}

# Частичные коллизии тайлов (не весь 32×32 блок)
TILE_COLLISION = {
    TILE_WALL: (0, 0, 32, 32),
    TILE_TREE: (11, 20, 10, 10),
    TILE_CACTUS: (8, 10, 16, 18),
    TILE_ICE: (4, 10, 24, 20),
    TILE_RUINS_PILLAR: (6, 4, 20, 26),
    TILE_RUINS_SPIKE: (8, 14, 16, 14),
}

# Лимиты врагов и волны респавна (хардкор — больше угроз на карте)
MAX_SLIMES = 40
MAX_BOSSES = 6
MAX_FROST = 24
MAX_WOLVES = 15
MAX_SCORPIONS = 18
MAX_WRAITHS = 18
CHEST_COUNT = 15
RESPAWN_INTERVAL = 520
RESPAWN_FILL_RATIO = 0.45

# Roguelike-баланс прокачки (beta — чуть мягче старта, сохраняем хардкор)
PLAYER_START_HP = 80
PLAYER_START_DAMAGE = 12
PLAYER_START_MAX_EXP = 120
LEVEL_HP_BONUS = 10
LEVEL_HEAL_RATIO = 0.25
EXP_SCALING = 1.42

# Базовый шанс элитных мобов при спавне
ELITE_SPAWN_CHANCE = 0.10
ELITE_SPAWN_CAP = 0.62

# Критические удары (шанс и множитель урона)
CRIT_CHANCE = 0.12
CRIT_MULTIPLIER = 2.0

# Урон от врагов (хардкор — выше урон и чаще удары)
ENEMY_DAMAGE = {
    "slime": {"contact": 6, "cooldown": 44},
    "frost_slime": {"contact": 7, "cooldown": 42},
    "wolf": {"contact": 10, "cooldown": 46},
    "scorpion": {"contact": 11, "cooldown": 50},
    "wraith": {"contact": 10, "cooldown": 44},
    "ice_guardian": {"contact": 16, "cooldown": 54},
    "blue_boss": {"contact": 14, "cooldown": 50},
    "sand_colossus": {"contact": 22, "cooldown": 64},
    "boss_orb": {"hit": 14},
    "frost_orb": {"hit": 11},
    "sand_slam": {"hit": 22},
}

# Неуязвимость после старта / продолжения (кадры @ 60 FPS)
SPAWN_IFRAMES_NEW = 180
SPAWN_IFRAMES_CONTINUE = 180
