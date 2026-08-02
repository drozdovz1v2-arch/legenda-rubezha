import math
import random
import pygame

INTERACT_RADIUS = 50


def _draw_chest_surface(opened=False):
    surf = pygame.Surface((24, 20), pygame.SRCALPHA)
    body_color = (120, 80, 30) if not opened else (90, 60, 25)
    lid_color = (160, 110, 45) if not opened else (110, 75, 30)
    pygame.draw.rect(surf, body_color, (2, 8, 20, 12), border_radius=2)
    pygame.draw.rect(surf, lid_color, (2, 2, 20, 9), border_radius=3)
    pygame.draw.rect(surf, (255, 215, 0), (10, 10, 4, 6))
    if opened:
        pygame.draw.rect(surf, (255, 230, 120), (6, 10, 12, 4))
        pygame.draw.circle(surf, (255, 215, 0), (12, 12), 2)
    else:
        pygame.draw.line(surf, (200, 160, 60), (2, 10), (22, 10), 1)
    return surf


class Chest(pygame.sprite.Sprite):
    def __init__(self, x, y, chest_id, opened=False, loot=None):
        super().__init__()
        self.chest_id = chest_id
        self.opened = opened
        self.loot = loot if loot else self._roll_loot()
        self.bob_timer = random.uniform(0, 3.14)
        self.base_y = y
        self.image = _draw_chest_surface(opened)
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)

    def update(self):
        if self.opened:
            return
        self.bob_timer += 0.06
        self.rect.y = self.base_y + int(math.sin(self.bob_timer) * 2)

    @staticmethod
    def _roll_loot():
        return {
            "gold": random.randint(6, 20),
            "potions": 1 if random.random() < 0.4 else 0,
        }

    def refresh_sprite(self):
        self.image = _draw_chest_surface(self.opened)

    def is_near(self, player_rect):
        dx = self.rect.centerx - player_rect.centerx
        dy = self.rect.centery - player_rect.centery
        return math.hypot(dx, dy) <= INTERACT_RADIUS

    def open_chest(self):
        if self.opened:
            return None
        self.opened = True
        self.refresh_sprite()
        return dict(self.loot)


def chest_to_dict(chest):
    return {
        "id": chest.chest_id,
        "x": chest.rect.x,
        "y": chest.rect.y,
        "opened": chest.opened,
        "loot": chest.loot,
    }


def chest_from_dict(data):
    return Chest(
        data["x"],
        data["y"],
        data["id"],
        opened=data.get("opened", False),
        loot=data.get("loot"),
    )
