import pygame
import random

class Potion(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        
        # --- ПРОЦЕДУРНАЯ ГРАФИКА ФЛАКОНА ЗЕЛЬЯ ---
        self.image = pygame.Surface((16, 20), pygame.SRCALPHA)
        # Горлышко бутылки (прозрачно-серое)
        pygame.draw.rect(self.image, (200, 200, 220), (6, 0, 4, 6))
        # Пробка (коричневая)
        pygame.draw.rect(self.image, (139, 69, 19), (6, 0, 4, 2))
        # Колба (округлая нижняя часть)
        pygame.draw.circle(self.image, (200, 200, 220), (8, 13), 7)
        # Красная целебная жидкость внутри колбы
        pygame.draw.circle(self.image, (220, 20, 60), (8, 14), 5)
        # Блик на стекле (белая точка)
        pygame.draw.circle(self.image, (255, 255, 255), (6, 11), 1)
        
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        
        # Легкая анимация покачивания зелья на траве/песке
        self.bounce_timer = random.randint(0, 100)
        self.base_y = y

    def update(self):
        """Плавное покачивание зелья вверх-вниз, чтобы его было заметно"""
        self.bounce_timer += 0.05
        # Небольшой сдвиг по синусоиде
        self.rect.y = self.base_y + int(pygame.math.Vector2(0, 1).rotate(self.bounce_timer * 100).y * 3)
