import os
import sys

import pygame



from audio_synth import (

    build_potion_drink_sound,

    build_potion_pickup_sound,

    build_relic_pickup_sound,

    build_sword_hit_sound,

    build_sword_swing_sound,

)



_ROOT = sys._MEIPASS if getattr(sys, "frozen", False) else os.path.dirname(os.path.abspath(__file__))
AUDIO_DIR = os.path.join(_ROOT, "assets", "audio")



# CC0: Kenney (kenney.nl) — SFX; OpenGameArt — music loops (см. assets/audio/ATTRIBUTION.txt)





class AudioManager:

    def __init__(self, vol_master=0.8, vol_music=0.5, vol_sfx=0.7):

        self.vol_master = vol_master

        self.vol_music = vol_music

        self.vol_sfx = vol_sfx

        self.enabled = False

        self.current_music = None

        self.current_biome = None

        self.sounds = {}



        self._music_files = {

            "menu": os.path.join(AUDIO_DIR, "music", "menu.ogg"),

            "forest": os.path.join(AUDIO_DIR, "music", "forest.ogg"),

            "desert": os.path.join(AUDIO_DIR, "music", "desert.mp3"),

            "snow": os.path.join(AUDIO_DIR, "music", "forest.ogg"),

        }



        try:

            if not pygame.mixer.get_init():

                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

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

        self._load_sound("enemy_death", "enemy_death.ogg")

        self._load_sound("coin", "coin.ogg")

        self._load_sound("potion_pickup", "potion_pickup.ogg", build_potion_pickup_sound)

        self._load_sound("potion_drink", "potion_drink.ogg", build_potion_drink_sound)

        self._load_sound("potion", "potion.ogg", build_potion_pickup_sound)

        self._load_sound("level_up", "level_up.ogg")

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



    def play_music(self, track, force=False):

        if not self.enabled:

            return

        if not force and track == self.current_music:

            return



        path = self._music_files.get(track)

        if not path or not os.path.exists(path):

            return



        try:

            pygame.mixer.music.load(path)

            pygame.mixer.music.play(-1)

            self.current_music = track

            self.apply_volumes()

        except pygame.error as exc:

            print(f"Не удалось воспроизвести музыку '{track}': {exc}")



    def stop_music(self):

        if self.enabled:

            pygame.mixer.music.stop()

        self.current_music = None

        self.current_biome = None



    def play_sfx(self, name):

        if not self.enabled:

            return

        sound = self.sounds.get(name)

        if sound:

            sound.play()



    def sync_state_music(self, state):

        if state in ("MENU", "SETTINGS", "SHOP", "GAMEOVER", "INTRO", "FINALE"):

            self.current_biome = None

            self.play_music("menu")



    def update_biome_music(self, biome):

        if not self.enabled:

            return

        if biome == self.current_biome:

            return

        self.current_biome = biome

        self.play_music(biome, force=True)



    def reset_biome(self):

        self.current_biome = None


