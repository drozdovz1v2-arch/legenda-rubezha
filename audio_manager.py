import os
import sys

import pygame

from audio_synth import (
    build_coin_sound,
    build_enemy_death_sound,
    build_level_up_sound,
    build_potion_drink_sound,
    build_potion_pickup_sound,
    build_relic_pickup_sound,
    build_sword_hit_sound,
    build_sword_swing_sound,
)

_ROOT = sys._MEIPASS if getattr(sys, "frozen", False) else os.path.dirname(os.path.abspath(__file__))
AUDIO_DIR = os.path.join(_ROOT, "assets", "audio")

# CC0: Kenney (kenney.nl) — SFX; OpenGameArt — music loops (см. assets/audio/ATTRIBUTION.txt)

BIOME_TRACKS = {
    "forest": "forest",
    "desert": "desert",
    "snow": "snow",
    "ruins": "forest",
}


class AudioManager:
    SFX_CHANNELS = 32

    def __init__(self, vol_master=0.8, vol_music=0.5, vol_sfx=0.7):
        self.vol_master = vol_master
        self.vol_music = vol_music
        self.vol_sfx = vol_sfx
        self.enabled = False
        self.current_music = None
        self.current_biome = None
        self.sounds = {}
        self._music_check_timer = 0

        self._music_files = {
            "menu": os.path.join(AUDIO_DIR, "music", "menu.ogg"),
            "forest": os.path.join(AUDIO_DIR, "music", "forest.ogg"),
            "desert": os.path.join(AUDIO_DIR, "music", "desert.mp3"),
            "snow": os.path.join(AUDIO_DIR, "music", "forest.ogg"),
        }

        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            pygame.mixer.set_num_channels(self.SFX_CHANNELS)
            self.enabled = True
        except pygame.error as exc:
            print(f"Аудио недоступно: {exc}")
            return

        self._load_sounds()
        self.apply_volumes()

    def _load_sound(self, name, filename, synth_builder=None):
        path = os.path.join(AUDIO_DIR, "sfx", filename)
        if os.path.exists(path):
            try:
                self.sounds[name] = pygame.mixer.Sound(path)
                return
            except pygame.error as exc:
                print(f"Не удалось загрузить {filename}: {exc}")
        if synth_builder is not None:
            try:
                self.sounds[name] = pygame.mixer.Sound(buffer=synth_builder())
            except pygame.error as exc:
                print(f"Не удалось синтезировать звук '{name}': {exc}")
            return
        print(f"Звуковой файл не найден: {path}")

    def _load_sounds(self):
        self._load_sound("sword_swing", "sword_swing.ogg", build_sword_swing_sound)
        self._load_sound("sword_hit", "sword_hit.ogg", build_sword_hit_sound)
        self._load_sound("enemy_death", "enemy_death.ogg", build_enemy_death_sound)
        self._load_sound("coin", "coin.ogg", build_coin_sound)
        self._load_sound("potion_pickup", "potion_pickup.ogg", build_potion_pickup_sound)
        self._load_sound("potion_drink", "potion_drink.ogg", build_potion_drink_sound)
        self._load_sound("potion", "potion.ogg", build_potion_pickup_sound)
        self._load_sound("level_up", "level_up.ogg", build_level_up_sound)
        self._load_sound("relic_pickup", "relic_pickup.ogg", build_relic_pickup_sound)

    @property
    def music_volume(self):
        return max(0.0, min(1.0, self.vol_master * self.vol_music))

    @property
    def sfx_volume(self):
        return max(0.0, min(1.0, self.vol_master * self.vol_sfx))

    def apply_volumes(self):
        if not self.enabled:
            return
        pygame.mixer.music.set_volume(self.music_volume)
        for sound in self.sounds.values():
            sound.set_volume(self.sfx_volume)

    def set_volumes(self, master, music, sfx):
        self.vol_master = master
        self.vol_music = music
        self.vol_sfx = sfx
        self.apply_volumes()

    def _resolve_track(self, track):
        path = self._music_files.get(track)
        if path and os.path.exists(path):
            return track, path
        fallback = self._music_files.get("forest")
        if fallback and os.path.exists(fallback):
            return "forest", fallback
        return None, None

    def _music_is_playing(self):
        if not self.enabled:
            return False
        try:
            return pygame.mixer.music.get_busy()
        except pygame.error:
            return False

    def play_music(self, track, force=False):
        if not self.enabled or self.music_volume <= 0:
            return

        track_name, path = self._resolve_track(track)
        if not path:
            return

        if not force and track_name == self.current_music and self._music_is_playing():
            return

        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.play(-1)
            self.current_music = track_name
            self.apply_volumes()
        except pygame.error as exc:
            print(f"Не удалось воспроизвести музыку '{track}': {exc}")

    def stop_music(self):
        if self.enabled:
            pygame.mixer.music.stop()
        self.current_music = None
        self.current_biome = None

    def play_sfx(self, name):
        if not self.enabled or self.sfx_volume <= 0:
            return
        sound = self.sounds.get(name)
        if not sound:
            return
        channel = pygame.mixer.find_channel(True)
        if channel:
            channel.play(sound)
        else:
            sound.play()

    def sync_state_music(self, state):
        if state in ("PLAYING", "PAUSE"):
            return
        if state == "SETTINGS" and self.current_biome is not None:
            return
        if state in ("MENU", "SETTINGS", "SHOP", "GAMEOVER", "INTRO", "FINALE"):
            self.current_biome = None
            self.play_music("menu")

    def update_biome_music(self, biome):
        if not self.enabled or self.music_volume <= 0:
            return

        track = BIOME_TRACKS.get(biome, "forest")
        if biome == self.current_biome:
            if self._music_is_playing():
                return
            self.play_music(track, force=True)
            return

        self.current_biome = biome
        self.play_music(track, force=True)

    def reset_biome(self):
        self.current_biome = None

    def tick(self, state, biome=None):
        if not self.enabled or self.music_volume <= 0:
            return

        self._music_check_timer += 1
        if self._music_check_timer < 120:
            return
        self._music_check_timer = 0

        if self._music_is_playing():
            return

        if state in ("PLAYING", "PAUSE") and biome:
            self.current_biome = None
            self.update_biome_music(biome)
        elif state in ("MENU", "SETTINGS", "SHOP", "GAMEOVER", "INTRO", "FINALE"):
            self.play_music("menu", force=True)

    def on_display_changed(self, state, biome=None):
        if not self.enabled:
            return
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            pygame.mixer.set_num_channels(self.SFX_CHANNELS)
        except pygame.error as exc:
            print(f"Не удалось восстановить аудио: {exc}")
            self.enabled = False
            return

        self.current_music = None
        self.apply_volumes()
        if state in ("PLAYING", "PAUSE") and biome:
            self.current_biome = None
            self.update_biome_music(biome)
        else:
            self.sync_state_music(state)
