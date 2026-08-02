import math

import pygame

from assets import create_npc_sprite



INTERACT_RADIUS = 72





class NPC(pygame.sprite.Sprite):

    ROLES = {

        "elder": {"name": "Старейшина", "color": (200, 180, 120)},

        "merchant": {"name": "Торговец", "color": (255, 200, 80)},

        "scout": {"name": "Разведчик", "color": (140, 200, 255)},

        "mystic": {"name": "Мистик", "color": (180, 120, 255)},

    }



    def __init__(self, x, y, role, npc_id):

        super().__init__()

        self.role = role

        self.npc_id = npc_id

        self.image = create_npc_sprite(role)

        self.rect = self.image.get_rect()

        self.rect.center = (x, y)

        self.bob_timer = 0

        self.base_y = y

        meta = self.ROLES.get(role, {"name": "NPC", "color": (200, 200, 200)})

        self.display_name = meta["name"]

        self.name_color = meta["color"]



    def update(self):

        self.bob_timer += 0.04

        self.rect.centery = self.base_y + int(math.sin(self.bob_timer) * 2)



    def is_near(self, player_rect):

        dx = self.rect.centerx - player_rect.centerx

        dy = self.rect.centery - player_rect.centery

        return math.hypot(dx, dy) <= INTERACT_RADIUS





def create_world_npcs():

    from config import TILE_SIZE, MAP_WIDTH, SNOW_BOUNDARY_Y, RUINS_BOUNDARY_X, RUINS_BOUNDARY_Y

    npcs = pygame.sprite.Group()

    plaza_x = (MAP_WIDTH // 2) * TILE_SIZE
    plaza_y = (MAP_WIDTH // 2) * TILE_SIZE

    npcs.add(NPC(plaza_x - 40, plaza_y, "elder", "elder"))
    npcs.add(NPC(plaza_x + 40, plaza_y + 16, "merchant", "merchant"))
    npcs.add(NPC(plaza_x, (SNOW_BOUNDARY_Y - 3) * TILE_SIZE, "scout", "scout"))
    npcs.add(NPC((RUINS_BOUNDARY_X + 5) * TILE_SIZE, (RUINS_BOUNDARY_Y + 4) * TILE_SIZE, "mystic", "mystic"))

    return npcs

