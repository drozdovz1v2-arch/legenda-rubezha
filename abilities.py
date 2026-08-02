"""Активные способности — Q, R, 1."""

import math
import pygame

ABILITIES = {
    "fire_wave": {
        "name": "Огненная волна",
        "key_hint": "Q",
        "cooldown": 180,
        "unlock_level": 2,
        "color": (255, 120, 40),
        "desc": "Урон по области перед героем",
    },
    "arcane_shield": {
        "name": "Магический щит",
        "key_hint": "R",
        "cooldown": 360,
        "unlock_level": 4,
        "duration": 120,
        "color": (120, 180, 255),
        "desc": "Краткая неуязвимость",
    },
    "lightning": {
        "name": "Молния",
        "key_hint": "1",
        "cooldown": 300,
        "unlock_level": 6,
        "color": (255, 255, 120),
        "desc": "Удар по ближайшему врагу",
    },
}

KEY_MAP = {
    pygame.K_q: "fire_wave",
    pygame.K_r: "arcane_shield",
    pygame.K_1: "lightning",
}


class AbilityManager:
    def __init__(self):
        self.cooldowns = {aid: 0 for aid in ABILITIES}
        self.shield_timer = 0
        self.cast_flash = 0

    def reset(self):
        self.cooldowns = {aid: 0 for aid in ABILITIES}
        self.shield_timer = 0
        self.cast_flash = 0

    def update(self):
        for aid in self.cooldowns:
            if self.cooldowns[aid] > 0:
                self.cooldowns[aid] -= 1
        if self.shield_timer > 0:
            self.shield_timer -= 1
        if self.cast_flash > 0:
            self.cast_flash -= 1

    def is_unlocked(self, ability_id, player):
        req = ABILITIES[ability_id].get("unlock_level", 1)
        return player.level >= req

    def is_ready(self, ability_id, player):
        return self.is_unlocked(ability_id, player) and self.cooldowns[ability_id] <= 0

    @property
    def shield_active(self):
        return self.shield_timer > 0

    def try_cast(self, ability_id, game):
        if ability_id not in ABILITIES:
            return False
        if not self.is_ready(ability_id, game.player):
            return False

        spec = ABILITIES[ability_id]
        self.cooldowns[ability_id] = spec["cooldown"]
        self.cast_flash = 30

        if ability_id == "fire_wave":
            return self._cast_fire_wave(game)
        if ability_id == "arcane_shield":
            self.shield_timer = spec["duration"]
            game.quests._notify("Щит активирован!")
            game.effects.spawn_shield_burst(game.player.rect.centerx, game.player.rect.centery)
            return True
        if ability_id == "lightning":
            return self._cast_lightning(game)
        return False

    def _cast_fire_wave(self, game):
        player = game.player
        facing_map = {
            "up": (0, -1),
            "down": (0, 1),
            "left": (-1, 0),
            "right": (1, 0),
        }
        fx, fy = facing_map.get(player.facing, (0, 1))
        cx = player.rect.centerx + fx * 48
        cy = player.rect.centery + fy * 48
        game.effects.spawn_fire_wave(cx, cy, fx, fy)
        hit_any = False
        for enemy in list(game.enemies_group):
            dist = math.hypot(enemy.rect.centerx - cx, enemy.rect.centery - cy)
            if dist <= 72:
                dmg = 28 + player.level * 2
                if enemy.take_damage(dmg):
                    game.process_enemy_kill(enemy)
                else:
                    if hasattr(enemy, "status"):
                        enemy.status.apply("burn", 120, 1)
                hit_any = True
        if hit_any:
            game.audio.play_sfx("sword_hit")
        game.quests._notify("Огненная волна!")
        return True

    def _cast_lightning(self, game):
        player = game.player
        nearest = None
        best_dist = 99999
        for enemy in game.enemies_group:
            dist = math.hypot(enemy.rect.centerx - player.rect.centerx, enemy.rect.centery - player.rect.centery)
            if dist < best_dist and dist <= 220:
                best_dist = dist
                nearest = enemy
        if not nearest:
            game.quests._notify("Нет цели для молнии")
            self.cooldowns["lightning"] = 45
            return False
        dmg = 40 + player.level * 3
        game.effects.spawn_lightning(nearest.rect.centerx, nearest.rect.centery)
        if nearest.take_damage(dmg):
            game.process_enemy_kill(nearest)
        game.audio.play_sfx("sword_hit")
        game.quests._notify("Молния!")
        return True

    def to_dict(self):
        return {"cooldowns": dict(self.cooldowns), "shield_timer": self.shield_timer}

    def load_dict(self, data):
        if not data:
            return
        for aid, val in data.get("cooldowns", {}).items():
            if aid in self.cooldowns:
                self.cooldowns[aid] = int(val)
        self.shield_timer = int(data.get("shield_timer", 0))
