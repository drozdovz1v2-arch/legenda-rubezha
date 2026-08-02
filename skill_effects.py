"""Применение эффектов скиллов к игроку (data-driven)."""

from config import PLAYER_START_HP


def reset_skill_bonuses(player):
    """Сбросить только бонусы/проклятия от скиллов (не оружие и экипировку)."""
    player.skill_attack_bonus = 0
    player.max_hp_skill_bonus = 0
    player.speed_multiplier = 1.0
    player.on_kill_heal = 0
    player.on_kill_damage = 0
    player.lifesteal_percent = 0.0
    player.life_drain_percent = 0.0
    player.thorn_damage = 0
    player.thorn_self_damage = 0
    player.gold_multiplier = 1.0
    player.exp_multiplier = 1.0
    player.potion_heal_bonus = 0
    player.potion_heal_mult = 1.0
    player.attack_cooldown_bonus = 0
    player.attack_cooldown_penalty = 0
    player.dash_cooldown_bonus = 0
    player.dash_cooldown_penalty = 0
    player.damage_reduction = 0.0
    player.damage_taken_mult = 1.0
    player.crit_chance_bonus = 0.0
    player.crit_damage_bonus = 0.0
    player.attack_range_bonus = 0
    player.dash_speed_bonus = 0
    player.dash_iframes_penalty = 0
    player.hp_regen_per_sec = 0.0
    player.self_damage_on_attack = 0
    player.enemy_aggro_mult = 1.0
    player.hp_regen_accum = 0.0
    player.recalc_attack_damage()
    player.attack_range = max(24, player.base_attack_range + player.attack_range_bonus)
    player.dash_speed = max(6, player.base_dash_speed + player.dash_speed_bonus)
    player.dash_iframes = max(2, player.base_dash_iframes - player.dash_iframes_penalty)
    player.recalc_max_hp()


def _clamp(value, low, high):
    return max(low, min(high, value))


def apply_stat_delta(player, stat, value):
    """Применить одно изменение стата (один стак)."""
    if stat == "skill_attack_bonus":
        player.skill_attack_bonus += int(value)
        player.recalc_attack_damage()
    elif stat == "max_hp":
        player.max_hp_skill_bonus += int(value)
        player.recalc_max_hp()
        if value > 0:
            player.hp = min(player.max_hp, player.hp + int(value))
    elif stat == "speed_mult":
        player.speed_multiplier = _clamp(player.speed_multiplier + float(value), 0.35, 2.2)
    elif stat == "on_kill_heal":
        player.on_kill_heal += int(value)
    elif stat == "on_kill_damage":
        player.on_kill_damage += int(value)
    elif stat == "lifesteal":
        player.lifesteal_percent = _clamp(player.lifesteal_percent + float(value), 0.0, 0.45)
    elif stat == "life_drain":
        player.life_drain_percent = _clamp(player.life_drain_percent + float(value), 0.0, 0.35)
    elif stat == "thorns":
        player.thorn_damage += int(value)
    elif stat == "thorn_self":
        player.thorn_self_damage += int(value)
    elif stat == "gold_mult":
        player.gold_multiplier = _clamp(player.gold_multiplier + float(value), 0.25, 4.0)
    elif stat == "exp_mult":
        player.exp_multiplier = _clamp(player.exp_multiplier + float(value), 0.35, 3.5)
    elif stat == "potion_bonus":
        player.potion_heal_bonus += int(value)
    elif stat == "potion_mult":
        player.potion_heal_mult = _clamp(player.potion_heal_mult + float(value), 0.2, 2.5)
    elif stat == "attack_cd_bonus":
        player.attack_cooldown_bonus = _clamp(player.attack_cooldown_bonus + int(value), 0, 28)
    elif stat == "attack_cd_penalty":
        player.attack_cooldown_penalty = _clamp(player.attack_cooldown_penalty + int(value), 0, 28)
    elif stat == "dash_cd_bonus":
        player.dash_cooldown_bonus = _clamp(player.dash_cooldown_bonus + int(value), 0, 36)
    elif stat == "dash_cd_penalty":
        player.dash_cooldown_penalty = _clamp(player.dash_cooldown_penalty + int(value), 0, 36)
    elif stat == "damage_reduction":
        player.damage_reduction = _clamp(player.damage_reduction + float(value), 0.0, 0.55)
    elif stat == "damage_taken":
        player.damage_taken_mult = _clamp(player.damage_taken_mult + float(value), 1.0, 2.8)
    elif stat == "crit_chance":
        player.crit_chance_bonus = _clamp(player.crit_chance_bonus + float(value), -0.12, 0.35)
    elif stat == "crit_damage":
        player.crit_damage_bonus = _clamp(player.crit_damage_bonus + float(value), -0.5, 1.5)
    elif stat == "attack_range":
        player.attack_range_bonus += int(value)
        player.attack_range = max(24, player.base_attack_range + player.attack_range_bonus)
    elif stat == "dash_speed":
        player.dash_speed_bonus += int(value)
        player.dash_speed = max(6, player.base_dash_speed + player.dash_speed_bonus)
    elif stat == "dash_iframes_penalty":
        player.dash_iframes_penalty += int(value)
        player.dash_iframes = max(2, player.base_dash_iframes - player.dash_iframes_penalty)
    elif stat == "hp_regen":
        player.hp_regen_per_sec += float(value)
    elif stat == "self_damage_on_attack":
        player.self_damage_on_attack += int(value)
    elif stat == "enemy_aggro":
        player.enemy_aggro_mult = _clamp(player.enemy_aggro_mult + float(value), 1.0, 2.5)


def apply_skill_stack(player, skill):
    for stat, value in skill.get("effects", []):
        apply_stat_delta(player, stat, value)


def reapply_all_skill_stacks(player):
    stacks = dict(player.skill_stacks)
    reset_skill_bonuses(player)
    player.skill_stacks = {}
    for skill_id, count in stacks.items():
        from skill_catalog import SKILLS

        skill = SKILLS.get(skill_id)
        if not skill:
            continue
        for _ in range(int(count)):
            max_stacks = skill.get("max_stacks", 1)
            if player.skill_stacks.get(skill_id, 0) >= max_stacks:
                break
            player.skill_stacks[skill_id] = player.skill_stacks.get(skill_id, 0) + 1
            apply_skill_stack(player, skill)
