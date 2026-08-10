import pygame
import math
from config import (
    PLAYER_SPEED,
    PLAYER_START_HP,
    PLAYER_START_DAMAGE,
    PLAYER_START_MAX_EXP,
    LEVEL_HP_BONUS,
    LEVEL_HEAL_RATIO,
    EXP_SCALING,
    PLAYER_COLLISION_INSET,
)
from assets import get_player_animations
from player_visuals import compose_player_image
from collision import move_and_collide
from status_effects import StatusEffectManager
from combat import angle_to_facing, facing_to_angle, compute_aim_angle

ATTACK_DURATION = 20
ATTACK_PHASES = 5
ATTACK_HIT_PHASE = 2
ATTACK_MOVE_MULT = 0.62
WALK_FRAME_DELAY = 7
BASE_ATTACK_COOLDOWN = 25
BASE_DASH_COOLDOWN = 45

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.animations = get_player_animations()
        self.facing = "down"
        self.attack_facing = "down"
        self.walk_frame = 0
        self.anim_counter = 0

        self.image = self.animations["idle"]["down"].copy()
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.collision_inset = PLAYER_COLLISION_INSET

        self.change_x = 0
        self.change_y = 0

        self.level = 1
        self.hp = PLAYER_START_HP
        self.max_hp = PLAYER_START_HP
        self.gold = 0
        self.exp = 0
        self.max_exp = PLAYER_START_MAX_EXP

        self.is_attacking = False
        self.attack_timer = 0
        self.attack_cooldown = 0
        self.attack_rect = pygame.Rect(0, 0, 0, 0)
        self.aim_angle = math.pi / 2
        self.attack_hit_done = False
        self.swing_flash = 0
        self.weapon_name = "Железный меч"
        self.weapon_base_damage = PLAYER_START_DAMAGE
        self.skill_attack_bonus = 0
        self.attack_damage = PLAYER_START_DAMAGE
        self.base_attack_range = 40
        self.attack_range_bonus = 0
        self.attack_range = 40
        self.purchased_weapons = ["Железный меч"]
        self.purchased_armor = []
        self.visual_armor_id = None
        self.potions_count = 0

        self.dash_unlocked = False
        self.is_dashing = False
        self.dash_timer = 0
        self.dash_cooldown = 0
        self.dash_direction = (0, 0)
        self.base_dash_speed = 11
        self.dash_speed_bonus = 0
        self.dash_speed = 11
        self.dash_duration = 10
        self.base_dash_iframes = 8
        self.dash_iframes_penalty = 0
        self.dash_iframes = 8
        self.title = ""

        self.skill_stacks = {}
        self.max_hp_skill_bonus = 0
        self.speed_multiplier = 1.0
        self.on_kill_heal = 0
        self.on_kill_damage = 0
        self.lifesteal_percent = 0.0
        self.life_drain_percent = 0.0
        self.thorn_damage = 0
        self.thorn_self_damage = 0
        self.gold_multiplier = 1.0
        self.exp_multiplier = 1.0
        self.potion_heal_bonus = 0
        self.potion_heal_mult = 1.0
        self.attack_cooldown_bonus = 0
        self.attack_cooldown_penalty = 0
        self.dash_cooldown_bonus = 0
        self.dash_cooldown_penalty = 0
        self.damage_reduction = 0.0
        self.damage_taken_mult = 1.0
        self.crit_chance_bonus = 0.0
        self.crit_damage_bonus = 0.0
        self.hp_regen_per_sec = 0.0
        self.hp_regen_accum = 0.0
        self.self_damage_on_attack = 0
        self.enemy_aggro_mult = 1.0
        self.equipment_crit_bonus = 0.0
        self.status = StatusEffectManager()
        self.ability_manager = None
        self.spawn_iframes = 0
        self._regen_frame_counter = 0

    def recalc_attack_damage(self):
        self.attack_damage = max(1, self.weapon_base_damage + self.skill_attack_bonus)

    def recalc_max_hp(self):
        without_skills = PLAYER_START_HP + (self.level - 1) * LEVEL_HP_BONUS
        self.max_hp = max(20, without_skills + self.max_hp_skill_bonus)
        self.hp = min(self.hp, self.max_hp)

    def set_weapon_stats(self, damage, attack_range):
        self.weapon_base_damage = damage
        self.base_attack_range = attack_range
        self.recalc_attack_damage()
        self.attack_range = max(24, self.base_attack_range + self.attack_range_bonus)

    def grant_spawn_protection(self, frames):
        self.spawn_iframes = max(self.spawn_iframes, int(frames))

    @property
    def spawn_protected(self):
        return self.spawn_iframes > 0

    @staticmethod
    def facing_from_delta(dx, dy):
        if abs(dx) > abs(dy):
            return "right" if dx > 0 else "left"
        if dy > 0:
            return "down"
        if dy < 0:
            return "up"
        return None

    def update_aim(self, world_x, world_y):
        self.aim_angle = compute_aim_angle(self.rect, world_x, world_y)

    def can_attack(self):
        return self.attack_cooldown <= 0 and not self.is_attacking and not self.is_dashing

    def try_begin_attack(self):
        if not self.can_attack():
            return False
        self.attack_facing = angle_to_facing(self.aim_angle)
        self.facing = self.attack_facing
        self.is_attacking = True
        self.attack_timer = ATTACK_DURATION
        self.attack_hit_done = False
        self.swing_flash = 14
        self.attack_cooldown = max(
            8,
            BASE_ATTACK_COOLDOWN - self.attack_cooldown_bonus + self.attack_cooldown_penalty,
        )
        return True

    def consume_attack_hit(self):
        if not self.is_attacking or self.attack_hit_done:
            return False
        elapsed = ATTACK_DURATION - self.attack_timer
        phase = min(ATTACK_PHASES - 1, (elapsed * ATTACK_PHASES) // ATTACK_DURATION)
        if phase >= ATTACK_HIT_PHASE:
            self.attack_hit_done = True
            return True
        return False

    def swing_progress(self):
        if not self.is_attacking:
            return 0.0
        elapsed = ATTACK_DURATION - self.attack_timer
        return max(0.0, min(1.0, elapsed / max(1, ATTACK_DURATION - 1)))

    def begin_attack(self, facing):
        self.aim_angle = facing_to_angle(facing)
        return self.try_begin_attack()
    def _update_facing(self):
        if self.is_attacking:
            return
        if self.change_x > 0:
            self.facing = "right"
        elif self.change_x < 0:
            self.facing = "left"
        elif self.change_y < 0:
            self.facing = "up"
        elif self.change_y > 0:
            self.facing = "down"
        else:
            self.facing = angle_to_facing(self.aim_angle)
    def _compose_frame(self, frame):
        facing = self.attack_facing if self.is_attacking else self.facing
        return compose_player_image(
            frame,
            facing,
            getattr(self, "visual_armor_id", None),
            self.weapon_name,
        )

    def _update_animation(self):
        if self.is_attacking:
            elapsed = ATTACK_DURATION - self.attack_timer
            phase = min(ATTACK_PHASES - 1, (elapsed * ATTACK_PHASES) // ATTACK_DURATION)
            frames = self.animations["attack"][self.attack_facing]
            self.image = self._compose_frame(frames[min(phase, len(frames) - 1)])
            return

        moving = self.change_x != 0 or self.change_y != 0
        if moving:
            self.anim_counter += 1
            if self.anim_counter >= WALK_FRAME_DELAY:
                self.anim_counter = 0
                self.walk_frame = (self.walk_frame + 1) % 4
            self.image = self._compose_frame(self.animations["walk"][self.facing][self.walk_frame])
        else:
            self.anim_counter = 0
            self.walk_frame = 0
            self.image = self._compose_frame(self.animations["idle"][self.facing])

    def handle_input(self):
        keys = pygame.key.get_pressed()
        self.change_x = 0
        self.change_y = 0

        if self.is_dashing:
            return

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.change_x = -int(PLAYER_SPEED * self.speed_multiplier * self.status.speed_multiplier())
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.change_x = int(PLAYER_SPEED * self.speed_multiplier * self.status.speed_multiplier())
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.change_y = -int(PLAYER_SPEED * self.speed_multiplier * self.status.speed_multiplier())
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.change_y = int(PLAYER_SPEED * self.speed_multiplier * self.status.speed_multiplier())

    def try_dash(self):
        if not self.dash_unlocked or self.dash_cooldown > 0 or self.is_attacking or self.is_dashing:
            return False
        dx, dy = self.change_x, self.change_y
        if dx == 0 and dy == 0:
            facing_map = {
                "up": (0, -1),
                "down": (0, 1),
                "left": (-1, 0),
                "right": (1, 0),
            }
            dx, dy = facing_map.get(self.facing, (0, 1))
        length = max(1.0, (dx * dx + dy * dy) ** 0.5)
        self.dash_direction = (dx / length, dy / length)
        self.is_dashing = True
        self.dash_timer = self.dash_duration
        self.dash_cooldown = max(
            12,
            BASE_DASH_COOLDOWN - self.dash_cooldown_bonus + self.dash_cooldown_penalty,
        )
        return True

    def apply_damage(self, amount):
        if amount <= 0 or self.invulnerable:
            return 0
        reduced = amount * (1.0 - self.damage_reduction) * self.damage_taken_mult
        dealt = max(1, int(round(reduced))) if reduced > 0 else 0
        if dealt <= 0:
            return 0
        self.hp = max(0, self.hp - dealt)
        if self.thorn_self_damage > 0:
            self.hp = max(0, self.hp - self.thorn_self_damage)
        return dealt

    def heal(self, amount):
        self.hp = min(self.max_hp, self.hp + amount)

    def _update_dash(self, tilemap):
        if self.dash_cooldown > 0:
            self.dash_cooldown -= 1
        if not self.is_dashing:
            return
        self.dash_timer -= 1
        move_x = int(self.dash_direction[0] * self.dash_speed)
        move_y = int(self.dash_direction[1] * self.dash_speed)
        move_and_collide(self, move_x, move_y, tilemap)
        if self.dash_timer <= 0:
            self.is_dashing = False

    @property
    def invulnerable(self):
        if self.spawn_iframes > 0:
            return True
        if self.ability_manager and self.ability_manager.shield_active:
            return True
        return self.is_dashing and self.dash_timer >= self.dash_duration - self.dash_iframes

    def _tick_hp_regen(self):
        if self.hp_regen_per_sec == 0 or self.hp <= 0:
            return
        self.hp_regen_accum += self.hp_regen_per_sec / 60.0
        if abs(self.hp_regen_accum) < 1.0:
            return
        delta = int(self.hp_regen_accum)
        self.hp_regen_accum -= delta
        if delta > 0:
            self.heal(delta)
        else:
            self.hp = max(0, self.hp + delta)

    def update(self, tilemap):
        if self.spawn_iframes > 0:
            self.spawn_iframes -= 1
        self._tick_hp_regen()
        self.status.tick(self, on_damage=lambda dmg: self.apply_damage(dmg))
        self.handle_input()
        self._update_facing()

        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
        if self.is_attacking:
            self.attack_timer -= 1
            if self.swing_flash > 0:
                self.swing_flash -= 1
            if self.attack_timer <= 0:
                self.is_attacking = False
        if self.is_dashing:
            self._update_dash(tilemap)
        else:
            if self.is_attacking:
                move_and_collide(
                    self,
                    int(self.change_x * ATTACK_MOVE_MULT),
                    int(self.change_y * ATTACK_MOVE_MULT),
                    tilemap,
                )
            else:
                move_and_collide(self, self.change_x, self.change_y, tilemap)
            self._update_dash(tilemap)

        self._update_animation()

    def reset_movement(self):
        self.change_x = 0
        self.change_y = 0
        self.is_attacking = False
        self.attack_timer = 0
        self.attack_hit_done = False
        self.swing_flash = 0
        self.is_dashing = False
        self.dash_timer = 0

    def reset_skills(self):
        from skill_effects import reset_skill_bonuses

        self.skill_stacks = {}
        reset_skill_bonuses(self)
        self.status.clear()

    def add_exp(self, amount):
        amount = int(amount * self.exp_multiplier)
        self.exp += amount
        if self.exp >= self.max_exp:
            self.exp -= self.max_exp
            self.level += 1
            self.max_exp = max(40, int(self.max_exp * EXP_SCALING))
            self.recalc_max_hp()
            heal_amount = max(6, int(self.max_hp * LEVEL_HEAL_RATIO))
            self.hp = min(self.max_hp, self.hp + heal_amount)
            return heal_amount
        return 0
