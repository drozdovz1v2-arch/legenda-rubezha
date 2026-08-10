import pygame
import random
import math
from assets import create_slime_frames, create_boss_idle_frames, create_frost_slime_frames, create_ice_guardian_frames, create_wolf_frames, create_scorpion_frames, create_wraith_frames, create_colossus_frames
from status_effects import StatusEffectManager
from config import ENEMY_DAMAGE, ENEMY_COLLISION_INSET
from combat import deal_damage_to_player, tick_contact_cooldown, try_contact_hit
from collision import (
    move_and_collide,
    cached_line_of_sight,
    separation_force,
    steer_velocity,
)

SLIME_ANIM_DELAY = 10
BOSS_ANIM_DELAY = 14


def update_sprite_animation(sprite, anim_delay):
    if sprite.hit_flash > 0:
        sprite.hit_flash -= 1
        if sprite.hit_flash == 0:
            sprite.image = sprite.frames[sprite.anim_index]
        return

    sprite.anim_timer += 1
    if sprite.anim_timer >= anim_delay:
        sprite.anim_timer = 0
        sprite.anim_index = (sprite.anim_index + 1) % len(sprite.frames)
        sprite.image = sprite.frames[sprite.anim_index]
    elif sprite.image is not sprite.frames[sprite.anim_index]:
        sprite.image = sprite.frames[sprite.anim_index]


def flash_on_hit(sprite):
    sprite.hit_flash = 8
    sprite.image = sprite.frames[sprite.anim_index].copy()
    sprite.image.fill((255, 255, 255), special_flags=pygame.BLEND_RGB_ADD)


def apply_telegraph_visual(sprite):
    pulse = getattr(sprite, "telegraph_pulse", 0)
    sprite.telegraph_pulse = (pulse + 1) % 8
    if sprite.telegraph_pulse < 4:
        tinted = sprite.image.copy()
        tinted.fill((255, 70, 70), special_flags=pygame.BLEND_RGB_ADD)
        sprite.image = tinted


class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()

        self.frames = create_slime_frames()
        self.anim_index = 0
        self.anim_timer = random.randint(0, SLIME_ANIM_DELAY)
        self.hit_flash = 0
        self.image = self.frames[0].copy()
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.collision_inset = ENEMY_COLLISION_INSET
        self.speed = 1.6
        self.change_x = 0
        self.change_y = 0
        self.wander_timer = random.randint(20, 80)
        self.notice_radius = 220
        self.attack_radius = 28
        self.hp = 30
        self.max_hp = 30
        self.is_elite = False

        self.state = "patrol"
        self.aggro_timer = 0
        self.last_seen = None
        self.stuck_timer = 0
        self.dodge_timer = 0
        self.status = StatusEffectManager()
        self.contact_hit_timer = 0
        stats = ENEMY_DAMAGE["slime"]
        self.contact_damage = stats["contact"]
        self.contact_cooldown = stats["cooldown"]
        self.leash_to_biome = True
        self.knockback_resist = 0.0
        self._init_combat_state()

    def _init_combat_state(self):
        self.lunge_cooldown = random.randint(30, 90)
        self.lunge_timer = 0
        self.lunge_dir = (0.0, 1.0)
        self.lunge_power = 3.8
        self.lunge_min = 34
        self.lunge_max = 92
        self.enraged = False
        self.telegraph_pulse = 0
        self.combat_tag = "slime"

    def effective_speed(self):
        bonus = 1.12 if self.enraged else 1.0
        return self.speed * self.status.speed_multiplier() * bonus

    def _check_enrage(self):
        if self.enraged or self.hp > self.max_hp * 0.32:
            return
        self.enraged = True
        self.speed *= 1.15
        self.contact_cooldown = max(18, int(self.contact_cooldown * 0.82))

    def _try_start_lunge(self, distance, dx, dy, can_see):
        if self.lunge_timer > 0 or self.lunge_cooldown > 0:
            return False
        if not can_see or distance < self.lunge_min or distance > self.lunge_max:
            return False
        norm = max(1.0, math.hypot(dx, dy))
        self.lunge_dir = (dx / norm, dy / norm)
        self.lunge_timer = 22
        self.lunge_cooldown = random.randint(75, 115)
        return True

    def _process_lunge(self):
        if self.lunge_timer <= 0:
            if self.lunge_cooldown > 0:
                self.lunge_cooldown -= 1
            return None
        self.lunge_timer -= 1
        if self.lunge_timer > 14:
            apply_telegraph_visual(self)
            return (0.0, 0.0)
        return (
            self.lunge_dir[0] * self.lunge_power,
            self.lunge_dir[1] * self.lunge_power,
        )

    def _resolve_chase_movement(self, player, distance, dx, dy, spd, sep_x, sep_y, can_see):
        lunge_move = self._process_lunge()
        if lunge_move is None:
            if self._try_start_lunge(distance, dx, dy, can_see):
                lunge_move = (0.0, 0.0)
        if lunge_move is not None:
            return lunge_move[0] + sep_x, lunge_move[1] + sep_y

        if distance > self.attack_radius:
            cx, cy = steer_velocity(
                self.rect.centerx,
                self.rect.centery,
                player.rect.centerx,
                player.rect.centery,
                spd,
                sep_x,
                sep_y,
            )
            return cx, cy
        orbit_angle = math.atan2(dy, dx) + math.pi / 2
        return (
            math.cos(orbit_angle) * spd * 0.8 + sep_x,
            math.sin(orbit_angle) * spd * 0.8 + sep_y,
        )

    def wander(self):
        self.wander_timer -= 1
        if self.wander_timer <= 0:
            spd = self.effective_speed()
            self.change_x = random.choice([-spd, 0, spd])
            self.change_y = random.choice([-spd, 0, spd])
            self.wander_timer = random.randint(50, 130)

    def _mark_stuck(self, tilemap):
        old_pos = (self.rect.x, self.rect.y)
        move_and_collide(self, self.change_x, self.change_y, tilemap)
        if (self.rect.x, self.rect.y) == old_pos and (self.change_x or self.change_y):
            self.stuck_timer += 1
        else:
            self.stuck_timer = 0

        if self.stuck_timer >= 18:
            self.wander_timer = 0
            self.stuck_timer = 0
            self.dodge_timer = 24
            self.change_x, self.change_y = random.choice(
                [(self.speed, 0), (-self.speed, 0), (0, self.speed), (0, -self.speed)]
            )

    def update(self, player, tilemap, others):
        update_sprite_animation(self, SLIME_ANIM_DELAY)
        tick_contact_cooldown(self)
        spd = self.effective_speed()
        self.status.tick(self, on_damage=lambda dmg: self.take_damage(dmg))

        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery
        distance_sq = dx * dx + dy * dy
        distance = math.sqrt(distance_sq)
        notice_sq = self.notice_radius * self.notice_radius
        if distance_sq <= notice_sq:
            can_see = cached_line_of_sight(self, self.rect, player.rect, tilemap)
        else:
            can_see = False

        from world_zones import enemy_can_chase_player
        if not enemy_can_chase_player(self, player, tilemap):
            can_see = False
            if self.state in ("chase", "investigate"):
                self.state = "patrol"
                self.aggro_timer = 0
                self.last_seen = None

        if self.dodge_timer > 0:
            self.dodge_timer -= 1
            self.state = "dodge"
        elif can_see and distance < self.notice_radius and player.hp > 0:
            self.state = "chase"
            self.last_seen = player.rect.center
            self.aggro_timer = 150
        elif self.aggro_timer > 0 and self.last_seen:
            self.state = "investigate"
            self.aggro_timer -= 1
        else:
            self.state = "patrol"
            self.last_seen = None

        others = others.sprites() if hasattr(others, "sprites") else others
        if distance_sq <= notice_sq * 1.4:
            sep_x, sep_y = separation_force(self, others, radius=30, strength=1.4)
        else:
            sep_x, sep_y = 0.0, 0.0
        self._check_enrage()

        if self.state == "chase":
            self.change_x, self.change_y = self._resolve_chase_movement(
                player, distance, dx, dy, spd, sep_x, sep_y, can_see
            )
        elif self.state == "investigate":
            target_x, target_y = self.last_seen
            arrive_dist = math.hypot(target_x - self.rect.centerx, target_y - self.rect.centery)
            if arrive_dist < 12:
                self.state = "patrol"
                self.aggro_timer = 0
                self.wander()
            else:
                self.change_x, self.change_y = steer_velocity(
                    self.rect.centerx,
                    self.rect.centery,
                    target_x,
                    target_y,
                    spd * 0.85,
                    sep_x,
                    sep_y,
                )
        elif self.state == "dodge":
            pass
        else:
            self.wander()
            self.change_x += sep_x * 0.35
            self.change_y += sep_y * 0.35

        self._mark_stuck(tilemap)

        try_contact_hit(
            player, self, self.contact_damage, self.contact_cooldown, can_see=can_see
        )

    def take_damage(self, amount):
        self.hp -= amount
        flash_on_hit(self)
        if self.hp <= 0:
            self.kill()
            return True
        return False

    def make_elite(self):
        if self.is_elite:
            return
        self.is_elite = True
        self.max_hp = int(self.max_hp * 2.6)
        self.hp = self.max_hp
        self.speed *= 1.32
        self.contact_damage = max(1, int(self.contact_damage * 1.28))
        self.notice_radius += 60
        if hasattr(self, "lunge_power"):
            self.lunge_power *= 1.15
        for i, frame in enumerate(self.frames):
            tinted = frame.copy()
            tinted.fill((255, 190, 40, 50), special_flags=pygame.BLEND_RGBA_ADD)
            self.frames[i] = tinted
        self.image = self.frames[self.anim_index].copy()


class ForestWolf(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.frames = create_wolf_frames()
        self.image = self.frames[0].copy()
        self.speed = 2.8
        self.hp = 24
        self.max_hp = 24
        self.notice_radius = 280
        self.attack_radius = 22
        stats = ENEMY_DAMAGE["wolf"]
        self.contact_damage = stats["contact"]
        self.contact_cooldown = stats["cooldown"]
        self.lunge_power = 5.5
        self.lunge_min = 42
        self.lunge_max = 170
        self.lunge_cooldown = random.randint(20, 60)
        self.combat_tag = "wolf"

    def on_contact_extra(self, player):
        if random.random() < 0.45:
            player.status.apply("poison", 180, 1)


class DesertScorpion(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.frames = create_scorpion_frames()
        self.image = self.frames[0].copy()
        self.speed = 1.4
        self.hp = 35
        self.max_hp = 35
        self.notice_radius = 200
        self.attack_radius = 30
        stats = ENEMY_DAMAGE["scorpion"]
        self.contact_damage = stats["contact"]
        self.contact_cooldown = stats["cooldown"]
        self.sting_timer = 0
        self.sting_cooldown = random.randint(10, 50)
        self.combat_tag = "scorpion"

    def _process_sting(self, distance, dx, dy, can_see):
        if self.sting_timer > 0:
            self.sting_timer -= 1
            if self.sting_timer > 11:
                apply_telegraph_visual(self)
                return (0.0, 0.0)
            norm = max(1.0, math.hypot(dx, dy))
            return (dx / norm * 5.8, dy / norm * 5.8)
        if self.sting_cooldown > 0:
            self.sting_cooldown -= 1
            return None
        if can_see and 38 < distance < 115:
            self.sting_timer = 17
            self.sting_cooldown = random.randint(90, 130)
            return (0.0, 0.0)
        return None

    def _try_start_lunge(self, distance, dx, dy, can_see):
        return False

    def _resolve_chase_movement(self, player, distance, dx, dy, spd, sep_x, sep_y, can_see):
        sting_move = self._process_sting(distance, dx, dy, can_see)
        if sting_move is not None:
            return sting_move[0] + sep_x * 0.3, sting_move[1] + sep_y * 0.3
        return super()._resolve_chase_movement(
            player, distance, dx, dy, spd * 0.85, sep_x, sep_y, can_see
        )

    def on_contact_extra(self, player):
        player.status.apply("poison", 240, 2)
        if getattr(self, "sting_timer", 0) > 0 and self.sting_timer <= 11:
            deal_damage_to_player(player, max(4, self.contact_damage // 2))


class RuinWraith(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.frames = create_wraith_frames()
        self.image = self.frames[0].copy()
        self.speed = 2.2
        self.hp = 28
        self.max_hp = 28
        self.notice_radius = 300
        self.attack_radius = 24
        stats = ENEMY_DAMAGE["wraith"]
        self.contact_damage = stats["contact"]
        self.contact_cooldown = stats["cooldown"]
        self.blink_cooldown = random.randint(20, 80)
        self.combat_tag = "wraith"

    def _resolve_chase_movement(self, player, distance, dx, dy, spd, sep_x, sep_y, can_see):
        if self.blink_cooldown > 0:
            self.blink_cooldown -= 1
        elif can_see and distance > 115:
            self.blink_cooldown = random.randint(110, 150)
            self.rect.x += int(dx * 0.58)
            self.rect.y += int(dy * 0.58)
            flash_on_hit(self)
            apply_telegraph_visual(self)
            return (0.0, 0.0)
        move = super()._resolve_chase_movement(
            player, distance, dx, dy, spd * 1.05, sep_x, sep_y, can_see
        )
        if can_see and distance < 55 and random.random() < 0.02:
            strafe = math.atan2(dy, dx) + math.pi / 2
            return (
                math.cos(strafe) * spd * 1.3 + sep_x,
                math.sin(strafe) * spd * 1.3 + sep_y,
            )
        return move

    def on_contact_extra(self, player):
        player.status.apply("burn", 150, 1)


class FrostSlime(Enemy):
    """Ледяной слайм — быстрее, слабее, обитает на севере."""

    def __init__(self, x, y):
        super().__init__(x, y)
        self.frames = create_frost_slime_frames()
        self.image = self.frames[0].copy()
        self.speed = 2.0
        self.hp = 22
        self.max_hp = 22
        self.notice_radius = 260
        self.attack_radius = 26
        stats = ENEMY_DAMAGE["frost_slime"]
        self.contact_damage = stats["contact"]
        self.contact_cooldown = stats["cooldown"]
        self.burst_cooldown = random.randint(10, 60)
        self.burst_timer = 0
        self.combat_tag = "frost"

    def _resolve_chase_movement(self, player, distance, dx, dy, spd, sep_x, sep_y, can_see):
        if getattr(self, "burst_timer", 0) > 0:
            self.burst_timer -= 1
            apply_telegraph_visual(self)
            if self.burst_timer == 0 and hasattr(player, "status"):
                player.status.apply("freeze", 75, 1)
            return (0.0, 0.0)
        if self.burst_cooldown > 0:
            self.burst_cooldown -= 1
        elif can_see and distance < 72:
            self.burst_cooldown = random.randint(130, 170)
            self.burst_timer = 14
            apply_telegraph_visual(self)
            return (0.0, 0.0)
        move = super()._resolve_chase_movement(
            player, distance, dx, dy, spd, sep_x, sep_y, can_see
        )
        if can_see and distance < 90:
            return move[0] * 1.08, move[1] * 1.08
        return move


class Projectile(pygame.sprite.Sprite):
    def __init__(self, x, y, target_x, target_y):
        super().__init__()
        self.image = pygame.Surface((12, 12), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (0, 191, 255), (6, 6), 6)
        pygame.draw.circle(self.image, (255, 255, 255), (6, 6), 3)

        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

        dx = target_x - x
        dy = target_y - y
        distance = math.hypot(dx, dy)

        self.speed = 4.0
        self.change_x = (dx / distance) * self.speed if distance > 0 else self.speed
        self.change_y = (dy / distance) * self.speed if distance > 0 else 0

    def update(self, player, tilemap):
        self.rect.x += int(self.change_x)
        self.rect.y += int(self.change_y)

        if tilemap.rect_hits_blocking(self.rect):
            self.kill()
            return

        if self.rect.colliderect(player.rect) and not player.invulnerable:
            deal_damage_to_player(player, ENEMY_DAMAGE["boss_orb"]["hit"])
            self.kill()


class FrostProjectile(Projectile):
    def __init__(self, x, y, target_x, target_y):
        super().__init__(x, y, target_x, target_y)
        self.image = pygame.Surface((10, 10), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (160, 230, 255), (5, 5), 5)
        pygame.draw.circle(self.image, (255, 255, 255), (5, 5), 2)
        self.speed = 3.2
        dx = target_x - x
        dy = target_y - y
        distance = math.hypot(dx, dy)
        self.change_x = (dx / distance) * self.speed if distance > 0 else self.speed
        self.change_y = (dy / distance) * self.speed if distance > 0 else 0

    def update(self, player, tilemap):
        self.rect.x += int(self.change_x)
        self.rect.y += int(self.change_y)
        if tilemap.rect_hits_blocking(self.rect):
            self.kill()
            return
        if self.rect.colliderect(player.rect) and not player.invulnerable:
            deal_damage_to_player(player, ENEMY_DAMAGE["frost_orb"]["hit"])
            if hasattr(player, "status"):
                player.status.apply("freeze", 90, 1)
            self.kill()


class IceGuardian(pygame.sprite.Sprite):
    """Уникальный босс севера — Ледяной страж."""

    def __init__(self, x, y):
        super().__init__()
        self.frames = create_ice_guardian_frames()
        self.anim_index = 0
        self.anim_timer = random.randint(0, BOSS_ANIM_DELAY)
        self.hit_flash = 0
        self.image = self.frames[0].copy()
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.hp = 120
        self.max_hp = 120
        self.speed = 1.0
        self.change_x = 0
        self.change_y = 0
        self.shoot_cooldown = 40
        self.notice_radius = 380
        self.preferred_range = 130
        self.retreat_range = 60
        self.wander_timer = 60
        self.contact_hit_timer = 0
        stats = ENEMY_DAMAGE["ice_guardian"]
        self.contact_damage = stats["contact"]
        self.contact_cooldown = stats["cooldown"]
        self.knockback_resist = 0.78

    def take_damage(self, amount):
        self.hp -= amount
        flash_on_hit(self)
        if self.hp <= 0:
            self.kill()
            return True
        return False

    def update(self, player, tilemap, projectiles_group, enemies_group):
        update_sprite_animation(self, BOSS_ANIM_DELAY)
        tick_contact_cooldown(self)
        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery
        distance = math.hypot(dx, dy)
        can_see = cached_line_of_sight(self, self.rect, player.rect, tilemap)
        sprite_list = enemies_group.sprites() if hasattr(enemies_group, "sprites") else enemies_group
        others = [e for e in sprite_list if e is not self]
        sep_x, sep_y = separation_force(self, others, radius=44, strength=1.8)

        if can_see and distance < self.notice_radius and player.hp > 0:
            if distance < self.retreat_range:
                self.change_x, self.change_y = steer_velocity(
                    self.rect.centerx, self.rect.centery,
                    self.rect.centerx - dx, self.rect.centery - dy,
                    self.speed, sep_x, sep_y,
                )
            elif distance > self.preferred_range + 15:
                self.change_x, self.change_y = steer_velocity(
                    self.rect.centerx, self.rect.centery,
                    player.rect.centerx, player.rect.centery,
                    self.speed, sep_x, sep_y,
                )
            else:
                strafe = math.atan2(dy, dx) + math.pi / 2
                self.change_x = math.cos(strafe) * self.speed * 0.85 + sep_x
                self.change_y = math.sin(strafe) * self.speed * 0.85 + sep_y
            if self.shoot_cooldown <= 0:
                projectiles_group.add(
                    FrostProjectile(self.rect.centerx, self.rect.centery, player.rect.centerx, player.rect.centery)
                )
                self.shoot_cooldown = 55
        else:
            self.wander_timer -= 1
            if self.wander_timer <= 0:
                self.change_x = random.choice([-self.speed, 0, self.speed])
                self.change_y = random.choice([-self.speed, 0, self.speed])
                self.wander_timer = random.randint(70, 130)

        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
        move_and_collide(self, self.change_x, self.change_y, tilemap)
        can_see = cached_line_of_sight(self, self.rect, player.rect, tilemap)
        try_contact_hit(
            player, self, self.contact_damage, self.contact_cooldown, can_see=can_see
        )


class BlueBoss(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()

        self.frames = create_boss_idle_frames()
        self.anim_index = 0
        self.anim_timer = random.randint(0, BOSS_ANIM_DELAY)
        self.hit_flash = 0
        self.image = self.frames[0].copy()
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

        self.hp = 80
        self.max_hp = 80
        self.speed = 1.15
        self.change_x, self.change_y = 0, 0
        self.wander_timer = random.randint(20, 80)
        self.shoot_cooldown = random.randint(20, 50)
        self.notice_radius = 360
        self.preferred_range = 150
        self.retreat_range = 70
        self.contact_hit_timer = 0
        stats = ENEMY_DAMAGE["blue_boss"]
        self.contact_damage = stats["contact"]
        self.contact_cooldown = stats["cooldown"]
        self.knockback_resist = 0.78

    def take_damage(self, amount):
        self.hp -= amount
        flash_on_hit(self)
        if self.hp <= 0:
            self.kill()
            return True
        return False

    def update(self, player, tilemap, projectiles_group, enemies_group):
        update_sprite_animation(self, BOSS_ANIM_DELAY)
        tick_contact_cooldown(self)

        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery
        distance = math.hypot(dx, dy)
        can_see = cached_line_of_sight(self, self.rect, player.rect, tilemap)
        sprite_list = enemies_group.sprites() if hasattr(enemies_group, "sprites") else enemies_group
        others = [e for e in sprite_list if e is not self]
        sep_x, sep_y = separation_force(self, others, radius=40, strength=1.6)

        if can_see and distance < self.notice_radius and player.hp > 0:
            if distance < self.retreat_range:
                self.change_x, self.change_y = steer_velocity(
                    self.rect.centerx,
                    self.rect.centery,
                    self.rect.centerx - dx,
                    self.rect.centery - dy,
                    self.speed,
                    sep_x,
                    sep_y,
                )
            elif distance > self.preferred_range + 20:
                self.change_x, self.change_y = steer_velocity(
                    self.rect.centerx,
                    self.rect.centery,
                    player.rect.centerx,
                    player.rect.centery,
                    self.speed,
                    sep_x,
                    sep_y,
                )
            else:
                strafe = math.atan2(dy, dx) + math.pi / 2
                self.change_x = math.cos(strafe) * self.speed * 0.9 + sep_x
                self.change_y = math.sin(strafe) * self.speed * 0.9 + sep_y

            if self.shoot_cooldown <= 0:
                projectiles_group.add(
                    Projectile(self.rect.centerx, self.rect.centery, player.rect.centerx, player.rect.centery)
                )
                self.shoot_cooldown = 75 if distance < self.preferred_range else 95
        else:
            self.wander_timer -= 1
            if self.wander_timer <= 0:
                self.change_x = random.choice([-self.speed, 0, self.speed])
                self.change_y = random.choice([-self.speed, 0, self.speed])
                self.wander_timer = random.randint(60, 140)
            self.change_x += sep_x * 0.4
            self.change_y += sep_y * 0.4

        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

        move_and_collide(self, self.change_x, self.change_y, tilemap)

        try_contact_hit(
            player, self, self.contact_damage, self.contact_cooldown, can_see=can_see
        )


class SandColossus(pygame.sprite.Sprite):
    """Уникальный босс пустыни — Песчаный колосс."""

    def __init__(self, x, y):
        super().__init__()
        self.frames = create_colossus_frames()
        self.anim_index = 0
        self.anim_timer = random.randint(0, BOSS_ANIM_DELAY)
        self.hit_flash = 0
        self.image = self.frames[0].copy()
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.hp = 150
        self.max_hp = 150
        self.speed = 0.9
        self.change_x = 0
        self.change_y = 0
        self.shoot_cooldown = 50
        self.notice_radius = 400
        self.preferred_range = 110
        self.retreat_range = 55
        self.wander_timer = 70
        self.slam_cooldown = 120
        self.is_elite = False
        self.contact_hit_timer = 0
        stats = ENEMY_DAMAGE["sand_colossus"]
        self.contact_damage = stats["contact"]
        self.contact_cooldown = stats["cooldown"]
        self.knockback_resist = 0.82

    def take_damage(self, amount):
        self.hp -= amount
        flash_on_hit(self)
        if self.hp <= 0:
            self.kill()
            return True
        return False

    def on_contact_extra(self, player):
        player.status.apply("burn", 90, 1)

    def update(self, player, tilemap, projectiles_group, enemies_group):
        update_sprite_animation(self, BOSS_ANIM_DELAY)
        tick_contact_cooldown(self)
        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery
        distance = math.hypot(dx, dy)
        can_see = cached_line_of_sight(self, self.rect, player.rect, tilemap)
        sprite_list = enemies_group.sprites() if hasattr(enemies_group, "sprites") else enemies_group
        others = [e for e in sprite_list if e is not self]
        sep_x, sep_y = separation_force(self, others, radius=50, strength=2.0)

        if can_see and distance < self.notice_radius and player.hp > 0:
            if distance < self.retreat_range:
                self.change_x, self.change_y = steer_velocity(
                    self.rect.centerx, self.rect.centery,
                    self.rect.centerx - dx, self.rect.centery - dy,
                    self.speed, sep_x, sep_y,
                )
            elif distance > self.preferred_range + 20:
                self.change_x, self.change_y = steer_velocity(
                    self.rect.centerx, self.rect.centery,
                    player.rect.centerx, player.rect.centery,
                    self.speed, sep_x, sep_y,
                )
            else:
                strafe = math.atan2(dy, dx) + math.pi / 2
                self.change_x = math.cos(strafe) * self.speed * 0.7 + sep_x
                self.change_y = math.sin(strafe) * self.speed * 0.7 + sep_y
            if self.shoot_cooldown <= 0:
                projectiles_group.add(
                    Projectile(self.rect.centerx, self.rect.centery, player.rect.centerx, player.rect.centery)
                )
                self.shoot_cooldown = 65
            if self.slam_cooldown <= 0 and distance < 90:
                player.status.apply("burn", 120, 2)
                deal_damage_to_player(player, ENEMY_DAMAGE["sand_slam"]["hit"])
                self.slam_cooldown = 150
        else:
            self.wander_timer -= 1
            if self.wander_timer <= 0:
                self.change_x = random.choice([-self.speed, 0, self.speed])
                self.change_y = random.choice([-self.speed, 0, self.speed])
                self.wander_timer = random.randint(80, 140)

        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
        if self.slam_cooldown > 0:
            self.slam_cooldown -= 1
        move_and_collide(self, self.change_x, self.change_y, tilemap)
        try_contact_hit(
            player, self, self.contact_damage, self.contact_cooldown, can_see=can_see
        )
