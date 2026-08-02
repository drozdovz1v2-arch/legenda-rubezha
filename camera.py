import random
import pygame
from config import WORLD_WIDTH, WORLD_HEIGHT


class Camera:
    def __init__(self, width, height):
        self.camera = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height
        self.shake_offset = (0, 0)
        self.shake_timer = 0
        self.shake_intensity = 0

    def apply(self, entity):
        """Сдвигает прямоугольник объекта относительно камеры и тряски"""
        moved = entity.rect.move(self.camera.topleft)
        return moved.move(self.shake_offset)

    def apply_pos(self, x, y):
        return x + self.camera.x + self.shake_offset[0], y + self.camera.y + self.shake_offset[1]

    def add_shake(self, intensity=4, duration=10):
        self.shake_timer = max(self.shake_timer, duration)
        self.shake_intensity = max(self.shake_intensity, intensity)

    def update_shake(self):
        if self.shake_timer > 0:
            self.shake_timer -= 1
            shake = max(1, int(self.shake_intensity))
            self.shake_offset = (
                random.randint(-shake, shake),
                random.randint(-shake, shake),
            )
            if self.shake_timer < self.shake_intensity:
                self.shake_intensity *= 0.85
        else:
            self.shake_offset = (0, 0)
            self.shake_intensity = 0

    def update(self, target, current_w, current_h):
        """Центрирует камеру на игроке с учетом динамического размера экрана"""
        x = -target.rect.centerx + int(current_w / 2)
        y = -target.rect.centery + int(current_h / 2)

        x = min(0, x)
        y = min(0, y)
        x = max(-(self.width - current_w), x)
        y = max(-(self.height - current_h), y)

        self.camera.topleft = (x, y)
        self.update_shake()

    def world_view_rect(self, screen_w, screen_h, padding=64):
        world_x = -self.camera.x - self.shake_offset[0] - padding
        world_y = -self.camera.y - self.shake_offset[1] - padding
        return pygame.Rect(world_x, world_y, screen_w + padding * 2, screen_h + padding * 2)
