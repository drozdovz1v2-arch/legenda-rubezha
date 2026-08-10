"""Нарастающая сложность — хардкорный roguelike-скейлинг."""





class DifficultyManager:

    MAX_WAVE = 22

    HARDCORE_BASE = 1.12



    def __init__(self):

        self.play_time_frames = 0

        self.total_kills = 0

        self.wave = 1

        self._last_announced_wave = 1

        self.run_enemy_mult = 1.0

        self.run_speed_mult = 1.0

        self.run_contact_cooldown_mult = 1.0

        self.event_damage_mult = 1.0



    def reset(self):

        self.play_time_frames = 0

        self.total_kills = 0

        self.wave = 1

        self._last_announced_wave = 1

        self.run_enemy_mult = 1.0

        self.run_speed_mult = 1.0

        self.run_contact_cooldown_mult = 1.0

        self.event_damage_mult = 1.0



    def update(self, player_level, paused=False):

        if not paused:

            self.play_time_frames += 1

        self.wave = self._calc_wave(player_level)



    def on_kill(self):

        self.total_kills += 1



    def _calc_wave(self, player_level):

        minutes = self.play_time_frames / 3600.0

        time_bonus = int(minutes / 3.5)

        kill_bonus = self.total_kills // 16

        return min(self.MAX_WAVE, max(1, player_level + time_bonus + kill_bonus))



    @property

    def tier(self):

        return max(0, self.wave - 1)



    @property

    def threat_label(self):

        if self.wave <= 2:

            return "I — Кровавый старт"

        if self.wave <= 5:

            return "II — Охота"

        if self.wave <= 9:

            return "III — Мясорубка"

        if self.wave <= 14:

            return "IV — Ад"

        if self.wave <= 18:

            return "V — Безумие"

        return "VI — Невозможно"



    def stat_multiplier(self, player_level=1):

        wave_part = 1.0 + self.tier * 0.055

        level_part = 1.0 + max(0, player_level - 1) * 0.045

        return wave_part * level_part * self.HARDCORE_BASE * self.run_enemy_mult



    def boss_multiplier(self, player_level=1):

        wave_part = 1.0 + self.tier * 0.042

        level_part = 1.0 + max(0, player_level - 1) * 0.035

        return wave_part * level_part * self.HARDCORE_BASE * self.run_enemy_mult



    def cap_multiplier(self):

        return 1.0 + self.tier * 0.042



    def respawn_multiplier(self):

        return 1.0 + self.tier * 0.038



    def elite_chance_bonus(self):

        return min(0.20, self.tier * 0.010 + max(0, self.tier - 2) * 0.005)



    def scaled_limits(self, base_limits):

        mult = self.cap_multiplier()

        return {key: max(1, int(value * mult)) for key, value in base_limits.items()}



    def scale_enemy(self, enemy, is_boss=False, player_level=1, aggro_mult=1.0, zone_mult=1.0):

        if getattr(enemy, "difficulty_scaled", False):

            return

        mult = self.boss_multiplier(player_level) if is_boss else self.stat_multiplier(player_level)
        mult *= max(1.0, float(zone_mult))

        if hasattr(enemy, "max_hp"):

            enemy.max_hp = max(1, int(enemy.max_hp * mult))

            enemy.hp = enemy.max_hp

        if hasattr(enemy, "speed"):

            speed_mult = 1.0 + (mult - 1.0) * 0.48

            speed_mult *= max(1.0, self.run_speed_mult)

            enemy.speed *= speed_mult

        if hasattr(enemy, "contact_damage"):

            dmg_mult = 1.0 + (mult - 1.0) * 0.62

            dmg_mult *= max(1.0, self.event_damage_mult)

            enemy.contact_damage = max(1, int(enemy.contact_damage * dmg_mult))

        if hasattr(enemy, "contact_cooldown"):

            cd_mult = max(1.0, float(getattr(self, "run_contact_cooldown_mult", 1.0)))

            enemy.contact_cooldown = max(

                16, int(enemy.contact_cooldown * (1.0 - min(0.20, (mult - 1.0) * 0.10)) * cd_mult)

            )

        if hasattr(enemy, "notice_radius"):

            aggro = max(1.0, float(aggro_mult))

            enemy.notice_radius = int(

                enemy.notice_radius * (1.0 + (mult - 1.0) * 0.20) * aggro

            )

        if hasattr(enemy, "lunge_power"):

            enemy.lunge_power *= 1.0 + (mult - 1.0) * 0.25

        if hasattr(enemy, "lunge_cooldown") and enemy.lunge_cooldown > 0:

            enemy.lunge_cooldown = max(20, int(enemy.lunge_cooldown * 0.93))

        enemy.difficulty_scaled = True



    def wave_increased(self):

        return self.wave > self._last_announced_wave



    def acknowledge_wave(self):

        self._last_announced_wave = self.wave



    def wave_message(self):

        return f"Угроза {self.wave}: {self.threat_label}"



    def to_dict(self):

        return {

            "play_time_frames": self.play_time_frames,

            "total_kills": self.total_kills,

            "wave": self.wave,

        }



    def load_dict(self, data):

        if not data:

            return

        self.play_time_frames = int(data.get("play_time_frames", 0))

        self.total_kills = int(data.get("total_kills", 0))

        self.wave = int(data.get("wave", 1))

        self._last_announced_wave = self.wave

