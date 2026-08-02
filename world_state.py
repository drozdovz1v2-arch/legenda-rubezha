"""Сериализация состояния мира: враги, лут, сундуки, святилища, квесты."""

from enemy import (
    Enemy, BlueBoss, FrostSlime, IceGuardian,
    ForestWolf, DesertScorpion, RuinWraith, SandColossus,
)
from loot import Potion
from chests import chest_to_dict, chest_from_dict
from shrines import shrine_to_dict, shrine_from_dict

ENEMY_TYPES = {
    "slime": Enemy,
    "boss": BlueBoss,
    "frost": FrostSlime,
    "ice_lord": IceGuardian,
    "wolf": ForestWolf,
    "scorpion": DesertScorpion,
    "wraith": RuinWraith,
    "colossus": SandColossus,
}


def enemy_to_dict(enemy):
    if isinstance(enemy, IceGuardian):
        kind = "ice_lord"
    elif isinstance(enemy, SandColossus):
        kind = "colossus"
    elif isinstance(enemy, BlueBoss):
        kind = "boss"
    elif isinstance(enemy, FrostSlime):
        kind = "frost"
    elif isinstance(enemy, ForestWolf):
        kind = "wolf"
    elif isinstance(enemy, DesertScorpion):
        kind = "scorpion"
    elif isinstance(enemy, RuinWraith):
        kind = "wraith"
    else:
        kind = "slime"
    data = {
        "type": kind,
        "x": enemy.rect.x,
        "y": enemy.rect.y,
        "hp": enemy.hp,
    }
    if getattr(enemy, "is_elite", False):
        data["elite"] = True
    return data


def enemy_from_dict(data):
    cls = ENEMY_TYPES.get(data.get("type", "slime"), Enemy)
    enemy = cls(data["x"], data["y"])
    if data.get("elite") and hasattr(enemy, "make_elite"):
        enemy.make_elite()
    enemy.hp = data.get("hp", enemy.hp)
    return enemy


def loot_to_dict(item):
    return {"x": item.rect.centerx, "y": item.rect.centery}


def loot_from_dict(data):
    return Potion(data["x"], data["y"])


def serialize_world(
    tilemap,
    enemies_group,
    loot_group,
    quests,
    npcs_group,
    chests_group,
    shrines_group=None,
    flags=None,
):
    return {
        "map_seed": tilemap.seed,
        "enemies": [enemy_to_dict(e) for e in enemies_group],
        "loot": [loot_to_dict(p) for p in loot_group],
        "chests": [chest_to_dict(c) for c in chests_group],
        "shrines": [shrine_to_dict(s) for s in shrines_group] if shrines_group else [],
        "quests": quests.to_dict(),
        "npcs": [{"id": n.npc_id, "x": n.rect.centerx, "y": n.rect.centery} for n in npcs_group],
        "flags": flags or {},
    }


def restore_world_state(game, world_data):
    if not world_data:
        return False

    seed = world_data.get("map_seed")
    if seed is not None and getattr(game.tilemap, "seed", None) != seed:
        from tilemap import TileMap
        game.tilemap = TileMap(seed=seed)

    game.enemies_group.empty()
    for ed in world_data.get("enemies", []):
        game.enemies_group.add(enemy_from_dict(ed))

    game.loot_group.empty()
    for ld in world_data.get("loot", []):
        game.loot_group.add(loot_from_dict(ld))

    game.chests_group.empty()
    chest_data = world_data.get("chests")
    if chest_data:
        for cd in chest_data:
            game.chests_group.add(chest_from_dict(cd))

    game.shrines_group.empty()
    shrine_data = world_data.get("shrines")
    if shrine_data:
        for sd in shrine_data:
            game.shrines_group.add(shrine_from_dict(sd))

    flags = world_data.get("flags", {})
    game.ice_guardian_defeated = flags.get("ice_guardian_defeated", False)
    game.sand_colossus_defeated = flags.get("sand_colossus_defeated", False)

    if world_data.get("quests"):
        game.quests.load_dict(world_data["quests"])
        if game.quests.player_title:
            game.player.title = game.quests.player_title
        if "first_steps" in game.quests.completed:
            game.player.dash_unlocked = True

    return True
