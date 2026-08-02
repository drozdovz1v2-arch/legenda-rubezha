import math
import random
import pygame


class Particle:
    __slots__ = ("x", "y", "vx", "vy", "color", "size", "lifetime", "gravity", "shrink")

    def __init__(self, x, y, vx, vy, color, size, lifetime, gravity=0.0, shrink=True):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.size = size
        self.lifetime = lifetime
        self.gravity = gravity
        self.shrink = shrink

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += self.gravity
        self.vx *= 0.96
        self.vy *= 0.96
        self.lifetime -= 1
        if self.shrink:
            self.size = max(0.5, self.size - 0.08)
        return self.lifetime > 0 and self.size > 0.3


_WEATHER_PROBE = pygame.Rect(0, 0, 2, 2)


class EffectsManager:
    def __init__(self):
        self.particles = []
        self.weather_particles = []
        self.weather_biome = None
        self.weather_timer = 0
        self.level_up_timer = 0
        self.relic_flash_timer = 0
        self._vignette_cache = {}
        self.particles_enabled = True
        self.screen_effects_enabled = True
        self.weather_enabled = True
        self.particle_multiplier = 1.0
        self._flash_surface = None

    def configure(self, particles_enabled=True, screen_effects_enabled=True, particle_multiplier=1.0, weather_enabled=True):
        self.particles_enabled = particles_enabled
        self.screen_effects_enabled = screen_effects_enabled
        self.weather_enabled = weather_enabled
        self.particle_multiplier = max(0.0, min(1.0, particle_multiplier))
        if not self.particles_enabled:
            self.particles.clear()
        if not self.weather_enabled:
            self.weather_particles.clear()

    def clear(self):
        self.particles.clear()
        self.weather_particles.clear()
        self.weather_biome = None
        self.level_up_timer = 0
        self.relic_flash_timer = 0

    def _scaled_count(self, base_count):
        if not self.particles_enabled or self.particle_multiplier <= 0:
            return 0
        return max(1, int(base_count * self.particle_multiplier)) if base_count > 0 else 0

    def spawn_hit_sparks(self, x, y, direction_x=0, direction_y=0):
        count = self._scaled_count(12)
        if count <= 0:
            return
        base_angle = math.atan2(direction_y, direction_x) if (direction_x or direction_y) else None
        for _ in range(count):
            if base_angle is not None:
                angle = base_angle + random.uniform(-0.9, 0.9)
            else:
                angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(1.5, 4.5)
            color = random.choice([(255, 255, 220), (255, 230, 120), (255, 255, 255), (200, 220, 255)])
            self.particles.append(
                Particle(
                    x + random.uniform(-4, 4),
                    y + random.uniform(-4, 4),
                    math.cos(angle) * speed,
                    math.sin(angle) * speed,
                    color,
                    random.uniform(2, 4),
                    random.randint(12, 22),
                    gravity=0.12,
                )
            )

    def spawn_death_cloud(self, x, y, tint=(220, 60, 80)):
        main_count = self._scaled_count(14)
        extra_count = self._scaled_count(6)
        for _ in range(main_count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(0.4, 1.8)
            shade = random.randint(-30, 40)
            color = (
                max(0, min(255, tint[0] + shade)),
                max(0, min(255, tint[1] + shade)),
                max(0, min(255, tint[2] + shade)),
            )
            self.particles.append(
                Particle(
                    x,
                    y,
                    math.cos(angle) * speed,
                    math.sin(angle) * speed - 0.5,
                    color,
                    random.uniform(5, 10),
                    random.randint(20, 32),
                    gravity=-0.04,
                    shrink=False,
                )
            )
        for _ in range(extra_count):
            self.particles.append(
                Particle(
                    x + random.uniform(-6, 6),
                    y + random.uniform(-6, 6),
                    random.uniform(-0.6, 0.6),
                    random.uniform(-1.2, -0.2),
                    (240, 240, 240),
                    random.uniform(4, 7),
                    random.randint(18, 28),
                    gravity=-0.02,
                    shrink=False,
                )
            )

    def spawn_potion_pickup(self, x, y):
        count = self._scaled_count(10)
        if count <= 0:
            return
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(0.8, 2.4)
            color = random.choice([(255, 120, 160), (180, 255, 180), (255, 220, 120)])
            self.particles.append(
                Particle(
                    x,
                    y,
                    math.cos(angle) * speed,
                    math.sin(angle) * speed - 1.2,
                    color,
                    random.uniform(2, 4),
                    random.randint(16, 28),
                    gravity=0.06,
                )
            )

    def spawn_heal_burst(self, x, y):
        count = self._scaled_count(16)
        if count <= 0:
            return
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(1.0, 3.0)
            color = random.choice([(120, 255, 160), (180, 255, 200), (255, 255, 220)])
            self.particles.append(
                Particle(
                    x,
                    y - 4,
                    math.cos(angle) * speed,
                    math.sin(angle) * speed - 1.5,
                    color,
                    random.uniform(2, 5),
                    random.randint(18, 30),
                    gravity=-0.03,
                )
            )
        if self.screen_effects_enabled:
            self.level_up_timer = max(self.level_up_timer, 24)

    def trigger_level_up_flash(self):
        if self.screen_effects_enabled:
            self.level_up_timer = 40

    def trigger_relic_pickup(self, x, y):
        count = self._scaled_count(20)
        if count > 0:
            for _ in range(count):
                angle = random.uniform(0, math.pi * 2)
                speed = random.uniform(1.2, 3.8)
                color = random.choice([(255, 215, 100), (180, 140, 255), (255, 240, 180)])
                self.particles.append(
                    Particle(
                        x,
                        y - 4,
                        math.cos(angle) * speed,
                        math.sin(angle) * speed - 1.2,
                        color,
                        random.uniform(2, 5),
                        random.randint(22, 36),
                        gravity=-0.02,
                    )
                )
        if self.screen_effects_enabled:
            self.relic_flash_timer = 35

    def update(self):
        if self.particles:
            write = 0
            particles = self.particles
            for idx in range(len(particles)):
                if particles[idx].update():
                    if write != idx:
                        particles[write] = particles[idx]
                    write += 1
            del particles[write:]
        if self.level_up_timer > 0:
            self.level_up_timer -= 1
        if self.relic_flash_timer > 0:
            self.relic_flash_timer -= 1

    def draw_particles(self, screen, camera):
        if not self.particles_enabled:
            return
        offset_x = camera.camera.x + camera.shake_offset[0]
        offset_y = camera.camera.y + camera.shake_offset[1]
        for particle in self.particles + self.weather_particles:
            sx = int(particle.x + offset_x)
            sy = int(particle.y + offset_y)
            size = max(1, int(particle.size))
            pygame.draw.circle(screen, particle.color, (sx, sy), size)

    def update_weather(self, biome, view_rect):
        if not self.particles_enabled or self.particle_multiplier <= 0 or not self.weather_enabled:
            self.weather_particles.clear()
            return
        if biome != self.weather_biome:
            self.weather_biome = biome
            self.weather_particles.clear()
        self.weather_timer += 1
        cap = max(6, int(28 * self.particle_multiplier))
        spawn_every = 3 if biome == "snow" else 4 if biome == "ruins" else 5 if biome == "desert" else 8
        if self.weather_timer % spawn_every == 0 and len(self.weather_particles) < cap:
            x = random.uniform(view_rect.left, view_rect.right)
            if biome == "snow":
                self.weather_particles.append(
                    Particle(x, view_rect.top - 8, random.uniform(-0.4, 0.4), random.uniform(1.2, 2.8),
                             (230, 240, 255), random.uniform(1.5, 3), 120, gravity=0.04, shrink=False)
                )
            elif biome == "desert":
                self.weather_particles.append(
                    Particle(x, random.uniform(view_rect.top, view_rect.bottom), random.uniform(1.5, 3.5), random.uniform(-0.2, 0.2),
                             (210, 180, 130), random.uniform(1, 2), 90, gravity=0, shrink=False)
                )
            elif biome == "ruins":
                self.weather_particles.append(
                    Particle(x, view_rect.top - 6, random.uniform(-0.3, 0.3), random.uniform(0.4, 1.0),
                             random.choice([(120, 100, 160), (80, 255, 200)]), random.uniform(1, 2), 80, gravity=0.01, shrink=False)
                )
            else:
                self.weather_particles.append(
                    Particle(x, view_rect.top - 6, random.uniform(-0.8, 0.8), random.uniform(0.6, 1.4),
                             random.choice([(80, 160, 70), (120, 180, 80)]), 2, 100, gravity=0.03, shrink=False)
                )
        alive = []
        probe = _WEATHER_PROBE
        pad = 40
        for p in self.weather_particles:
            p.lifetime -= 1
            p.x += p.vx
            p.y += p.vy
            p.vy += p.gravity
            if p.lifetime > 0:
                probe.x = int(p.x) - pad
                probe.y = int(p.y) - pad
                probe.width = pad * 2
                probe.height = pad * 2
                if view_rect.colliderect(probe):
                    alive.append(p)
                elif biome == "snow" and p.y < view_rect.bottom + pad:
                    alive.append(p)
        self.weather_particles = alive[:cap]

    def _get_vignette(self, width, height, edge):
        key = (width, height, edge)
        if key not in self._vignette_cache:
            surf = pygame.Surface((width, height), pygame.SRCALPHA)
            for i in range(edge):
                alpha = int(160 * (1 - i / edge))
                pygame.draw.rect(surf, (170, 0, 0, alpha), (0, i, width, 1))
                pygame.draw.rect(surf, (170, 0, 0, alpha), (0, height - 1 - i, width, 1))
                pygame.draw.rect(surf, (170, 0, 0, alpha), (i, 0, 1, height))
                pygame.draw.rect(surf, (170, 0, 0, alpha), (width - 1 - i, 0, 1, height))
            self._vignette_cache[key] = surf
        return self._vignette_cache[key]

    def draw_screen_overlays(self, screen, hp_ratio):
        if not self.screen_effects_enabled:
            return

        width, height = screen.get_size()
        if self._flash_surface is None or self._flash_surface.get_size() != (width, height):
            self._flash_surface = pygame.Surface((width, height), pygame.SRCALPHA)

        if self.level_up_timer > 0:
            progress = self.level_up_timer / 40
            alpha = int(130 * progress)
            self._flash_surface.fill((0, 0, 0, 0))
            self._flash_surface.fill((70, 255, 120, alpha))
            screen.blit(self._flash_surface, (0, 0))

        if self.relic_flash_timer > 0:
            progress = self.relic_flash_timer / 35
            alpha = int(110 * progress)
            self._flash_surface.fill((0, 0, 0, 0))
            self._flash_surface.fill((180, 140, 255, alpha))
            screen.blit(self._flash_surface, (0, 0))

        if hp_ratio <= 0.35:
            urgency = 1.0 - max(0.0, hp_ratio / 0.35)
            edge = int(24 + 56 * urgency)
            vignette = self._get_vignette(width, height, edge)
            pulse = 0.75 + 0.25 * math.sin(pygame.time.get_ticks() * 0.008)
            alpha = int(120 + 100 * urgency * pulse)
            if self._flash_surface is None or self._flash_surface.get_size() != (width, height):
                self._flash_surface = pygame.Surface((width, height), pygame.SRCALPHA)
            self._flash_surface.fill((0, 0, 0, 0))
            self._flash_surface.blit(vignette, (0, 0))
            self._flash_surface.set_alpha(alpha)
            screen.blit(self._flash_surface, (0, 0))

    def draw_night_overlay(self, screen, darkness):
        if not self.screen_effects_enabled or darkness <= 0.02:
            return
        width, height = screen.get_size()
        if self._flash_surface is None or self._flash_surface.get_size() != (width, height):
            self._flash_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        alpha = int(min(160, 180 * darkness))
        self._flash_surface.fill((0, 0, 0, 0))
        self._flash_surface.fill((15, 10, 40, alpha))
        screen.blit(self._flash_surface, (0, 0))

    def spawn_fire_wave(self, x, y, fx, fy):
        count = self._scaled_count(24)
        for _ in range(count):
            angle = math.atan2(fy, fx) + random.uniform(-0.8, 0.8)
            speed = random.uniform(2, 6)
            self.particles.append(
                Particle(x, y, math.cos(angle) * speed, math.sin(angle) * speed,
                         random.choice([(255, 120, 40), (255, 200, 60), (255, 80, 20)]),
                         random.uniform(3, 6), random.randint(20, 35), gravity=-0.02)
            )

    def spawn_lightning(self, x, y):
        count = self._scaled_count(16)
        for _ in range(count):
            self.particles.append(
                Particle(x + random.uniform(-8, 8), y + random.uniform(-20, 0),
                         random.uniform(-1, 1), random.uniform(2, 5),
                         (255, 255, 120), random.uniform(2, 4), random.randint(15, 30), gravity=0.05)
            )

    def spawn_shield_burst(self, x, y):
        count = self._scaled_count(20)
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(1, 3)
            self.particles.append(
                Particle(x, y, math.cos(angle) * speed, math.sin(angle) * speed,
                         (120, 180, 255), random.uniform(2, 4), random.randint(25, 40), gravity=0)
            )

    def spawn_meteor_strike(self, x, y):
        count = self._scaled_count(28)
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(2.5, 7.5)
            self.particles.append(
                Particle(
                    x + random.uniform(-6, 6),
                    y + random.uniform(-6, 6),
                    math.cos(angle) * speed,
                    math.sin(angle) * speed,
                    random.choice([(255, 120, 40), (255, 180, 60), (255, 70, 20), (255, 240, 180)]),
                    random.uniform(3, 7),
                    random.randint(18, 32),
                    gravity=0.08,
                )
            )

    def draw_event_overlays(self, screen, world_events):
        if not self.screen_effects_enabled or not world_events or not world_events.active:
            return
        width, height = screen.get_size()
        if self._flash_surface is None or self._flash_surface.get_size() != (width, height):
            self._flash_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        self._flash_surface.fill((0, 0, 0, 0))
        event_id = world_events.active
        if event_id == "fog":
            self._flash_surface.fill((120, 130, 150, 42))
        elif event_id == "blood_moon":
            pulse = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() * 0.004)
            self._flash_surface.fill((120, 20, 30, int(28 + 18 * pulse)))
        elif event_id == "meteor_shower":
            pulse = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() * 0.006)
            self._flash_surface.fill((80, 35, 10, int(18 + 12 * pulse)))
        elif event_id == "aurora":
            self._flash_surface.fill((40, 120, 100, 22))
        elif event_id == "golden_hour":
            self._flash_surface.fill((120, 90, 20, 24))
        elif event_id == "plague":
            self._flash_surface.fill((60, 100, 40, 26))
        elif event_id == "eclipse":
            self._flash_surface.fill((40, 30, 70, 34))
        screen.blit(self._flash_surface, (0, 0))

    def invalidate_vignette_cache(self):
        self._vignette_cache.clear()
        self._flash_surface = None
