import math
import pygame

INTERACT_RADIUS = 56

SHRINE_OFFERS = [
    {
        "id": "heal",
        "label": "Благословение: +45 HP",
        "desc": "Святой свет исцеляет раны.",
    },
    {
        "id": "gold",
        "label": "Дар богатства: +35 золота",
        "desc": "Монеты материализуются из воздуха.",
    },
    {
        "id": "skill",
        "label": "Дар судьбы: случайный скилл",
        "desc": "Мгновенно получить стак умения.",
    },
    {
        "id": "curse",
        "label": "Проклятие: −20 HP, +60 золота",
        "desc": "Риск ради награды.",
    },
]


def create_shrine_sprite(used=False):
    surf = pygame.Surface((28, 32), pygame.SRCALPHA)
    stone = (90, 95, 110) if not used else (60, 62, 70)
    glow = (255, 220, 120) if not used else (100, 100, 110)
    pygame.draw.rect(surf, stone, (4, 14, 20, 16), border_radius=3)
    pygame.draw.polygon(surf, stone, [(14, 4), (24, 14), (4, 14)])
    pygame.draw.circle(surf, glow, (14, 10), 5)
    if not used:
        pygame.draw.circle(surf, (255, 255, 200), (14, 10), 2)
    return surf


class Shrine(pygame.sprite.Sprite):
    def __init__(self, x, y, shrine_id):
        super().__init__()
        self.shrine_id = shrine_id
        self.used = False
        self.bob_timer = 0.0
        self.base_y = y
        self.image = create_shrine_sprite(False)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

    def mark_used(self):
        self.used = True
        self.image = create_shrine_sprite(True)

    def update(self):
        if self.used:
            return
        self.bob_timer += 0.05
        self.rect.centery = self.base_y + int(math.sin(self.bob_timer) * 3)

    def is_near(self, player_rect):
        if self.used:
            return False
        dx = self.rect.centerx - player_rect.centerx
        dy = self.rect.centery - player_rect.centery
        return math.hypot(dx, dy) <= INTERACT_RADIUS


def shrine_to_dict(shrine):
    return {
        "id": shrine.shrine_id,
        "x": shrine.rect.centerx,
        "y": shrine.rect.centery,
        "used": shrine.used,
    }


def shrine_from_dict(data):
    shrine = Shrine(data["x"], data["y"], data["id"])
    if data.get("used"):
        shrine.mark_used()
    return shrine


def spawn_shrines(tilemap, count=4, seed=0):
    import random
    from config import MAP_WIDTH, MAP_HEIGHT, TILE_SIZE

    rng = random.Random(seed + 5555)
    group = pygame.sprite.Group()
    biomes = ["forest", "desert", "snow", "ruins"]
    for i, biome in enumerate(biomes[:count]):
        placed = False
        for _ in range(120):
            gx = rng.randint(3, MAP_WIDTH - 4)
            gy = rng.randint(3, MAP_HEIGHT - 4)
            if not tilemap.is_walkable_spawn(gx, gy):
                continue
            if tilemap.biome_at(gx, gy) != biome:
                continue
            group.add(Shrine(gx * TILE_SIZE + 16, gy * TILE_SIZE + 16, f"shrine_{i}"))
            placed = True
            break
        if not placed:
            for _ in range(80):
                gx = rng.randint(3, MAP_WIDTH - 4)
                gy = rng.randint(3, MAP_HEIGHT - 4)
                if not tilemap.is_walkable_spawn(gx, gy):
                    continue
                group.add(Shrine(gx * TILE_SIZE + 16, gy * TILE_SIZE + 16, f"shrine_{i}"))
                break
    return group
