import pygame

import random

from config import (

    TILE_SIZE, MAP_WIDTH, MAP_HEIGHT,

    TILE_FLOOR, TILE_WALL, TILE_TREE, TILE_SAND, TILE_CACTUS, TILE_SNOW, TILE_ICE,
    TILE_RUINS, TILE_RUINS_PILLAR, TILE_RUINS_SPIKE,

    BIOME_BOUNDARY_X, SNOW_BOUNDARY_Y, RUINS_BOUNDARY_X, RUINS_BOUNDARY_Y,
    PLAZA_MIN, PLAZA_MAX, SPAWN_EXCLUDE_MIN, SPAWN_EXCLUDE_MAX,
    TILE_COLLISION,

)

from assets import (

    create_grass_sprite, create_wall_sprite, create_tree_sprite,

    create_sand_sprite, create_cactus_sprite, create_snow_sprite, create_ice_sprite,
    create_ruins_sprite, create_ruins_pillar_sprite, create_ruins_spike_sprite,

)



BLOCKING_TILES = {TILE_WALL, TILE_TREE, TILE_CACTUS, TILE_ICE, TILE_RUINS_SPIKE, TILE_RUINS_PILLAR}

CHUNK_TILES = 16
CHUNK_PX = CHUNK_TILES * TILE_SIZE





class Tile(pygame.sprite.Sprite):

    def __init__(self, x, y, tile_type):

        super().__init__()

        self.grid_x = x

        self.grid_y = y

        self.tile_type = tile_type



        sprite_map = {

            TILE_FLOOR: create_grass_sprite,

            TILE_WALL: create_wall_sprite,

            TILE_TREE: create_tree_sprite,

            TILE_SAND: create_sand_sprite,

            TILE_CACTUS: create_cactus_sprite,

            TILE_SNOW: create_snow_sprite,

            TILE_ICE: create_ice_sprite,

            TILE_RUINS: create_ruins_sprite,

            TILE_RUINS_PILLAR: create_ruins_pillar_sprite,

            TILE_RUINS_SPIKE: create_ruins_spike_sprite,

        }

        self.image = sprite_map[tile_type](x, y)



        self.rect = self.image.get_rect()

        self.rect.x = x * TILE_SIZE

        self.rect.y = y * TILE_SIZE





class TileMap:

    def __init__(self, seed=None):

        self.tiles_group = pygame.sprite.Group()

        self.obstacles_group = pygame.sprite.Group()

        self.matrix = []

        self.tile_grid = []

        self.seed = seed if seed is not None else random.randint(1, 999_999)

        self._chunk_surfaces = None
        self.los_tick = 0

        self.generate_map()



    def _pick_tile_type(self, x, y, rng):

        if x == 0 or y == 0 or x == MAP_WIDTH - 1 or y == MAP_HEIGHT - 1:

            return TILE_WALL

        if PLAZA_MIN < x < PLAZA_MAX and PLAZA_MIN < y < PLAZA_MAX:

            return TILE_FLOOR



        if x < RUINS_BOUNDARY_X and y > RUINS_BOUNDARY_Y:

            rand = rng.random()

            if rand < 0.70:

                return TILE_RUINS

            if rand < 0.88:

                return TILE_RUINS_PILLAR

            return TILE_RUINS_SPIKE



        if y < SNOW_BOUNDARY_Y:

            rand = rng.random()

            if rand < 0.78:

                return TILE_SNOW

            if rand < 0.93:

                return TILE_ICE

            return TILE_SNOW



        rand = rng.random()

        if x < BIOME_BOUNDARY_X:

            if rand < 0.85:

                return TILE_FLOOR

            if rand < 0.95:

                return TILE_TREE

            return TILE_WALL



        if rand < 0.88:

            return TILE_SAND

        return TILE_CACTUS



    def generate_map(self):

        rng = random.Random(self.seed)

        self.tiles_group.empty()

        self.obstacles_group.empty()

        self.matrix = []

        self.tile_grid = []



        for y in range(MAP_HEIGHT):

            row = []

            grid_row = []

            for x in range(MAP_WIDTH):

                tile_type = self._pick_tile_type(x, y, rng)

                row.append(tile_type)

                tile = Tile(x, y, tile_type)

                grid_row.append(tile)

                self.tiles_group.add(tile)

                if tile_type in BLOCKING_TILES:

                    self.obstacles_group.add(tile)



            self.matrix.append(row)

            self.tile_grid.append(grid_row)



    def is_blocking(self, grid_x, grid_y):

        if grid_x < 0 or grid_y < 0 or grid_x >= MAP_WIDTH or grid_y >= MAP_HEIGHT:

            return True

        return self.matrix[grid_y][grid_x] in BLOCKING_TILES



    def collision_rect_for_tile(self, tile):

        shape = TILE_COLLISION.get(tile.tile_type)

        if shape is None:

            return None

        ox, oy, w, h = shape

        return pygame.Rect(tile.rect.x + ox, tile.rect.y + oy, w, h)



    def rect_hits_blocking(self, rect):

        x0 = max(0, rect.left // TILE_SIZE)

        x1 = min(MAP_WIDTH - 1, rect.right // TILE_SIZE)

        y0 = max(0, rect.top // TILE_SIZE)

        y1 = min(MAP_HEIGHT - 1, rect.bottom // TILE_SIZE)

        for gy in range(y0, y1 + 1):

            for gx in range(x0, x1 + 1):

                if not self.is_blocking(gx, gy):

                    continue

                tile = self.tile_grid[gy][gx]

                block_rect = self.collision_rect_for_tile(tile)

                if block_rect is None:

                    block_rect = tile.rect

                if rect.colliderect(block_rect):

                    return True

        return False



    def get_blocking_tiles_touching(self, rect):

        x0 = max(0, rect.left // TILE_SIZE)

        x1 = min(MAP_WIDTH - 1, rect.right // TILE_SIZE)

        y0 = max(0, rect.top // TILE_SIZE)

        y1 = min(MAP_HEIGHT - 1, rect.bottom // TILE_SIZE)

        for gy in range(y0, y1 + 1):

            for gx in range(x0, x1 + 1):

                if self.is_blocking(gx, gy):

                    tile = self.tile_grid[gy][gx]

                    block_rect = self.collision_rect_for_tile(tile)

                    if block_rect is None:

                        block_rect = tile.rect

                    if rect.colliderect(block_rect):

                        yield tile



    def get_blocking_rects_touching(self, rect):

        x0 = max(0, rect.left // TILE_SIZE)

        x1 = min(MAP_WIDTH - 1, rect.right // TILE_SIZE)

        y0 = max(0, rect.top // TILE_SIZE)

        y1 = min(MAP_HEIGHT - 1, rect.bottom // TILE_SIZE)

        for gy in range(y0, y1 + 1):

            for gx in range(x0, x1 + 1):

                if not self.is_blocking(gx, gy):

                    continue

                tile = self.tile_grid[gy][gx]

                block_rect = self.collision_rect_for_tile(tile)

                if block_rect is None:

                    block_rect = tile.rect

                if rect.colliderect(block_rect):

                    yield block_rect



    def iter_visible_tiles(self, view_rect):

        x0 = max(0, view_rect.left // TILE_SIZE)

        x1 = min(MAP_WIDTH - 1, view_rect.right // TILE_SIZE)

        y0 = max(0, view_rect.top // TILE_SIZE)

        y1 = min(MAP_HEIGHT - 1, view_rect.bottom // TILE_SIZE)

        for gy in range(y0, y1 + 1):

            row = self.tile_grid[gy]

            for gx in range(x0, x1 + 1):

                yield row[gx]

    def build_chunk_cache(self, display=None):
        cols = (MAP_WIDTH + CHUNK_TILES - 1) // CHUNK_TILES
        rows = (MAP_HEIGHT + CHUNK_TILES - 1) // CHUNK_TILES
        chunks = {}
        for row in range(rows):
            for col in range(cols):
                surf = pygame.Surface((CHUNK_PX, CHUNK_PX))
                for ty in range(CHUNK_TILES):
                    gy = row * CHUNK_TILES + ty
                    if gy >= MAP_HEIGHT:
                        break
                    for tx in range(CHUNK_TILES):
                        gx = col * CHUNK_TILES + tx
                        if gx >= MAP_WIDTH:
                            break
                        tile = self.tile_grid[gy][gx]
                        surf.blit(tile.image, (tx * TILE_SIZE, ty * TILE_SIZE))
                if display is not None:
                    surf = surf.convert(display)
                else:
                    surf = surf.convert()
                chunks[(col, row)] = surf
        self._chunk_surfaces = chunks

    def draw_visible_chunks(self, screen, view_rect, cam_x, cam_y):
        if not self._chunk_surfaces:
            for tile in self.iter_visible_tiles(view_rect):
                screen.blit(tile.image, (tile.rect.x + cam_x, tile.rect.y + cam_y))
            return
        col0 = max(0, view_rect.left // CHUNK_PX)
        col1 = min((MAP_WIDTH - 1) // CHUNK_TILES, view_rect.right // CHUNK_PX)
        row0 = max(0, view_rect.top // CHUNK_PX)
        row1 = min((MAP_HEIGHT - 1) // CHUNK_TILES, view_rect.bottom // CHUNK_PX)
        for row in range(row0, row1 + 1):
            for col in range(col0, col1 + 1):
                chunk = self._chunk_surfaces.get((col, row))
                if chunk is not None:
                    screen.blit(chunk, (col * CHUNK_PX + cam_x, row * CHUNK_PX + cam_y))



    def biome_at(self, grid_x, grid_y):

        if grid_y < SNOW_BOUNDARY_Y:

            return "snow"

        if grid_x < RUINS_BOUNDARY_X and grid_y > RUINS_BOUNDARY_Y:

            return "ruins"

        if grid_x >= BIOME_BOUNDARY_X:

            return "desert"

        return "forest"



    def is_walkable_spawn(self, grid_x, grid_y):

        if grid_x < 2 or grid_y < 2 or grid_x >= MAP_WIDTH - 2 or grid_y >= MAP_HEIGHT - 2:

            return False

        if SPAWN_EXCLUDE_MIN < grid_x < SPAWN_EXCLUDE_MAX and SPAWN_EXCLUDE_MIN < grid_y < SPAWN_EXCLUDE_MAX:

            return False

        tile = self.matrix[grid_y][grid_x]

        return tile not in BLOCKING_TILES



    def random_spawn_cell(self, biome=None):

        rng = random.Random()

        for _ in range(120):

            gx = rng.randint(2, MAP_WIDTH - 3)

            gy = rng.randint(2, MAP_HEIGHT - 3)

            if not self.is_walkable_spawn(gx, gy):

                continue

            if biome and self.biome_at(gx, gy) != biome:

                continue

            return gx, gy

        return None, None

