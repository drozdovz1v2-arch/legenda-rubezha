import math
import pygame
import sys
import random
import json
import os
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, WORLD_WIDTH, WORLD_HEIGHT, TILE_SIZE,
    MAP_WIDTH, MAP_HEIGHT, TILE_FLOOR, TILE_SAND, TILE_SNOW, TILE_RUINS,
    BIOME_BOUNDARY_X, SNOW_BOUNDARY_Y, RUINS_BOUNDARY_X, RUINS_BOUNDARY_Y,
    GAME_VERSION, GAME_TITLE, MAX_SLIMES, MAX_BOSSES, MAX_FROST, MAX_WOLVES, MAX_SCORPIONS, MAX_WRAITHS,
    RESPAWN_INTERVAL, CHEST_COUNT, CRIT_CHANCE, CRIT_MULTIPLIER,
    SPAWN_IFRAMES_NEW, SPAWN_IFRAMES_CONTINUE,
    PLAYER_START_HP, PLAYER_START_DAMAGE, PLAYER_START_MAX_EXP,
    ELITE_SPAWN_CHANCE, ELITE_SPAWN_CAP, RESPAWN_FILL_RATIO,
)
from player import Player
from tilemap import TileMap
from camera import Camera
from enemy import Enemy, BlueBoss, FrostSlime, IceGuardian, ForestWolf, DesertScorpion, RuinWraith, SandColossus
from loot import Potion
from chests import Chest
from audio_manager import AudioManager
from collision import resolve_group_separation, separate_player_from_enemies
from combat import find_attack_targets, draw_attack_aim, draw_attack_swing, draw_attack_sword_overlay, update_player_aim, preview_targets, draw_crosshair
from ui_theme import (
    AnimatedBackground,
    draw_menu_button,
    draw_title_header,
    draw_rounded_panel,
    draw_meta_chip,
    draw_menu_panel,
    draw_menu_footer,
)
from effects import EffectsManager
from daynight import DayNightCycle
from abilities import AbilityManager, KEY_MAP
from equipment import EquipmentManager, EquipmentDrop, roll_equipment_drop, EQUIPMENT
from achievements import AchievementManager
from world_events import WorldEventManager
from difficulty import DifficultyManager
from meta_progression import MetaProgression, SAVE_VERSION
from run_modifiers import RunModifierManager, ModifierPicker
from relics import RelicManager, RELICS
from skill_synergies import SynergyManager
from run_summary import draw_run_summary, build_run_stats, MetaMenu
from game_settings import (
    DEFAULT_FPS_LIMIT,
    DEFAULT_VSYNC,
    DEFAULT_QUALITY,
    DEFAULT_PARTICLES,
    DEFAULT_SCREEN_EFFECTS,
    DEFAULT_SHOW_FPS,
    DEFAULT_MUTE_ALL,
    DEFAULT_MUSIC_ENABLED,
    DEFAULT_SFX_ENABLED,
    DEFAULT_UI_SCALE,
    DEFAULT_CAMERA_SHAKE,
    DEFAULT_SHAKE_INTENSITY,
    DEFAULT_DAMAGE_NUMBERS,
    DEFAULT_SHOW_MINIMAP,
    DEFAULT_WEATHER,
    DEFAULT_NIGHT_OVERLAY,
    DEFAULT_DAY_SPEED,
    DEFAULT_ENEMY_PUSH,
    DEFAULT_SHOW_HINTS,
    DEFAULT_BRIGHTNESS,
    DEFAULT_FULLSCREEN,
    FPS_OPTIONS,
    DAY_SPEED_OPTIONS,
    UI_SCALE_OPTIONS,
    QUALITY_PRESETS,
    RESOLUTIONS,
    SETTING_DEFAULTS,
)
from settings_menu import SettingsMenu
from intro import IntroScreen
from finale import FinaleScreen
from hud import GameHUD
from quests import QuestManager, QUESTS
from npc import create_world_npcs, NPC
from dialog import DialogBox
from combo import ComboTracker
from shrines import spawn_shrines, SHRINE_OFFERS
from skills import SkillPicker, SKILLS, apply_skill_to_player, roll_skill_offers
from skill_effects import reapply_all_skill_stacks
from world_state import serialize_world, restore_world_state

if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAVE_PATH = os.path.join(BASE_DIR, "save.json")
CRASH_LOG_PATH = os.path.join(BASE_DIR, "crash_log.txt")

TUTORIAL_HINTS = (
    (420, "WASD — движение. ЛКМ — атака по прицелу."),
    (900, "Tab — журнал квестов и целей."),
    (1500, "Подойди к NPC, сундуку или святилищу и нажми E."),
    (2400, "Q / R / 1 — активные способности (открываются по сюжету)."),
)

class DamageText(pygame.sprite.Sprite):
    """Класс всплывающих и тающих цифр урона над врагами"""
    def __init__(self, x, y, amount, font, crit=False):
        super().__init__()
        text_str = f"-{amount}!" if crit else f"-{amount}"
        if crit:
            color = (255, 240, 80)
        elif amount == 50:
            color = (255, 215, 0)
        else:
            color = (255, 50, 50)
        self.image = font.render(text_str, True, color).convert_alpha()
        self.rect = self.image.get_rect()
        self.rect.center = (x, y - 20)
        self.y_speed = -1.2
        self.lifetime = 45
        self.alpha = 255

    def update(self):
        self.rect.y += int(self.y_speed)
        self.lifetime -= 1
        if self.lifetime < 25:
            self.alpha = max(0, self.alpha - 12)
            self.image.set_alpha(self.alpha)
        if self.lifetime <= 0 or self.alpha <= 0:
            self.kill()


class Game:
    def __init__(self):
        pygame.init()
        self.current_w = SCREEN_WIDTH
        self.current_h = SCREEN_HEIGHT
        self.screen = pygame.display.set_mode((self.current_w, self.current_h))
        pygame.display.set_caption(f"{GAME_TITLE} — {GAME_VERSION}")
        self.clock = pygame.time.Clock()
        
        self.font_large = pygame.font.SysFont("Arial", 36, bold=True)
        self.font_medium = pygame.font.SysFont("Arial", 24, bold=True)
        self.font_small = pygame.font.SysFont("Arial", 18)
        self.font_menu = pygame.font.SysFont("Arial", 20, bold=True)
        self.font_menu_sub = pygame.font.SysFont("Arial", 14)
        
        self.state = "MENU"
        self.menu_selection = 0
        self.game_initialized = False

        self.vol_master = 0.8
        self.vol_music = 0.5
        self.vol_sfx = 0.7
        self.active_slider = None 

        self.resolutions = RESOLUTIONS
        self.res_index = 2
        self.dropdown_open = False
        self.fullscreen = DEFAULT_FULLSCREEN
        self.fps_limit = DEFAULT_FPS_LIMIT
        self.fps_index = FPS_OPTIONS.index(DEFAULT_FPS_LIMIT) if DEFAULT_FPS_LIMIT in FPS_OPTIONS else 1
        self.vsync = DEFAULT_VSYNC
        self.quality = DEFAULT_QUALITY
        self.particles_enabled = DEFAULT_PARTICLES
        self.screen_effects_enabled = DEFAULT_SCREEN_EFFECTS
        self.show_fps = DEFAULT_SHOW_FPS
        self.mute_all = DEFAULT_MUTE_ALL
        self.music_enabled = DEFAULT_MUSIC_ENABLED
        self.sfx_enabled = DEFAULT_SFX_ENABLED
        self.ui_scale = DEFAULT_UI_SCALE
        self.camera_shake = DEFAULT_CAMERA_SHAKE
        self.shake_intensity = DEFAULT_SHAKE_INTENSITY
        self.damage_numbers = DEFAULT_DAMAGE_NUMBERS
        self.show_minimap = DEFAULT_SHOW_MINIMAP
        self.weather_enabled = DEFAULT_WEATHER
        self.night_overlay = DEFAULT_NIGHT_OVERLAY
        self.day_speed = DEFAULT_DAY_SPEED
        self.day_speed_index = DAY_SPEED_OPTIONS.index(DEFAULT_DAY_SPEED)
        self.enemy_push = DEFAULT_ENEMY_PUSH
        self.show_hints = DEFAULT_SHOW_HINTS
        self.brightness = DEFAULT_BRIGHTNESS
        self.ui_scale_index = UI_SCALE_OPTIONS.index(DEFAULT_UI_SCALE)
        self.settings_menu = SettingsMenu()

        self.menu_buttons = {}
        self.settings_buttons = {}
        self.dropdown_rects = [] 
        
        self.shop_buttons = {}
        self.shop_weapons = [
            {"name": "Стальной палаш", "price": 30, "damage": 25, "range": 60, "desc": "Урон: 25, Дальность: +50%"},
            {"name": "Клинок света", "price": 75, "damage": 50, "range": 80, "desc": "Урон: 50, Дальность: +100%"}
        ]
        
        self.projectiles_group = pygame.sprite.Group()
        self.loot_group = pygame.sprite.Group()
        self.chests_group = pygame.sprite.Group()
        self.damage_texts_group = pygame.sprite.Group()
        self.effects = EffectsManager()
        self.hud = GameHUD()
        self.quests = QuestManager()
        self.dialog = DialogBox()
        self.intro = IntroScreen()
        self.finale = FinaleScreen()
        self.story_finale_seen = False
        self._tutorial_step = 0
        self._tutorial_timer = 0
        self._hint_dash_shown = False
        self._last_world_event = None
        self.skill_picker = SkillPicker()
        self.pending_skill_picks = 0
        self.combo = ComboTracker()
        self.session_kills = 0
        self.daynight = DayNightCycle()
        self.abilities = AbilityManager()
        self.equipment = EquipmentManager()
        self.achievements = AchievementManager()
        self.world_events = WorldEventManager()
        self.difficulty = DifficultyManager()
        self.meta = MetaProgression()
        self.run_mods = RunModifierManager()
        self.relics = RelicManager()
        self.synergies = SynergyManager()
        self.modifier_picker = ModifierPicker()
        self.meta_menu = MetaMenu()
        self.run_souls_earned = 0
        self.pending_new_run = False
        self.equipment_drops_group = pygame.sprite.Group()
        self.shrines_group = pygame.sprite.Group()
        self.npcs_group = pygame.sprite.Group()
        self.nearby_shrine = None
        self.respawn_timer = RESPAWN_INTERVAL
        self._frame = 0
        self.nearby_npc = None
        self.nearby_chest = None
        self.ice_guardian_defeated = False
        self.sand_colossus_defeated = False
        self.pause_selection = 0
        self._settings_return = "MENU"
        self.menu_bg = AnimatedBackground()

        self.load_game()
        self.apply_performance_settings()
        self.apply_display_mode()
        self.audio = AudioManager(self.vol_master, self.vol_music, self.vol_sfx)
        self.apply_audio_settings()
        self.audio.sync_state_music(self.state)
        self._last_state = self.state

    def on_state_change(self, new_state):
        if new_state == self._last_state:
            return
        self._last_state = new_state
        if new_state == "SETTINGS":
            self.settings_menu.reset_scroll()
        if new_state == "PLAYING":
            self.audio.reset_biome()
        self.audio.sync_state_music(new_state)

    def set_state(self, new_state):
        self.on_state_change(new_state)
        self.state = new_state

    def sync_screen_size(self):
        """Синхронизирует логический размер с реальным буфером экрана."""
        self.current_w, self.current_h = self.screen.get_size()

    def apply_display_mode(self):
        if self.fullscreen:
            info = pygame.display.Info()
            size = (max(800, info.current_w), max(600, info.current_h))
            flags = pygame.FULLSCREEN
        else:
            size = self.resolutions[self.res_index]
            flags = 0
        self.screen = pygame.display.set_mode(
            size,
            flags,
            vsync=1 if self.vsync else 0,
        )
        self.sync_screen_size()
        self.effects.invalidate_vignette_cache()
        self.hud.invalidate_minimap_cache()
        self.rebuild_tile_cache()

    def rebuild_tile_cache(self):
        if getattr(self, "tilemap", None) and getattr(self, "screen", None):
            self.tilemap.build_chunk_cache(self.screen)

    def apply_performance_settings(self):
        preset = QUALITY_PRESETS.get(self.quality, QUALITY_PRESETS["medium"])
        self.effects.configure(
            particles_enabled=self.particles_enabled,
            screen_effects_enabled=self.screen_effects_enabled,
            particle_multiplier=preset["particle_multiplier"],
            weather_enabled=self.weather_enabled,
        )
        self.separation_iterations = preset["separation_iterations"]

    def apply_audio_settings(self):
        if not hasattr(self, "audio"):
            return
        master = 0.0 if self.mute_all else self.vol_master
        music = 0.0 if (self.mute_all or not self.music_enabled) else self.vol_music
        sfx = 0.0 if (self.mute_all or not self.sfx_enabled) else self.vol_sfx
        self.audio.set_volumes(master, music, sfx)

    def apply_vsync(self, value):
        self.vsync = value
        self.apply_display_mode()

    def apply_fullscreen(self, value):
        self.fullscreen = value
        self.apply_display_mode()

    def apply_particles(self, value):
        self.particles_enabled = value
        self.apply_performance_settings()

    def apply_screen_effects(self, value):
        self.screen_effects_enabled = value
        self.apply_performance_settings()

    def apply_weather(self, value):
        self.weather_enabled = value
        self.apply_performance_settings()

    def apply_music_enabled(self, value):
        self.music_enabled = value
        self.apply_audio_settings()

    def apply_sfx_enabled(self, value):
        self.sfx_enabled = value
        self.apply_audio_settings()

    def apply_mute_all(self, value):
        self.mute_all = value
        self.apply_audio_settings()

    def cycle_day_speed(self):
        self.day_speed_index = (self.day_speed_index + 1) % len(DAY_SPEED_OPTIONS)
        self.day_speed = DAY_SPEED_OPTIONS[self.day_speed_index]

    def cycle_ui_scale(self):
        self.ui_scale_index = (self.ui_scale_index + 1) % len(UI_SCALE_OPTIONS)
        self.ui_scale = UI_SCALE_OPTIONS[self.ui_scale_index]

    def reset_settings_defaults(self):
        SettingsMenu.apply_dict(self, SETTING_DEFAULTS)
        self.day_speed_index = DAY_SPEED_OPTIONS.index(self.day_speed)
        self.ui_scale_index = UI_SCALE_OPTIONS.index(self.ui_scale)
        self.apply_display_mode()
        self.apply_performance_settings()
        self.apply_audio_settings()

    def save_settings_only(self):
        if os.path.exists(SAVE_PATH):
            try:
                with open(SAVE_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = {}
        else:
            data = {}
        for key in SETTING_DEFAULTS:
            if hasattr(self, key):
                data[key] = getattr(self, key)
        data["game_initialized"] = self.game_initialized
        try:
            with open(SAVE_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Ошибка сохранения настроек: {e}")

    def get_settings_dict(self):
        return {key: getattr(self, key) for key in SETTING_DEFAULTS if hasattr(self, key)}

    def apply_quality_preset(self, quality):
        self.quality = quality
        preset = QUALITY_PRESETS[quality]
        self.particles_enabled = preset["particles"]
        self.screen_effects_enabled = preset["screen_effects"]
        self.weather_enabled = preset.get("weather", self.weather_enabled)
        self.apply_performance_settings()

    def cycle_fps_limit(self):
        self.fps_index = (self.fps_index + 1) % len(FPS_OPTIONS)
        self.fps_limit = FPS_OPTIONS[self.fps_index]

    def count_enemies(self):
        counts = {"slimes": 0, "bosses": 0, "frost": 0, "wolves": 0, "scorpions": 0, "wraiths": 0}
        for enemy in self.enemies_group:
            if isinstance(enemy, BlueBoss):
                counts["bosses"] += 1
            elif isinstance(enemy, FrostSlime):
                counts["frost"] += 1
            elif isinstance(enemy, ForestWolf):
                counts["wolves"] += 1
            elif isinstance(enemy, DesertScorpion):
                counts["scorpions"] += 1
            elif isinstance(enemy, RuinWraith):
                counts["wraiths"] += 1
            elif not isinstance(enemy, (IceGuardian, SandColossus)):
                counts["slimes"] += 1
        return counts

    def _elite_spawn_chance(self, biome_mult=1.0):
        bonus = (
            self.daynight.elite_chance_bonus
            + self.world_events.elite_bonus
            + self.difficulty.elite_chance_bonus()
            + self.run_mods.active.get("elite_bonus", 0.0)
        )
        return min(ELITE_SPAWN_CAP, ELITE_SPAWN_CHANCE * biome_mult + bonus)

    def _sync_difficulty_modifiers(self):
        self.run_mods.apply_to_difficulty(self.difficulty)
        self.difficulty.run_speed_mult = self.run_mods.active.get("enemy_speed_mult", 1.0)
        self.difficulty.event_damage_mult = max(1.0, self.world_events.damage_bonus)

    def _rescale_all_enemies(self):
        if not getattr(self, "enemies_group", None):
            return
        self._sync_difficulty_modifiers()
        level = self.player.level if self.player else 1
        aggro = getattr(self.player, "enemy_aggro_mult", 1.0) if self.player else 1.0
        for enemy in self.enemies_group:
            enemy.difficulty_scaled = False
            is_boss = isinstance(enemy, (BlueBoss, IceGuardian, SandColossus))
            self.difficulty.scale_enemy(
                enemy, is_boss=is_boss, player_level=level, aggro_mult=aggro
            )

    def _register_enemy(self, enemy, is_boss=False):
        self._sync_difficulty_modifiers()
        level = self.player.level if self.player else 1
        aggro = getattr(self.player, "enemy_aggro_mult", 1.0) if self.player else 1.0
        self.difficulty.scale_enemy(
            enemy, is_boss=is_boss, player_level=level, aggro_mult=aggro
        )
        self.enemies_group.add(enemy)

    def _sync_player_build(self):
        """Пересчитать статы скиллов поверх оружия и экипировки."""
        weapon_stats = {"Железный меч": (PLAYER_START_DAMAGE, 40)}
        for wpn in self.shop_weapons:
            weapon_stats[wpn["name"]] = (wpn["damage"], wpn["range"])
        dmg, rng = weapon_stats.get(self.player.weapon_name, (PLAYER_START_DAMAGE, 40))
        self.player.set_weapon_stats(dmg, rng)
        reapply_all_skill_stacks(self.player)

    def clear_run_save(self):
        """Удаляет прогресс забега из сохранения (roguelike — смерть стирает run)."""
        save_data = {
            **self.get_settings_dict(),
            "save_version": SAVE_VERSION,
            "meta": self.meta.to_dict(),
            "game_initialized": False,
        }
        try:
            with open(SAVE_PATH, "w", encoding="utf-8") as f:
                json.dump(save_data, f, ensure_ascii=False, indent=4)
        except OSError as exc:
            print(f"Не удалось очистить сохранение: {exc}")
        self.game_initialized = False

    def _apply_run_bonuses(self):
        self.run_mods.apply_to_player(self.player)
        self.meta.apply_run_start(self.player)
        self.relics.apply_all(self.player)

    def _finalize_run_death(self):
        if self.state == "GAMEOVER":
            return
        stats = build_run_stats(self)
        souls = self.meta.compute_run_souls(stats)
        souls = int(souls * self.run_mods.active.get("soul_mult", 1.0))
        souls += int(souls * getattr(self.player, "relic_soul_mult", 0))
        self.run_souls_earned = max(1, souls)
        self.meta.record_run_end(stats, self.run_souls_earned)
        self.achievements.update(self)
        self.clear_run_save()
        self.set_state("GAMEOVER")

    def begin_new_run_flow(self):
        self.run_souls_earned = 0
        self.clear_run_save()
        self.init_game_world(force=True, apply_bonuses=False)
        self.modifier_picker.open()

    def try_open_pending_skill_picker(self):
        if self.pending_skill_picks <= 0 or self.skill_picker.active:
            return
        if self.player.spawn_protected or self.dialog.active:
            return
        self.pending_skill_picks -= 1
        curse_chance = self.run_mods.active.get("curse_chance", 0.35)
        self.skill_picker.open(self.player, curse_chance=curse_chance)

    def grant_spawn_shield(self, frames, message=None):
        self.player.grant_spawn_protection(frames)
        self.effects.spawn_shield_burst(self.player.rect.centerx, self.player.rect.centery)
        if message:
            self.quests._notify(message)

    def enter_playing(self, spawn_frames=0, spawn_message=None):
        if spawn_frames > 0:
            self.grant_spawn_shield(spawn_frames, spawn_message)
        self.set_state("PLAYING")

    def sync_world_event_notify(self):
        active = self.world_events.active
        if active == self._last_world_event:
            return
        self._last_world_event = active
        if not active:
            return
        from world_events import EVENTS
        ev = EVENTS[active]
        self.quests._notify(f"⚡ {ev['name']}: {ev['desc']}")

    def update_tutorial_hints(self):
        if not self.show_hints or self.state != "PLAYING":
            return
        if self.dialog.active or self.skill_picker.active or self.game_simulation_paused():
            return
        self._tutorial_timer += 1
        while self._tutorial_step < len(TUTORIAL_HINTS):
            trigger, message = TUTORIAL_HINTS[self._tutorial_step]
            if self._tutorial_timer < trigger:
                break
            self.quests._notify(message)
            self._tutorial_step += 1
        if self.player.dash_unlocked and not self._hint_dash_shown:
            self.quests._notify("Shift — рывок с краткой неуязвимостью!")
            self._hint_dash_shown = True

    def apply_meteor_strike(self, x, y, radius, damage):
        self.effects.spawn_meteor_strike(x, y)
        if self.camera_shake and self.screen_effects_enabled:
            self.camera.add_shake(5, 10)
        px, py = self.player.rect.center
        if (px - x) ** 2 + (py - y) ** 2 <= (radius + 10) ** 2:
            if not self.player.spawn_protected and not self.player.invulnerable:
                dealt = self.player.apply_damage(damage)
                if dealt and self.damage_numbers:
                    self.damage_texts_group.add(
                        DamageText(px, py - 18, dealt, self.font_small)
                    )
        for enemy in list(self.enemies_group):
            ex, ey = enemy.rect.center
            if (ex - x) ** 2 + (ey - y) ** 2 > radius ** 2:
                continue
            dmg = max(4, damage // 2) if isinstance(
                enemy, (BlueBoss, IceGuardian, SandColossus)
            ) else damage
            if enemy.take_damage(dmg):
                self.process_enemy_kill(enemy)

    def spawn_enemies(self, limits=None):
        """Спавн врагов по биомам."""
        if limits is None:
            limits = {
                "slimes": MAX_SLIMES, "bosses": MAX_BOSSES, "frost": MAX_FROST,
                "wolves": MAX_WOLVES, "scorpions": MAX_SCORPIONS, "wraiths": MAX_WRAITHS,
            }
        limits = self.difficulty.scaled_limits(limits)
        cap_mult = self.run_mods.active.get("enemy_cap_mult", 1.0)
        if cap_mult != 1.0:
            limits = {k: max(1, int(v * cap_mult)) for k, v in limits.items()}
        counts = self.count_enemies()
        elite_bonus = self._elite_spawn_chance()
        for _ in range(200):
            if all(counts[k] >= limits[k] for k in limits):
                break
            gx, gy = self.tilemap.random_spawn_cell()
            if gx is None:
                continue
            biome = self.tilemap.biome_at(gx, gy)
            tile = self.tilemap.matrix[gy][gx]
            px, py = gx * TILE_SIZE + 4, gy * TILE_SIZE + 4
            if biome == "forest" and counts["slimes"] < limits["slimes"] and tile == TILE_FLOOR:
                if counts["wolves"] < limits["wolves"] and random.random() < 0.32:
                    enemy = ForestWolf(px, py)
                    if random.random() < self._elite_spawn_chance(0.9):
                        enemy.make_elite()
                    self._register_enemy(enemy)
                    counts["wolves"] += 1
                else:
                    enemy = Enemy(px, py)
                    if random.random() < elite_bonus:
                        enemy.make_elite()
                    self._register_enemy(enemy)
                    counts["slimes"] += 1
            elif biome == "desert" and tile == TILE_SAND:
                need_scorpions = counts["scorpions"] < limits["scorpions"]
                need_bosses = counts["bosses"] < limits["bosses"]
                if not need_scorpions and not need_bosses:
                    continue
                spawn_scorpion = need_scorpions and (
                    not need_bosses or random.random() < 0.58
                )
                if spawn_scorpion:
                    enemy = DesertScorpion(px, py)
                    if random.random() < self._elite_spawn_chance(0.85):
                        enemy.make_elite()
                    self._register_enemy(enemy)
                    counts["scorpions"] += 1
                elif need_bosses:
                    boss = BlueBoss(gx * TILE_SIZE + 2, gy * TILE_SIZE + 2)
                    self._register_enemy(boss, is_boss=True)
                    counts["bosses"] += 1
            elif biome == "snow" and counts["frost"] < limits["frost"] and tile == TILE_SNOW:
                enemy = FrostSlime(px, py)
                if random.random() < self._elite_spawn_chance(0.9):
                    enemy.make_elite()
                self._register_enemy(enemy)
                counts["frost"] += 1
            elif biome == "ruins" and counts["wraiths"] < limits["wraiths"] and tile == TILE_RUINS:
                enemy = RuinWraith(px, py)
                if random.random() < self._elite_spawn_chance(1.05):
                    enemy.make_elite()
                self._register_enemy(enemy)
                counts["wraiths"] += 1

    def spawn_chests(self, count=CHEST_COUNT):
        rng = random.Random(self.tilemap.seed + 1337)
        self.chests_group = pygame.sprite.Group()
        biomes = ["forest"] * 3 + ["desert"] * 3 + ["snow"] * 2 + ["ruins"] * 2
        placed = 0
        for biome in biomes:
            if placed >= count:
                break
            for _ in range(100):
                gx = rng.randint(2, MAP_WIDTH - 3)
                gy = rng.randint(2, MAP_HEIGHT - 3)
                if not self.tilemap.is_walkable_spawn(gx, gy):
                    continue
                if self.tilemap.biome_at(gx, gy) != biome:
                    continue
                chest = Chest(gx * TILE_SIZE + 4, gy * TILE_SIZE + 6, f"chest_{placed}")
                self.chests_group.add(chest)
                placed += 1
                break

    def spawn_ice_guardian(self):
        if self.ice_guardian_defeated:
            return
        if any(isinstance(e, IceGuardian) for e in self.enemies_group):
            return
        rng = random.Random(self.tilemap.seed + 404)
        for _ in range(120):
            gx = rng.randint(55, MAP_WIDTH - 4)
            gy = rng.randint(2, SNOW_BOUNDARY_Y - 2)
            if self.tilemap.is_walkable_spawn(gx, gy) and self.tilemap.biome_at(gx, gy) == "snow":
                self._register_enemy(IceGuardian(gx * TILE_SIZE, gy * TILE_SIZE), is_boss=True)
                return

    def spawn_sand_colossus(self):
        if self.sand_colossus_defeated:
            return
        if any(isinstance(e, SandColossus) for e in self.enemies_group):
            return
        rng = random.Random(self.tilemap.seed + 808)
        for _ in range(120):
            gx = rng.randint(BIOME_BOUNDARY_X + 4, MAP_WIDTH - 4)
            gy = rng.randint(SNOW_BOUNDARY_Y + 4, MAP_HEIGHT - 4)
            if self.tilemap.is_walkable_spawn(gx, gy) and self.tilemap.biome_at(gx, gy) == "desert":
                self._register_enemy(SandColossus(gx * TILE_SIZE, gy * TILE_SIZE), is_boss=True)
                return

    def open_chest(self, chest):
        loot = chest.open_chest()
        if not loot:
            return
        self.player.gold += loot.get("gold", 0)
        self.player.potions_count += loot.get("potions", 0)
        self.effects.spawn_hit_sparks(chest.rect.centerx, chest.rect.centery, 0, -1)
        self.audio.play_sfx("coin")
        if loot.get("potions"):
            self.audio.play_sfx("potion_pickup")
            self.effects.spawn_potion_pickup(self.player.rect.centerx, self.player.rect.centery)
        self.quests._notify(f"+{loot['gold']} золота" + (", зелье!" if loot.get("potions") else ""))

    def interact_with_shrine(self, shrine):
        choices = [
            {"id": o["id"], "label": o["label"]}
            for o in SHRINE_OFFERS
        ]

        def on_choice(choice_id, _choice):
            if choice_id == "heal":
                self.player.heal(45)
                self.quests._notify("Святилище: +45 HP")
            elif choice_id == "gold":
                self.player.gold += 35
                self.audio.play_sfx("coin")
                self.quests._notify("Святилище: +35 золота")
            elif choice_id == "skill":
                offers = roll_skill_offers(self.player, 1)
                if offers:
                    apply_skill_to_player(self.player, offers[0])
                    self.quests._notify(f"Судьба: {SKILLS[offers[0]]['name']}")
            elif choice_id == "curse":
                self.player.apply_damage(20)
                self.player.gold += 60
                self.audio.play_sfx("coin")
                self.quests._notify("Проклятие: −20 HP, +60 золота")
            shrine.mark_used()
            self.effects.spawn_hit_sparks(shrine.rect.centerx, shrine.rect.centery, 0, -1)

        self.dialog.open(
            "Древнее святилище",
            ["Алтарь предлагает силу — но каждый дар имеет цену."],
            choices=choices,
            on_choice=on_choice,
        )

    def setup_world_entities(self):
        self.npcs_group = create_world_npcs()

    def spawn_shrines(self):
        self.shrines_group = spawn_shrines(self.tilemap, count=4, seed=self.tilemap.seed)

    def ensure_world_content(self):
        if len(self.chests_group) == 0:
            self.spawn_chests()
        if len(self.shrines_group) == 0:
            self.spawn_shrines()
        if not self.ice_guardian_defeated and not any(isinstance(e, IceGuardian) for e in self.enemies_group):
            self.spawn_ice_guardian()
        if not self.sand_colossus_defeated and not any(isinstance(e, SandColossus) for e in self.enemies_group):
            self.spawn_sand_colossus()

    def get_current_biome(self):
        gx = self.player.rect.centerx // TILE_SIZE
        gy = self.player.rect.centery // TILE_SIZE
        return self.tilemap.biome_at(gx, gy)

    def try_respawn_enemies(self):
        self.respawn_timer -= 1
        if self.respawn_timer > 0:
            return
        self.respawn_timer = max(
            100,
            int(RESPAWN_INTERVAL / (
                self.daynight.spawn_multiplier
                * self.difficulty.respawn_multiplier()
                * self.run_mods.active.get("respawn_mult", 1.0)
            )),
        )
        counts = self.count_enemies()
        caps = {
            "slimes": MAX_SLIMES, "bosses": MAX_BOSSES, "frost": MAX_FROST,
            "wolves": MAX_WOLVES, "scorpions": MAX_SCORPIONS, "wraiths": MAX_WRAITHS,
        }
        caps = self.difficulty.scaled_limits(caps)
        cap_mult = self.run_mods.active.get("enemy_cap_mult", 1.0)
        if cap_mult != 1.0:
            caps = {k: max(1, int(v * cap_mult)) for k, v in caps.items()}

        def below_cap(key):
            return counts[key] < max(1, int(caps[key] * RESPAWN_FILL_RATIO))

        limits = dict(counts)
        changed = False
        tier = self.difficulty.tier

        if below_cap("slimes") or below_cap("wolves"):
            limits["slimes"] = counts["slimes"] + 2 + tier // 3
            limits["wolves"] = counts["wolves"] + 1 + tier // 4
            changed = True
        if below_cap("frost"):
            limits["frost"] = counts["frost"] + 2 + tier // 4
            changed = True
        if below_cap("wraiths"):
            limits["wraiths"] = counts["wraiths"] + 2 + tier // 5
            changed = True
        if below_cap("scorpions") or below_cap("bosses"):
            limits["scorpions"] = counts["scorpions"] + 2 + tier // 4
            limits["bosses"] = counts["bosses"] + 1 + max(0, tier // 6)
            changed = True

        if self.world_events.active == "invasion":
            limits["slimes"] = counts["slimes"] + 3 + tier // 2
            limits["frost"] = counts["frost"] + 1
            limits["wolves"] = counts["wolves"] + 2
            limits["scorpions"] = counts["scorpions"] + 1
            limits["wraiths"] = counts["wraiths"] + 1
            changed = True

        if changed:
            self.spawn_enemies(limits=limits)

    def apply_quest_rewards(self, rewards):
        if not rewards:
            return
        self.player.gold += rewards.get("gold", 0)
        if rewards.get("max_hp"):
            self.player.max_hp += rewards["max_hp"]
            self.player.hp = min(self.player.max_hp, self.player.hp + rewards["max_hp"])
        if rewards.get("unlocks_dash"):
            self.player.dash_unlocked = True
        if rewards.get("title"):
            self.player.title = rewards["title"]
            self.quests.player_title = rewards["title"]
        if rewards.get("quest_id") == "sand_titan" and not self.story_finale_seen:
            self.start_finale()

    def on_enemy_killed(self, enemy):
        if isinstance(enemy, IceGuardian):
            self.ice_guardian_defeated = True
            rewards = self.quests.increment("kill_ice_lord")
        elif isinstance(enemy, SandColossus):
            self.sand_colossus_defeated = True
            rewards = self.quests.increment("kill_colossus")
            self.achievements.unlock("colossus_down", self)
        elif isinstance(enemy, BlueBoss):
            rewards = self.quests.increment("kill_boss")
        elif isinstance(enemy, FrostSlime):
            rewards = self.quests.increment("kill_frost")
        elif isinstance(enemy, RuinWraith):
            rewards = self.quests.increment("kill_wraith")
        elif type(enemy) is Enemy:
            rewards = self.quests.increment("kill_slime")
        else:
            rewards = None
        self.apply_quest_rewards(rewards)

    def interact_with_npc(self, npc):
        if npc.role == "elder":
            self._dialog_elder(npc)
        elif npc.role == "merchant":
            self._dialog_merchant(npc)
        elif npc.role == "scout":
            self._dialog_scout(npc)
        elif npc.role == "mystic":
            self._dialog_mystic(npc)

    def _dialog_elder(self, npc):
        if self.quests.active_quest == "first_steps":
            prog = self.quests.progress.get("first_steps", 0)
            target = QUESTS["first_steps"]["target"]
            self.dialog.open(npc.display_name, [f"Прогресс: {prog}/{target} слаймов убито."])
            return
        if "first_steps" in self.quests.completed and "desert_hunt" not in self.quests.completed:
            if self.quests.active_quest == "desert_hunt":
                prog = self.quests.progress.get("desert_hunt", 0)
                target = QUESTS["desert_hunt"]["target"]
                self.dialog.open(npc.display_name, [f"Боссы пустыни: {prog}/{target}."])
                return

            def on_desert(choice_id, _choice):
                if choice_id == "accept":
                    self.quests.start_quest("desert_hunt")

            self.dialog.open(
                npc.display_name,
                ["Ты доказал силу в лесу.", "На востоке — синие стражи пустыни. Убей двоих."],
                choices=[
                    {"id": "accept", "label": "Принять «Охота на стражей»"},
                    {"id": "leave", "label": "Уйти"},
                ],
                on_choice=on_desert,
            )
            return
        if "first_steps" in self.quests.completed:
            self.dialog.open(npc.display_name, [
                "Лес стал спокойнее благодаря тебе.",
                "Отправляйся на север к разведчику или на восток в пустыню.",
            ])
            return

        def on_choice(choice_id, _choice):
            if choice_id == "accept":
                self.quests.start_quest("first_steps")

        self.dialog.open(
            npc.display_name,
            ["Странник, лес кишит слаймами.", "Убей 5 из них — научу рывку в бою."],
            choices=[
                {"id": "accept", "label": "Принять квест «Первые шаги»"},
                {"id": "leave", "label": "Уйти"},
            ],
            on_choice=on_choice,
        )

    def _dialog_merchant(self, npc):
        def on_choice(choice_id, _choice):
            if choice_id == "shop":
                self.set_state("SHOP")
            elif choice_id == "potion":
                if self.player.gold >= 10:
                    self.player.gold -= 10
                    self.player.potions_count += 1
                    self.audio.play_sfx("potion_pickup")
                    self.effects.spawn_potion_pickup(self.player.rect.centerx, self.player.rect.centery)

        self.dialog.open(
            npc.display_name,
            ["Лучшее оружие — в моём арсенале!", "Зелья лечат на 40 HP."],
            choices=[
                {"id": "shop", "label": "Открыть оружейную лавку"},
                {"id": "potion", "label": "Купить зелье (10 G)"},
                {"id": "leave", "label": "Уйти"},
            ],
            on_choice=on_choice,
        )

    def _dialog_scout(self, npc):
        if "frost_lord" in self.quests.completed:
            self.dialog.open(npc.display_name, ["Рубеж покорён. Легенды будут помнить тебя."])
            return
        if self.quests.active_quest == "frost_lord":
            self.dialog.open(npc.display_name, ["Ледяной страж где-то на дальнем севере. Будь осторожен."])
            return
        if "frost_peak" in self.quests.completed:
            def on_lord(choice_id, _choice):
                if choice_id == "accept":
                    self.quests.start_quest("frost_lord")

            self.dialog.open(
                npc.display_name,
                ["Ледяной страж пробудился!", "Уничтожь его — станешь Покорителем Рубежа."],
                choices=[
                    {"id": "accept", "label": "Принять «Повелитель льда»"},
                    {"id": "leave", "label": "Уйти"},
                ],
                on_choice=on_lord,
            )
            return
        if self.quests.active_quest == "frost_peak":
            prog = self.quests.progress.get("frost_peak", 0)
            target = QUESTS["frost_peak"]["target"]
            self.dialog.open(npc.display_name, [f"Ледяные твари: {prog}/{target}."])
            return
        if "desert_hunt" not in self.quests.completed:
            self.dialog.open(npc.display_name, ["Сначала докажи себя в пустыне."])
            return

        def on_choice(choice_id, _choice):
            if choice_id == "accept":
                self.quests.start_quest("frost_peak")

        self.dialog.open(
            npc.display_name,
            ["На севере — ледяные слаймы.", "Уничтожь 8 — получишь звание стража."],
            choices=[
                {"id": "accept", "label": "Принять «Ледяная вершина»"},
                {"id": "leave", "label": "Уйти"},
            ],
            on_choice=on_choice,
        )

    def _dialog_mystic(self, npc):
        if "sand_titan" in self.quests.completed:
            self.dialog.open(npc.display_name, ["Мир пробудился. Ты — его легенда."])
            return
        if self.quests.active_quest == "sand_titan":
            self.dialog.open(npc.display_name, ["Колосс бродит по пустыне на востоке. Сокруши его."])
            return
        if "ruins_awakening" in self.quests.completed:
            def on_titan(choice_id, _choice):
                if choice_id == "accept":
                    self.quests.start_quest("sand_titan")

            self.dialog.open(
                npc.display_name,
                ["Песчаный колосс блокирует торговые пути.", "Победи его — и мир станет свободнее."],
                choices=[
                    {"id": "accept", "label": "Принять «Песчаный титан»"},
                    {"id": "leave", "label": "Уйти"},
                ],
                on_choice=on_titan,
            )
            return
        if self.quests.active_quest == "ruins_awakening":
            prog = self.quests.progress.get("ruins_awakening", 0)
            target = QUESTS["ruins_awakening"]["target"]
            self.dialog.open(npc.display_name, [f"Призраки руин: {prog}/{target}."])
            return
        if "frost_lord" not in self.quests.completed:
            self.dialog.open(npc.display_name, ["Руины спят... Сначала покори ледяного стража."])
            return

        def on_ruins(choice_id, _choice):
            if choice_id == "accept":
                self.quests.start_quest("ruins_awakening")

        self.dialog.open(
            npc.display_name,
            ["Древние руины наполнились призраками.", "Очисти их — и откроется путь к колоссу."],
            choices=[
                {"id": "accept", "label": "Принять «Пробуждение руин»"},
                {"id": "leave", "label": "Уйти"},
            ],
            on_choice=on_ruins,
        )

    def save_game(self):
        """Сохраняет прогресс и настройки в JSON"""
        save_data = {
            **self.get_settings_dict(),
            "save_version": SAVE_VERSION,
            "meta": self.meta.to_dict(),
            "game_initialized": self.game_initialized,
        }
        if self.game_initialized:
            save_data.update({
                "player_lvl": self.player.level,
                "player_exp": self.player.exp,
                "player_max_exp": self.player.max_exp,
                "player_gold": self.player.gold,
                "player_hp": self.player.hp,
                "player_max_hp": self.player.max_hp,
                "player_weapon_name": self.player.weapon_name,
                "player_attack_damage": self.player.attack_damage,
                "player_attack_range": self.player.attack_range,
                "player_purchased_weapons": self.player.purchased_weapons,
                "player_potions": self.player.potions_count,
                "player_x": self.player.rect.x,
                "player_y": self.player.rect.y,
                "player_dash_unlocked": self.player.dash_unlocked,
                "player_title": self.player.title,
                "player_skill_stacks": dict(self.player.skill_stacks),
                "player_equipment": self.equipment.to_dict(),
                "relics": self.relics.to_dict(),
                "run_modifiers": self.run_mods.to_dict(),
                "synergies": self.synergies.to_dict(),
                "abilities": self.abilities.to_dict(),
                "combo": self.combo.to_dict(),
                "world_events": self.world_events.to_dict(),
                "daynight": self.daynight.to_dict(),
                "achievements": self.achievements.to_dict(),
                "difficulty": self.difficulty.to_dict(),
                "session_kills": self.session_kills,
                "story_finale_seen": self.story_finale_seen,
                "world": serialize_world(
                    self.tilemap,
                    self.enemies_group,
                    self.loot_group,
                    self.quests,
                    self.npcs_group,
                    self.chests_group,
                    self.shrines_group,
                    flags={
                        "ice_guardian_defeated": self.ice_guardian_defeated,
                        "sand_colossus_defeated": self.sand_colossus_defeated,
                    },
                ),
            })
        try:
            with open(SAVE_PATH, "w", encoding="utf-8") as f:
                json.dump(save_data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Ошибка сохранения: {e}")

    def load_game(self):
        """Загружает прогресс и настройки из JSON"""
        if not os.path.exists(SAVE_PATH):
            return
        try:
            with open(SAVE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            SettingsMenu.apply_dict(self, data)
            self.meta.load_dict(data.get("meta"))
            self.current_w, self.current_h = self.resolutions[self.res_index]
            if data.get("game_initialized", False):
                world_data = data.get("world")
                map_seed = world_data.get("map_seed") if world_data else None
                self.tilemap = TileMap(seed=map_seed)
                self.rebuild_tile_cache()
                self.player = Player(data.get("player_x", 0), data.get("player_y", 0))
                self.player.level = data.get("player_lvl", 1)
                self.player.exp = data.get("player_exp", 0)
                self.player.max_exp = data.get("player_max_exp", PLAYER_START_MAX_EXP)
                self.player.gold = data.get("player_gold", 0)
                self.player.weapon_name = data.get("player_weapon_name", "Железный меч")
                self.player.attack_range = data.get("player_attack_range", 40)
                self.player.purchased_weapons = data.get("player_purchased_weapons", ["Железный меч"])
                self.player.potions_count = data.get("player_potions", 0)
                self.player.dash_unlocked = data.get("player_dash_unlocked", False)
                self.player.title = data.get("player_title", "")
                self.player.skill_stacks = dict(data.get("player_skill_stacks", {}))
                self.equipment.reset()
                self._sync_player_build()
                self.equipment.load_dict(self.player, data.get("player_equipment"))
                self.relics.load_dict(data.get("relics"))
                self.run_mods.load_dict(data.get("run_modifiers"))
                self._run_day_speed_mult = self.run_mods.active.get("day_speed_mult", 1.0)
                self.synergies.load_dict(data.get("synergies"))
                self.synergies.reapply_after_load(self.player)
                self.relics.apply_all(self.player)
                self.abilities.load_dict(data.get("abilities"))
                self.combo.load_dict(data.get("combo"))
                self.world_events.load_dict(data.get("world_events"))
                self._last_world_event = self.world_events.active
                self.session_kills = int(data.get("session_kills", 0))
                self.story_finale_seen = bool(data.get("story_finale_seen", False))
                saved_hp = data.get("player_hp", PLAYER_START_HP)
                self.player.hp = min(saved_hp, self.player.max_hp)
                self.daynight.load_dict(data.get("daynight"))
                self.achievements.load_dict(data.get("achievements"))
                self.difficulty.load_dict(data.get("difficulty"))
                self._sync_difficulty_modifiers()
                self.player.ability_manager = self.abilities

                self.all_sprites = pygame.sprite.Group()
                self.all_sprites.add(self.player)
                self.loot_group = pygame.sprite.Group()
                self.chests_group = pygame.sprite.Group()
                self.shrines_group = pygame.sprite.Group()
                self.equipment_drops_group = pygame.sprite.Group()
                self.damage_texts_group = pygame.sprite.Group()
                self.projectiles_group = pygame.sprite.Group()
                self.enemies_group = pygame.sprite.Group()
                self.setup_world_entities()

                if world_data:
                    restore_world_state(self, world_data)
                else:
                    self.spawn_enemies()
                    self.quests.reset()
                self.ensure_world_content()
                self._rescale_all_enemies()
                if data.get("player_title"):
                    self.quests.player_title = data["player_title"]
                self.camera = Camera(WORLD_WIDTH, WORLD_HEIGHT)
                self.game_initialized = True
                self.respawn_timer = RESPAWN_INTERVAL
        except Exception as e:
            import traceback
            with open(CRASH_LOG_PATH, "w", encoding="utf-8") as log_file:
                log_file.write("Произошла критическая ошибка при загрузке:\n")
                log_file.write(f"Тип ошибки: {type(e).__name__}\n")
                log_file.write(f"Описание: {e}\n\n")
                log_file.write("Полный след ошибки (Traceback):\n")
                traceback.print_exc(file=log_file)
            print("Критический сбой! Подробный лог сохранен в файл crash_log.txt")
            pygame.quit()
            sys.exit()

    def init_game_world(self, force=False, apply_bonuses=True):
        if self.game_initialized and not force:
            return
        self.tilemap = TileMap()
        self.hud.invalidate_minimap_cache()
        self.rebuild_tile_cache()
        spawn_x = (WORLD_WIDTH // 2) - (TILE_SIZE // 2)
        spawn_y = (WORLD_HEIGHT // 2) - (TILE_SIZE // 2)
        self.player = Player(spawn_x, spawn_y)
        self.player.reset_skills()
        self.player.ability_manager = self.abilities
        self.all_sprites = pygame.sprite.Group()
        self.all_sprites.add(self.player)
        self.enemies_group = pygame.sprite.Group()
        self.projectiles_group = pygame.sprite.Group()
        self.loot_group = pygame.sprite.Group()
        self.chests_group = pygame.sprite.Group()
        self.shrines_group = pygame.sprite.Group()
        self.equipment_drops_group = pygame.sprite.Group()
        self.damage_texts_group = pygame.sprite.Group()
        self.effects.clear()
        self.quests.reset()
        self.combo.reset()
        self.session_kills = 0
        self.daynight.reset()
        self.abilities.reset()
        self.equipment.reset()
        self.achievements.reset()
        self.world_events.reset()
        self.difficulty.reset()
        self.run_mods.reset()
        self.relics.reset()
        self.synergies.reset()
        self.pending_skill_picks = 0
        self.story_finale_seen = False
        self._tutorial_step = 0
        self._tutorial_timer = 0
        self._hint_dash_shown = False
        self._last_world_event = None
        self._run_day_speed_mult = 1.0
        self.sand_colossus_defeated = False
        self.ice_guardian_defeated = False
        self.player.ability_manager = self.abilities
        self.setup_world_entities()

        self.spawn_enemies()
        self.ensure_world_content()
        self.camera = Camera(WORLD_WIDTH, WORLD_HEIGHT)
        self.game_initialized = True
        self.respawn_timer = RESPAWN_INTERVAL
        if apply_bonuses:
            self._apply_run_bonuses()
            self._sync_difficulty_modifiers()
            spec = self.run_mods.active
            self._run_day_speed_mult = spec.get("day_speed_mult", 1.0)

    def confirm_run_modifiers(self):
        self._apply_run_bonuses()
        self._sync_difficulty_modifiers()
        spec = self.run_mods.active
        self._run_day_speed_mult = spec.get("day_speed_mult", 1.0)
        self._rescale_all_enemies()
        self.start_with_intro()

    def draw_menu(self):
        self.menu_bg.draw(self.screen, self.current_w, self.current_h)
        draw_title_header(
            self.screen, self.current_w, self.current_h,
            GAME_TITLE.upper(), GAME_VERSION,
            self.font_large, self.font_small,
        )
        chip_w, chip_h = 118, 44 if self.meta.lifetime_runs > 0 else 32
        draw_meta_chip(
            self.screen,
            pygame.Rect(self.current_w - chip_w - 24, 20, chip_w, chip_h),
            self.meta.souls,
            self.meta.lifetime_runs,
            self.font_menu_sub,
        )

        if self.modifier_picker.active or self.meta_menu.active:
            return

        mouse_pos = pygame.mouse.get_pos()
        if self.game_initialized:
            items = [
                {"label": "ПРОДОЛЖИТЬ"},
                {"label": "НОВЫЙ ЗАБЕГ"},
                {"label": "ДРЕВО ДУШ"},
                {"label": "МАГАЗИН"},
                {"label": "НАСТРОЙКИ"},
                {"label": "ВЫХОД"},
            ]
        else:
            items = [
                {"label": "НАЧАТЬ ЗАБЕГ"},
                {"label": "ДРЕВО ДУШ"},
                {"label": "МАГАЗИН", "locked": True},
                {"label": "НАСТРОЙКИ"},
                {"label": "ВЫХОД"},
            ]

        btn_w, btn_h = 340, 50
        btn_gap = 8
        panel_pad_x, panel_pad_y = 20, 18
        list_h = len(items) * btn_h + (len(items) - 1) * btn_gap
        panel_w = btn_w + panel_pad_x * 2
        panel_h = list_h + panel_pad_y * 2
        panel_x = self.current_w // 2 - panel_w // 2
        header_bottom = max(130, int(self.current_h * 0.18))
        footer_top = self.current_h - 40
        panel_y = header_bottom + max(8, (footer_top - header_bottom - panel_h) // 2)
        panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
        draw_menu_panel(self.screen, panel_rect)

        list_x = panel_x + panel_pad_x
        start_y = panel_y + panel_pad_y

        self.menu_buttons = {}
        for i, item in enumerate(items):
            rect = pygame.Rect(list_x, start_y + i * (btn_h + btn_gap), btn_w, btn_h)
            locked = item.get("locked", False)
            hovered = not locked and rect.collidepoint(mouse_pos)
            selected = i == self.menu_selection
            if hovered:
                self.menu_selection = i
            draw_menu_button(
                self.screen, rect, item["label"], self.font_menu, self.font_menu_sub,
                selected=selected, hovered=hovered, locked=locked,
            )
            self.menu_buttons[i] = rect if not locked else pygame.Rect(0, 0, 0, 0)

        draw_menu_footer(self.screen, self.current_w, self.current_h, self.font_menu_sub)

    def draw_slider(self, label, y_pos, value, slider_id):
        mouse_pos = pygame.mouse.get_pos()
        slider_width = 250
        x_start = (self.current_w // 2) - (slider_width // 2) + 50
        track_rect = pygame.Rect(x_start, y_pos, slider_width, 6)
        pygame.draw.rect(self.screen, (80, 80, 90), track_rect)
        lbl_surf = self.font_small.render(f"{label}: {int(value * 100)}%", True, (255, 255, 255))
        self.screen.blit(lbl_surf, (x_start - 240, y_pos - 8))
        handle_x = x_start + int(value * slider_width)
        handle_center = (handle_x, y_pos + 3)
        handle_radius = 8
        is_hovered = (handle_x - handle_radius <= mouse_pos[0] <= handle_x + handle_radius and
                      y_pos + 3 - handle_radius <= mouse_pos[1] <= y_pos + 3 + handle_radius)
        color = (0, 255, 255) if (is_hovered or self.active_slider == slider_id) else (200, 200, 200)
        pygame.draw.circle(self.screen, color, handle_center, handle_radius)
        self.settings_buttons[slider_id] = pygame.Rect(x_start, y_pos - 10, slider_width, 26)

    def draw_toggle(self, label, y_pos, enabled, toggle_id):
        mouse_pos = pygame.mouse.get_pos()
        lbl = self.font_small.render(label, True, (255, 255, 255))
        self.screen.blit(lbl, (self.current_w // 2 - 240, y_pos + 2))
        box = pygame.Rect(self.current_w // 2 - 40, y_pos, 24, 24)
        self.settings_buttons[toggle_id] = box
        box_color = (60, 50, 70) if box.collidepoint(mouse_pos) else (45, 35, 55)
        pygame.draw.rect(self.screen, box_color, box, border_radius=4)
        border = (0, 220, 220) if enabled else (100, 100, 110)
        pygame.draw.rect(self.screen, border, box, 2, border_radius=4)
        if enabled:
            pygame.draw.line(self.screen, (0, 255, 255), (box.x + 5, box.y + 5), (box.right - 5, box.bottom - 5), 3)
            pygame.draw.line(self.screen, (0, 255, 255), (box.right - 5, box.top + 5), (box.x + 5, box.bottom - 5), 3)

    def draw_option_button(self, label, rect, button_id, active=False):
        mouse_pos = pygame.mouse.get_pos()
        self.settings_buttons[button_id] = rect
        bg = (0, 120, 120) if active else ((60, 50, 70) if rect.collidepoint(mouse_pos) else (45, 35, 55))
        pygame.draw.rect(self.screen, bg, rect, border_radius=4)
        pygame.draw.rect(self.screen, (0, 204, 204), rect, 1, border_radius=4)
        txt = self.font_small.render(label, True, (255, 255, 255))
        self.screen.blit(txt, txt.get_rect(center=rect.center))

    def draw_settings(self):
        self.settings_menu.draw(self.screen, self)

    def handle_settings_events(self, event):
        result = self.settings_menu.handle_event(event, self)
        if result == "back":
            self.set_state(getattr(self, "_settings_return", "MENU"))

    def draw_shop(self):
        self.screen.fill((25, 30, 25))
        mouse_pos = pygame.mouse.get_pos()
        title_text = self.font_large.render("ОРУЖЕЙНАЯ ЛАВКА", True, (255, 215, 0))
        self.screen.blit(title_text, title_text.get_rect(center=(self.current_w // 2, self.current_h // 6)))
        gold_text = self.font_medium.render(f"Ваше золото: {self.player.gold} G", True, (255, 255, 0))
        self.screen.blit(gold_text, gold_text.get_rect(center=(self.current_w // 2, self.current_h // 4)))
        for i, wpn in enumerate(self.shop_weapons):
            card_rect = pygame.Rect(self.current_w // 2 - 250, self.current_h // 3 + i * 110, 500, 90)
            self.shop_buttons[wpn["name"]] = card_rect
            if wpn["name"] in self.player.purchased_weapons:
                bg_color, border_color, status_txt = (35, 45, 35), (0, 180, 0), "ЭКИПИРОВАНО" if self.player.weapon_name == wpn["name"] else "КУПЛЕНО (Клик для экипировки)"
            elif self.player.gold >= wpn["price"]:
                bg_color, border_color, status_txt = ((45, 55, 45), (255, 215, 0), f"КУПИТЬ: {wpn['price']} G") if card_rect.collidepoint(mouse_pos) else ((35, 40, 35), (150, 130, 0), f"КУПИТЬ: {wpn['price']} G")
            else:
                bg_color, border_color, status_txt = (30, 30, 30), (100, 50, 50), f"НЕДОСТАТОЧНО ЗОЛОТА ({wpn['price']} G)"
            pygame.draw.rect(self.screen, bg_color, card_rect, border_radius=6)
            pygame.draw.rect(self.screen, border_color, card_rect, 2, border_radius=6)
            name_surf = self.font_medium.render(wpn["name"], True, (255, 255, 255))
            desc_surf = self.font_small.render(wpn["desc"], True, (180, 180, 180))
            stat_surf = self.font_small.render(status_txt, True, border_color)
            self.screen.blit(name_surf, (card_rect.x + 20, card_rect.y + 15))
            self.screen.blit(desc_surf, (card_rect.x + 20, card_rect.y + 50))
            self.screen.blit(stat_surf, (card_rect.right - stat_surf.get_width() - 20, card_rect.y + 35))
        cur_surf = self.font_small.render(f"Сейчас в руках: {self.player.weapon_name}", True, (200, 200, 200))
        self.screen.blit(cur_surf, cur_surf.get_rect(center=(self.current_w // 2, self.current_h - 120)))
        back_rect = pygame.Rect(self.current_w // 2 - 100, self.current_h - 70, 200, 40)
        self.shop_buttons["back"] = back_rect
        b_color = (255, 255, 255) if back_rect.collidepoint(mouse_pos) else (150, 150, 150)
        back_surf = self.font_medium.render("НАЗАД В МЕНЮ", True, b_color)
        self.screen.blit(back_surf, back_surf.get_rect(center=back_rect.center))
        
    def handle_shop_events(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.set_state("PLAYING" if self.game_initialized else "MENU")
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            if self.shop_buttons.get("back") and self.shop_buttons["back"].collidepoint(pos):
                self.set_state("PLAYING" if self.game_initialized else "MENU")
                return
            for wpn in self.shop_weapons:
                if self.shop_buttons.get(wpn["name"]) and self.shop_buttons[wpn["name"]].collidepoint(pos):
                    if wpn["name"] in self.player.purchased_weapons:
                        self.player.weapon_name = wpn["name"]
                        self.player.set_weapon_stats(wpn["damage"], wpn["range"])
                    elif self.player.gold >= wpn["price"]:
                        self.player.gold -= wpn["price"]
                        self.player.purchased_weapons.append(wpn["name"])
                        self.player.weapon_name = wpn["name"]
                        self.player.set_weapon_stats(wpn["damage"], wpn["range"])
                        
    def screen_to_world(self, screen_pos):
        sx, sy = screen_pos
        return (
            sx - self.camera.camera.x - self.camera.shake_offset[0],
            sy - self.camera.camera.y - self.camera.shake_offset[1],
        )

    def try_player_attack(self):
        if not self.player.try_begin_attack():
            return False
        self.audio.play_sfx("sword_swing")
        return True

    def resolve_player_attack(self):
        targets = find_attack_targets(
            self.player, self.player.aim_angle, self.enemies_group, self.tilemap
        )
        if not targets:
            return
        self.audio.play_sfx("sword_hit")
        for enemy in targets:
            hit_dx = enemy.rect.centerx - self.player.rect.centerx
            hit_dy = enemy.rect.centery - self.player.rect.centery
            self.effects.spawn_hit_sparks(enemy.rect.centerx, enemy.rect.centery, hit_dx, hit_dy)
            damage, is_crit = self.roll_attack_damage(enemy)
            dmg_pop = DamageText(enemy.rect.centerx, enemy.rect.top, damage, self.font_small, crit=is_crit)
            if self.damage_numbers:
                self.damage_texts_group.add(dmg_pop)
            if is_crit:
                self.effects.spawn_hit_sparks(
                    enemy.rect.centerx, enemy.rect.centery - 8, hit_dx, hit_dy - 1
                )
            if getattr(self.player, "relic_poison", False) and hasattr(enemy, "status"):
                enemy.status.apply("poison", 120, 1)
            freeze_chance = getattr(self.player, "relic_freeze_chance", 0)
            if freeze_chance and random.random() < freeze_chance and hasattr(enemy, "status"):
                enemy.status.apply("freeze", 60, 1)
            killed = enemy.take_damage(damage)
            if self.player.lifesteal_percent > 0 and not killed:
                steal = max(1, int(damage * self.player.lifesteal_percent))
                self.player.heal(steal)
            if self.player.life_drain_percent > 0:
                drain = max(1, int(damage * self.player.life_drain_percent))
                self.player.apply_damage(drain)
            if self.player.self_damage_on_attack > 0:
                self.player.apply_damage(self.player.self_damage_on_attack)
            if killed:
                self.process_enemy_kill(enemy)

    def roll_attack_damage(self, enemy=None):
        base = self.player.attack_damage
        if enemy is not None and isinstance(enemy, (BlueBoss, IceGuardian, SandColossus)):
            boss_bonus = getattr(self.player, "relic_boss_damage", 0) + self.meta.stat_bonus("boss_damage", 0)
            if boss_bonus:
                base = max(1, int(base * (1.0 + boss_bonus)))
        if self.daynight.is_night:
            night_bonus = getattr(self.player, "relic_night_damage", 0)
            if night_bonus:
                base = max(1, int(base * (1.0 + night_bonus)))
        crit_chance = CRIT_CHANCE + self.player.equipment_crit_bonus + self.player.crit_chance_bonus
        crit_mult = CRIT_MULTIPLIER + self.player.crit_damage_bonus
        if random.random() < max(0.02, crit_chance):
            return max(1, int(base * crit_mult)), True
        return base, False

    def draw_hud(self):
        interact_hint = None
        if self.show_hints and not self.dialog.active:
            if self.nearby_chest and not self.nearby_chest.opened:
                interact_hint = "[E] Открыть сундук"
            elif self.nearby_shrine:
                interact_hint = "[E] Святилище"
            elif self.nearby_npc:
                interact_hint = f"[E] {self.nearby_npc.display_name}"

        self.hud.draw(
            self.screen, self.player, self.quests, self.tilemap,
            self.enemies_group, self.npcs_group, self.chests_group,
            shrines_group=self.shrines_group,
            daynight=self.daynight,
            abilities=self.abilities,
            equipment=self.equipment,
            world_events=self.world_events,
            achievements=self.achievements,
            difficulty=self.difficulty,
            interact_hint=interact_hint,
            combo_tracker=self.combo,
            show_minimap=self.show_minimap,
            ui_scale=self.ui_scale,
            relics=self.relics,
            synergies=self.synergies,
            run_mods=self.run_mods,
        )

    def draw_pause(self):
        overlay = pygame.Surface((self.current_w, self.current_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 165))
        self.screen.blit(overlay, (0, 0))
        panel_w, panel_h = 440, 400
        panel = pygame.Rect(self.current_w // 2 - panel_w // 2, self.current_h // 2 - panel_h // 2, panel_w, panel_h)
        draw_rounded_panel(self.screen, panel, (16, 20, 30), (0, 170, 170), radius=14, alpha=235)
        title = self.font_large.render("ПАУЗА", True, (0, 255, 220))
        self.screen.blit(title, title.get_rect(center=(panel.centerx, panel.y + 36)))
        btn_start = panel.y + 68
        if self.run_mods.active_id != "none":
            mod = self.run_mods.active
            mod_txt = self.font_menu_sub.render(
                f"Забег: {mod['name']}", True, mod.get("color", (180, 190, 200))
            )
            self.screen.blit(mod_txt, mod_txt.get_rect(center=(panel.centerx, panel.y + 58)))
            btn_start = panel.y + 82
        options = [
            ("ПРОДОЛЖИТЬ", "Вернуться в игру"),
            ("НАСТРОЙКИ", "Графика и звук"),
            ("ГЛАВНОЕ МЕНЮ", "Сохранить прогресс"),
            ("ВЫХОД", "Закрыть игру"),
        ]
        mouse_pos = pygame.mouse.get_pos()
        self.pause_buttons = {}
        btn_h = 62
        btn_gap = 10
        for i, (label, subtitle) in enumerate(options):
            rect = pygame.Rect(panel.x + 22, btn_start + i * (btn_h + btn_gap), panel.width - 44, btn_h)
            self.pause_buttons[i] = rect
            hovered = rect.collidepoint(mouse_pos) or i == self.pause_selection
            if rect.collidepoint(mouse_pos):
                self.pause_selection = i
            draw_menu_button(
                self.screen, rect, label, self.font_menu, self.font_menu_sub,
                selected=i == self.pause_selection, hovered=hovered,
                subtitle=subtitle,
            )
        if self.show_hints:
            hint = self.font_small.render(
                "Esc — пауза  |  Tab — квесты  |  E — взаимодействие",
                True,
                (130, 140, 155),
            )
            self.screen.blit(hint, hint.get_rect(center=(panel.centerx, panel.bottom - 18)))

    def process_enemy_kill(self, enemy):
        if isinstance(enemy, IceGuardian):
            cloud_tint = (100, 180, 255)
            gold_drop = random.randint(25, 45)
            exp_drop = random.randint(40, 60)
        elif isinstance(enemy, SandColossus):
            cloud_tint = (255, 180, 80)
            gold_drop = random.randint(35, 55)
            exp_drop = random.randint(55, 75)
        elif isinstance(enemy, BlueBoss):
            cloud_tint = (80, 120, 220)
            gold_drop = random.randint(10, 16)
            exp_drop = random.randint(22, 32)
        elif isinstance(enemy, FrostSlime):
            cloud_tint = (120, 200, 255)
            gold_drop = random.randint(4, 8)
            exp_drop = random.randint(15, 22)
        elif isinstance(enemy, RuinWraith):
            cloud_tint = (140, 100, 180)
            gold_drop = random.randint(5, 10)
            exp_drop = random.randint(18, 26)
        elif isinstance(enemy, DesertScorpion):
            cloud_tint = (255, 160, 60)
            gold_drop = random.randint(6, 12)
            exp_drop = random.randint(16, 24)
        elif isinstance(enemy, ForestWolf):
            cloud_tint = (180, 200, 120)
            gold_drop = random.randint(3, 7)
            exp_drop = random.randint(12, 18)
        else:
            cloud_tint = (220, 60, 80)
            gold_drop = random.randint(2, 5)
            exp_drop = random.randint(10, 16)
        if getattr(enemy, "is_elite", False):
            gold_drop = int(gold_drop * 2.0)
            exp_drop = int(exp_drop * 1.8)
            gold_drop = int(gold_drop * (1.0 + getattr(self.player, "relic_elite_gold", 0)))
        self.session_kills += 1
        self.difficulty.on_kill()
        self.achievements.on_kill(self, enemy, self.daynight.is_night)
        combo_bonus = getattr(self.player, "relic_combo_bonus", 0) + self.meta.stat_bonus("combo_bonus", 0)
        self.combo.on_kill(extra_bonus=combo_bonus)
        combo_mult = self.combo.multiplier
        gold_drop = int(gold_drop * combo_mult * self.world_events.gold_bonus)
        gold_drop = int(gold_drop * self.run_mods.active.get("gold_mult", 1.0))
        exp_drop = int(exp_drop * combo_mult)
        self.effects.spawn_death_cloud(enemy.rect.centerx, enemy.rect.centery, cloud_tint)
        if self.player.lifesteal_percent > 0:
            self.player.heal(max(1, int(self.player.attack_damage * self.player.lifesteal_percent)))
        self.player.gold += int(gold_drop * self.player.gold_multiplier)
        self.audio.play_sfx("enemy_death")
        leveled_heal = self.player.add_exp(int(exp_drop * self.world_events.exp_bonus))
        if leveled_heal:
            self.audio.play_sfx("level_up")
            self.effects.trigger_level_up_flash()
            self.pending_skill_picks += 1
            self.try_open_pending_skill_picker()
            self.quests._notify(f"Уровень {self.player.level}! +{leveled_heal} HP")
        if self.player.on_kill_heal > 0:
            self.player.heal(self.player.on_kill_heal)
        if self.player.on_kill_damage > 0:
            self.player.apply_damage(self.player.on_kill_damage)
        self.audio.play_sfx("coin")
        if random.random() < 0.30:
            self.loot_group.add(Potion(enemy.rect.centerx, enemy.rect.centery))
        drop_id = roll_equipment_drop(
            is_elite=getattr(enemy, "is_elite", False),
            is_boss=isinstance(enemy, (BlueBoss, IceGuardian, SandColossus)),
        )
        if drop_id:
            self.equipment_drops_group.add(EquipmentDrop(enemy.rect.centerx, enemy.rect.centery, drop_id))
        relic_bonus = self.meta.stat_bonus("relic_chance", 0)
        relic_id = self.relics.roll_drop(
            is_elite=getattr(enemy, "is_elite", False),
            is_boss=isinstance(enemy, (BlueBoss, IceGuardian, SandColossus)),
            bonus=relic_bonus,
        )
        if relic_id:
            self.relics.add(relic_id, self, enemy.rect.centerx, enemy.rect.centery)
        self.on_enemy_killed(enemy)

    def game_simulation_paused(self):
        return (
            self.dialog.active
            or self.skill_picker.active
            or self.modifier_picker.active
            or self.meta_menu.active
            or self.hud.show_quest_log
            or self.state == "PAUSE"
        )

    def update_playing_world(self):
        if self.game_simulation_paused():
            return
        self._frame = getattr(self, "_frame", 0) + 1
        if self.tilemap:
            self.tilemap.los_tick = self._frame
        prev_hp = self.player.hp
        self.difficulty.update(self.player.level, paused=self.game_simulation_paused())
        if self.difficulty.wave_increased() and not self.game_simulation_paused():
            self.quests._notify(self.difficulty.wave_message())
            self.difficulty.acknowledge_wave()
        self.daynight.update(self.day_speed * getattr(self, "_run_day_speed_mult", 1.0))
        self.abilities.update()
        self.world_events.update(self.daynight)
        self.sync_world_event_notify()
        strike = self.world_events.tick_meteor(self)
        if strike:
            self.apply_meteor_strike(*strike)
        self.world_events.tick_plague(self.player)
        self.achievements.update(self)
        self.update_tutorial_hints()
        if self.get_current_biome() == "ruins":
            self.achievements.visited_ruins = True
        if not self.game_simulation_paused():
            mouse_screen = pygame.mouse.get_pos()
            wx, wy = self.screen_to_world(mouse_screen)
            update_player_aim(self.player, wx, wy, self.enemies_group, self.camera, mouse_screen)
        self.player.update(self.tilemap)
        if self.enemy_push and not self.player.is_dashing:
            separate_player_from_enemies(self.player, self.enemies_group, self.tilemap)
        if pygame.mouse.get_pressed()[0]:
            self.try_player_attack()
        if self.player.consume_attack_hit():
            self.resolve_player_attack()
        enemy_list = self.enemies_group.sprites()
        for enemy in enemy_list:
            if isinstance(enemy, (BlueBoss, IceGuardian, SandColossus)):
                enemy.update(self.player, self.tilemap, self.projectiles_group, enemy_list)
            else:
                enemy.update(self.player, self.tilemap, enemy_list)
        for npc in self.npcs_group:
            npc.update()
        for chest in self.chests_group:
            chest.update()
        for shrine in self.shrines_group:
            shrine.update()
        enemy_count = len(enemy_list)
        if enemy_count > 70 and self._frame % 2 == 0:
            pass
        else:
            sep_iters = 1 if enemy_count > 40 else self.separation_iterations
            resolve_group_separation(
                self.enemies_group, self.tilemap, iterations=sep_iters
            )
        self.projectiles_group.update(self.player, self.tilemap)
        if self.player.hp < prev_hp:
            damage_taken = int(round(prev_hp - self.player.hp))
            if damage_taken > 0:
                self.hud.ping_damage(damage_taken)
            if self.screen_effects_enabled and self.camera_shake:
                shake = min(9, 2 + int(damage_taken * 0.35)) * self.shake_intensity
                duration = min(14, 6 + int(damage_taken * 0.25))
                self.camera.add_shake(int(shake), duration)
        self.effects.update()
        view_rect = self.camera.world_view_rect(self.current_w, self.current_h)
        self.effects.update_weather(self.get_current_biome(), view_rect)
        self.loot_group.update()
        self.equipment_drops_group.update()
        picked_potions = pygame.sprite.spritecollide(self.player, self.loot_group, True)
        for potion in picked_potions:
            self.player.potions_count += 1
            self.audio.play_sfx("potion_pickup")
            self.effects.spawn_potion_pickup(potion.rect.centerx, potion.rect.centery)
        for drop in pygame.sprite.spritecollide(self.player, self.equipment_drops_group, True):
            old = self.equipment.equip(self.player, drop.item_id)
            name = EQUIPMENT[drop.item_id]["name"]
            self.quests._notify(f"Экипировка: {name}")
            self.audio.play_sfx("coin")
        self.damage_texts_group.update()
        self.hud.update()
        self.quests.update()
        self.combo.update()
        self.camera.update(self.player, self.current_w, self.current_h)
        self.audio.update_biome_music(self.get_current_biome())
        self.try_respawn_enemies()
        self.nearby_chest = next((c for c in self.chests_group if not c.opened and c.is_near(self.player.rect)), None)
        self.nearby_shrine = next((s for s in self.shrines_group if s.is_near(self.player.rect)), None)
        self.nearby_npc = next((n for n in self.npcs_group if n.is_near(self.player.rect)), None)
        self.try_open_pending_skill_picker()
        if self.player.hp <= 0:
            if self.relics.try_revive(self.player, self):
                pass
            elif self.state != "GAMEOVER":
                self._finalize_run_death()

    def draw_world_scene(self):
        self.screen.fill((0, 0, 0))
        cam_x = self.camera.camera.x + self.camera.shake_offset[0]
        cam_y = self.camera.camera.y + self.camera.shake_offset[1]
        view_rect = self.camera.world_view_rect(self.current_w, self.current_h)
        self.tilemap.draw_visible_chunks(self.screen, view_rect, cam_x, cam_y)
        for potion in self.loot_group:
            if potion.rect.colliderect(view_rect):
                self.screen.blit(potion.image, self.camera.apply(potion))
        for drop in self.equipment_drops_group:
            if drop.rect.colliderect(view_rect):
                self.screen.blit(drop.image, self.camera.apply(drop))
        for chest in self.chests_group:
            if chest.rect.colliderect(view_rect):
                self.screen.blit(chest.image, self.camera.apply(chest))
        for shrine in self.shrines_group:
            if shrine.rect.colliderect(view_rect):
                self.screen.blit(shrine.image, self.camera.apply(shrine))
        for npc in self.npcs_group:
            if npc.rect.colliderect(view_rect):
                self.screen.blit(npc.image, self.camera.apply(npc))
        for enemy in self.enemies_group:
            if enemy.rect.colliderect(view_rect):
                self.screen.blit(enemy.image, self.camera.apply(enemy))
        for proj in self.projectiles_group:
            if proj.rect.colliderect(view_rect):
                self.screen.blit(proj.image, self.camera.apply(proj))
        aim_targets = None
        if not self.dialog.active and not self.skill_picker.active:
            aim_targets = preview_targets(
                self.player, self.player.aim_angle, self.enemies_group, self.tilemap
            )
            draw_attack_aim(
                self.screen, self.camera, self.player,
                self.enemies_group, self.tilemap, self.player.can_attack(),
                precomputed_targets=aim_targets,
            )
        player_pos = self.camera.apply(self.player)
        if self.player.spawn_protected:
            pulse = 0.55 + 0.45 * math.sin(pygame.time.get_ticks() * 0.02)
            pygame.draw.circle(self.screen, (100, 255, 190), player_pos.center, 24, 2)
            self.screen.blit(self.player.image, player_pos)
            tint = pygame.Surface(player_pos.size, pygame.SRCALPHA)
            tint.fill((120, 255, 200, int(50 + 40 * pulse)))
            self.screen.blit(tint, player_pos)
        else:
            self.screen.blit(self.player.image, player_pos)
        if self.player.is_attacking:
            draw_attack_sword_overlay(self.screen, self.camera, self.player)
        if self.player.swing_flash > 0:
            draw_attack_swing(self.screen, self.camera, self.player, self.player.swing_progress())
        for text in self.damage_texts_group:
            if text.rect.colliderect(view_rect):
                self.screen.blit(text.image, self.camera.apply(text))
        self.effects.draw_particles(self.screen, self.camera)
        if self.abilities.shield_active:
            pos = self.camera.apply(self.player)
            pygame.draw.circle(self.screen, (100, 180, 255), pos.center, 22, 2)
        if not self.skill_picker.active:
            self.draw_hud()
            self.hud.draw_enemy_combat_hints(self.screen, self.camera, self.enemies_group)
            self.hud.draw_enemy_health_bars(
                self.screen, self.camera, self.enemies_group, pygame.mouse.get_pos()
            )
        hp_ratio = max(0.0, self.player.hp / self.player.max_hp)
        if not self.skill_picker.active:
            self.effects.draw_screen_overlays(self.screen, hp_ratio)
        if self.night_overlay:
            self.effects.draw_night_overlay(self.screen, self.daynight.darkness)
        self.effects.draw_event_overlays(self.screen, self.world_events)
        if self.brightness != 1.0:
            w, h = self.screen.get_size()
            if not hasattr(self, "_brightness_surf") or self._brightness_surf.get_size() != (w, h):
                self._brightness_surf = pygame.Surface((w, h), pygame.SRCALPHA)
            alpha = int(abs(1.0 - self.brightness) * 120)
            if self.brightness < 1.0:
                self._brightness_surf.fill((0, 0, 0, alpha))
            else:
                self._brightness_surf.fill((255, 255, 255, alpha))
            self.screen.blit(self._brightness_surf, (0, 0))
        if self.state == "PLAYING" and not self.dialog.active and not self.skill_picker.active:
            draw_crosshair(self.screen, pygame.mouse.get_pos(), bool(aim_targets))
        if self.show_fps:
            fps_surf = self.font_small.render(f"FPS: {int(self.clock.get_fps())}", True, (120, 255, 120))
            self.screen.blit(fps_surf, (self.current_w - fps_surf.get_width() - 14, self.current_h - 24))

    def handle_playing_events(self, event):
        if self.skill_picker.active:
            result = self.skill_picker.handle_event(event)
            if result == "confirm":
                skill_id = self.skill_picker.confirm(self.player)
                if skill_id:
                    self.quests._notify(f"Скилл: {SKILLS[skill_id]['name']}")
                    self.synergies.on_stacks_changed(self.player, self)
                self.try_open_pending_skill_picker()
            return
        if self.dialog.active and self.dialog.handle_event(event):
            return
        if self.hud.show_quest_log:
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_TAB, pygame.K_ESCAPE):
                self.hud.show_quest_log = False
            return
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.pause_selection = 0
                self.set_state("PAUSE")
            elif event.key == pygame.K_TAB:
                self.hud.show_quest_log = True
            elif event.key == pygame.K_LSHIFT or event.key == pygame.K_RSHIFT:
                if self.player.try_dash():
                    self.audio.play_sfx("sword_hit")
            elif event.key in KEY_MAP:
                self.abilities.try_cast(KEY_MAP[event.key], self)
            elif event.key == pygame.K_SPACE or event.key == pygame.K_j:
                self.try_player_attack()
            elif event.key == pygame.K_f or event.key == pygame.K_e:
                if self.nearby_chest and not self.nearby_chest.opened:
                    self.open_chest(self.nearby_chest)
                elif self.nearby_shrine:
                    self.interact_with_shrine(self.nearby_shrine)
                elif self.nearby_npc:
                    self.interact_with_npc(self.nearby_npc)
                elif event.key == pygame.K_e and self.player.potions_count > 0 and self.player.hp < self.player.max_hp:
                    self.player.potions_count -= 1
                    heal_amount = int((40 + self.player.potion_heal_bonus) * self.player.potion_heal_mult)
                    self.player.heal(heal_amount)
                    self.audio.play_sfx("potion_drink")
                    self.effects.spawn_heal_burst(self.player.rect.centerx, self.player.rect.centery)
                    self.quests._notify(f"Зелье: +{heal_amount} HP")
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.try_player_attack()

    def handle_pause_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.pause_selection = (self.pause_selection - 1) % 4
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.pause_selection = (self.pause_selection + 1) % 4
            elif event.key == pygame.K_ESCAPE:
                self.set_state("PLAYING")
            elif event.key == pygame.K_RETURN:
                self.execute_pause_action(self.pause_selection)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, rect in getattr(self, "pause_buttons", {}).items():
                if rect.collidepoint(event.pos):
                    self.execute_pause_action(i)

    def execute_pause_action(self, selection):
        if selection == 0:
            self.set_state("PLAYING")
        elif selection == 1:
            self._settings_return = "PAUSE"
            self.set_state("SETTINGS")
        elif selection == 2:
            self.save_game()
            self.set_state("MENU")
        elif selection == 3:
            self.save_game()
            self.audio.stop_music()
            pygame.quit()
            sys.exit()

    def draw_game_over(self):
        bottom = draw_run_summary(
            self.screen, self,
            (self.font_large, self.font_medium, self.font_small),
            self.run_souls_earned,
        )
        mouse_pos = pygame.mouse.get_pos()
        btn_y = min(bottom + 24, self.current_h - 120)
        btn_rect = pygame.Rect(self.current_w // 2 - 130, btn_y, 260, 45)
        meta_rect = pygame.Rect(self.current_w // 2 - 130, btn_y + 55, 260, 45)
        self.game_over_button = btn_rect
        self.game_over_meta_button = meta_rect
        for rect, label, hover_fill, hover_border in (
            (btn_rect, "НОВЫЙ ЗАБЕГ", (60, 20, 20), (255, 50, 50)),
            (meta_rect, "ДРЕВО ДУШ", (30, 20, 50), (180, 140, 255)),
        ):
            is_hovered = rect.collidepoint(mouse_pos)
            btn_color = hover_fill if is_hovered else tuple(c // 2 for c in hover_fill)
            border_color = hover_border if is_hovered else tuple(c // 2 for c in hover_border)
            text_color = (255, 255, 255) if is_hovered else (200, 200, 200)
            pygame.draw.rect(self.screen, btn_color, rect, border_radius=6)
            pygame.draw.rect(self.screen, border_color, rect, 2, border_radius=6)
            btn_text = self.font_medium.render(label, True, text_color)
            self.screen.blit(btn_text, btn_text.get_rect(center=rect.center))

    def restart_after_death(self):
        """Roguelike: полный сброс забега после смерти."""
        self.begin_new_run_flow()

    def adjust_menu_selection(self, delta):
        max_items = 6 if self.game_initialized else 5
        self.menu_selection = (self.menu_selection + delta) % max_items
        if not self.game_initialized and self.menu_selection == 2:
            self.menu_selection = (self.menu_selection + delta) % max_items

    def start_finale(self):
        self.finale.start()
        self.set_state("FINALE")

    def finish_finale(self):
        self.story_finale_seen = True
        self.save_game()
        self.enter_playing(
            180,
            "Рубеж покорён — свободный режим",
        )
        self.quests._notify("★ Сюжет завершён. Мир открыт для исследования.")

    def start_with_intro(self):
        self.intro.start()
        self.set_state("INTRO")

    def execute_menu_action(self, selection):
        if self.game_initialized:
            if selection == 0:
                self.enter_playing(
                    SPAWN_IFRAMES_CONTINUE,
                    f"Неуязвимость {SPAWN_IFRAMES_CONTINUE // 60} сек",
                )
            elif selection == 1:
                self.begin_new_run_flow()
            elif selection == 2:
                self.meta_menu.open()
            elif selection == 3:
                self.set_state("SHOP")
            elif selection == 4:
                self._settings_return = "MENU"
                self.set_state("SETTINGS")
            elif selection == 5:
                self.save_game()
                self.audio.stop_music()
                pygame.quit()
                sys.exit()
        else:
            if selection == 0:
                self.begin_new_run_flow()
            elif selection == 1:
                self.meta_menu.open()
            elif selection == 3:
                self._settings_return = "MENU"
                self.set_state("SETTINGS")
            elif selection == 4:
                self.save_game()
                self.audio.stop_music()
                pygame.quit()
                sys.exit()
                
    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.save_game()
                    self.audio.stop_music()
                    running = False
                if self.state == "MENU":
                    if self.modifier_picker.active:
                        result = self.modifier_picker.handle_event(event, self.run_mods)
                        if result and result not in (True, "cancel"):
                            self.confirm_run_modifiers()
                    elif self.meta_menu.active:
                        result = self.meta_menu.handle_event(event, self.meta)
                        if result == "bought":
                            self.save_game()
                    elif event.type == pygame.KEYDOWN:
                        if event.key in [pygame.K_UP, pygame.K_w]:
                            self.adjust_menu_selection(-1)
                        elif event.key in [pygame.K_DOWN, pygame.K_s]:
                            self.adjust_menu_selection(1)
                        elif event.key == pygame.K_RETURN:
                            self.execute_menu_action(self.menu_selection)
                    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        for i, rect in self.menu_buttons.items():
                            if rect.collidepoint(event.pos):
                                self.execute_menu_action(i)
                elif self.state == "SETTINGS":
                    self.handle_settings_events(event)
                elif self.state == "SHOP":
                    self.handle_shop_events(event)
                elif self.state == "GAMEOVER":
                    if self.modifier_picker.active:
                        result = self.modifier_picker.handle_event(event, self.run_mods)
                        if result and result not in (True, "cancel"):
                            self.set_state("MENU")
                            self.confirm_run_modifiers()
                    elif self.meta_menu.active:
                        result = self.meta_menu.handle_event(event, self.meta)
                        if result == "bought":
                            self.save_game()
                    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        if hasattr(self, "game_over_button") and self.game_over_button.collidepoint(event.pos):
                            self.restart_after_death()
                        elif hasattr(self, "game_over_meta_button") and self.game_over_meta_button.collidepoint(event.pos):
                            self.meta_menu.open()
                    elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        self.set_state("MENU")
                elif self.state == "PLAYING":
                    self.handle_playing_events(event)
                elif self.state == "PAUSE":
                    self.handle_pause_events(event)
                elif self.state == "INTRO":
                    result = self.intro.handle_event(event)
                    if result == "done":
                        self.enter_playing(
                            SPAWN_IFRAMES_NEW,
                            f"Неуязвимость {SPAWN_IFRAMES_NEW // 60} сек — удачи!",
                        )
                elif self.state == "FINALE":
                    result = self.finale.handle_event(event)
                    if result == "done":
                        self.finish_finale()
                                    
            self.sync_screen_size()

            if self.state == "MENU":
                self.menu_bg.update()
                self.draw_menu()
                if self.modifier_picker.active:
                    self.modifier_picker.draw(self.screen, self.current_w, self.current_h)
                if self.meta_menu.active:
                    self.meta_menu.draw(self.screen, self.current_w, self.current_h, self.meta)
            elif self.state == "INTRO":
                self.intro.update()
                self.intro.draw(self.screen, self.current_w, self.current_h)
            elif self.state == "FINALE":
                self.finale.update()
                self.finale.draw(self.screen, self.current_w, self.current_h)
            elif self.state == "SETTINGS":
                self.draw_settings()
            elif self.state == "SHOP":
                self.draw_shop()
            elif self.state == "GAMEOVER":
                self.draw_game_over()
                if self.meta_menu.active:
                    self.meta_menu.draw(self.screen, self.current_w, self.current_h, self.meta)
                if self.modifier_picker.active:
                    self.modifier_picker.draw(self.screen, self.current_w, self.current_h)
            elif self.state in ("PLAYING", "PAUSE"):
                self.update_playing_world()
                self.draw_world_scene()
                if self.state == "PAUSE":
                    self.draw_pause()
                if self.dialog.active:
                    self.dialog.draw(self.screen, self.current_w, self.current_h)
                if self.skill_picker.active:
                    self.skill_picker.draw(self.screen, self.current_w, self.current_h, self.player)
                
            pygame.display.flip()
            if self.fps_limit > 0:
                self.clock.tick(self.fps_limit)
            else:
                self.clock.tick()
        self.audio.stop_music()
        pygame.quit()
        sys.exit()
        
if __name__ == "__main__":
    game = Game()
    game.run()