"""Оружейная лавка — каталог, требования и интерфейс."""
import pygame

from config import PLAYER_START_DAMAGE
from equipment import EQUIPMENT, format_armor_stats, get_equipped_armor_name
from quests import QUESTS
from ui_theme import draw_rounded_panel

STARTER_WEAPON = {
    "id": "iron_sword",
    "name": "Железный меч",
    "price": 0,
    "damage": PLAYER_START_DAMAGE,
    "range": 40,
    "tier": 0,
    "desc": "Стартовый клинок караванщика.",
}

SHOP_WEAPONS = [
    {
        "id": "steel_saber",
        "name": "Стальной палаш",
        "price": 55,
        "damage": 28,
        "range": 48,
        "tier": 1,
        "desc": "Надёжный клинок для первых вылазок.",
        "req_wave": 2,
        "req_level": 2,
    },
    {
        "id": "hunter_blade",
        "name": "Клинок охотника",
        "price": 100,
        "damage": 36,
        "range": 52,
        "tier": 2,
        "desc": "Заточен под волков и элитных слаймов.",
        "req_wave": 3,
        "req_level": 4,
        "req_zone": 1,
    },
    {
        "id": "frost_blade",
        "name": "Морозный клинок",
        "price": 165,
        "damage": 48,
        "range": 58,
        "tier": 3,
        "desc": "Ледяная сталь с северных склонов.",
        "req_wave": 5,
        "req_level": 6,
        "req_zone": 2,
        "req_quests": ["desert_hunt"],
    },
    {
        "id": "caravan_cleaver",
        "name": "Секира каравана",
        "price": 245,
        "damage": 62,
        "range": 64,
        "tier": 3,
        "desc": "Тяжёлый удар по пустынным стражам.",
        "req_wave": 7,
        "req_level": 8,
        "req_zone": 3,
    },
    {
        "id": "wraith_blade",
        "name": "Клинок призраков",
        "price": 350,
        "damage": 78,
        "range": 70,
        "tier": 4,
        "desc": "Выкован из обломков древних руин.",
        "req_wave": 9,
        "req_level": 10,
        "req_zone": 3,
        "req_quests": ["ruins_awakening"],
    },
    {
        "id": "light_brand",
        "name": "Светозарный клинок",
        "price": 480,
        "damage": 96,
        "range": 78,
        "tier": 5,
        "desc": "Сияет в самых кровавых боях.",
        "req_wave": 12,
        "req_level": 12,
        "req_zone": 4,
    },
    {
        "id": "ice_reaver",
        "name": "Рассекатель льда",
        "price": 620,
        "damage": 112,
        "range": 82,
        "tier": 5,
        "desc": "Клинок победителя Ледяного стража.",
        "req_wave": 14,
        "req_level": 14,
        "req_zone": 4,
        "req_ice_guardian": True,
    },
    {
        "id": "border_glaive",
        "name": "Глефа рубежа",
        "price": 850,
        "damage": 135,
        "range": 92,
        "tier": 6,
        "desc": "Легендарное оружие покорителя пустыни.",
        "req_wave": 17,
        "req_level": 16,
        "req_zone": 5,
        "req_colossus": True,
    },
]

SHOP_ARMOR = [
    {
        "id": "shop_padded_vest",
        "equipment_id": "padded_vest",
        "price": 45,
        "tier": 1,
        "desc": "Лёгкая защита для первых вылазок.",
        "req_wave": 2,
        "req_level": 2,
    },
    {
        "id": "shop_hunter_mail",
        "equipment_id": "hunter_mail",
        "price": 85,
        "tier": 2,
        "desc": "Кольчуга лесных следопытов.",
        "req_wave": 3,
        "req_level": 4,
        "req_zone": 1,
    },
    {
        "id": "shop_frost_plate",
        "equipment_id": "frost_plate",
        "price": 150,
        "tier": 3,
        "desc": "Выдерживает удары ледяных тварей.",
        "req_wave": 5,
        "req_level": 6,
        "req_zone": 2,
        "req_quests": ["desert_hunt"],
    },
    {
        "id": "shop_caravan_plate",
        "equipment_id": "caravan_plate",
        "price": 220,
        "tier": 3,
        "desc": "Тяжёлые латы караванщиков пустыни.",
        "req_wave": 7,
        "req_level": 8,
        "req_zone": 3,
    },
    {
        "id": "shop_wraith_mail",
        "equipment_id": "wraith_mail",
        "price": 320,
        "tier": 4,
        "desc": "Лёгкая, но прочная — духи руин не догонят.",
        "req_wave": 9,
        "req_level": 10,
        "req_zone": 3,
        "req_quests": ["ruins_awakening"],
    },
    {
        "id": "shop_aegis_plate",
        "equipment_id": "aegis_plate",
        "price": 450,
        "tier": 5,
        "desc": "Эгида для самых кровавых боёв.",
        "req_wave": 12,
        "req_level": 12,
        "req_zone": 4,
    },
    {
        "id": "shop_ice_bulwark",
        "equipment_id": "ice_bulwark",
        "price": 580,
        "tier": 5,
        "desc": "Кована после победы над Ледяным стражем.",
        "req_wave": 14,
        "req_level": 14,
        "req_zone": 4,
        "req_ice_guardian": True,
    },
    {
        "id": "shop_border_armor",
        "equipment_id": "border_armor",
        "price": 780,
        "tier": 6,
        "desc": "Легендарный доспех покорителя рубежа.",
        "req_wave": 17,
        "req_level": 16,
        "req_zone": 5,
        "req_colossus": True,
    },
]

TIER_LABELS = {
    0: "I",
    1: "II",
    2: "III",
    3: "IV",
    4: "V",
    5: "VI",
    6: "VI+",
}

TIER_COLORS = {
    0: (160, 160, 170),
    1: (120, 200, 120),
    2: (100, 180, 255),
    3: (180, 140, 255),
    4: (255, 180, 80),
    5: (255, 120, 90),
    6: (255, 215, 0),
}

POTION_PRICE = 12
POTION_HEAL = 40


def all_weapon_names():
    return [STARTER_WEAPON["name"]] + [w["name"] for w in SHOP_WEAPONS]


LEGACY_WEAPON_STATS = {
    "Клинок света": (96, 78),
}

def weapon_stats_dict():
    stats = {STARTER_WEAPON["name"]: (STARTER_WEAPON["damage"], STARTER_WEAPON["range"])}
    for weapon in SHOP_WEAPONS:
        stats[weapon["name"]] = (weapon["damage"], weapon["range"])
    stats.update(LEGACY_WEAPON_STATS)
    return stats


def get_weapon_by_name(name):
    if name == STARTER_WEAPON["name"]:
        return STARTER_WEAPON
    for weapon in SHOP_WEAPONS:
        if weapon["name"] == name:
            return weapon
    return None


def effective_price(item, player):
    price = item.get("price", 0)
    if price <= 0:
        return 0
    discount = getattr(player, "relic_shop_discount", 0.0)
    return max(1, int(price * (1.0 - discount)))


def check_requirements(item, game):
    missing = []
    req_wave = item.get("req_wave", 1)
    if game.difficulty.wave < req_wave:
        missing.append(f"угроза {req_wave}")

    req_level = item.get("req_level", 1)
    if game.player.level < req_level:
        missing.append(f"ур. {req_level}")

    req_zone = item.get("req_zone", 0)
    max_zone = getattr(game, "max_zone_tier_reached", 0)
    if max_zone < req_zone:
        missing.append(f"зона {req_zone}+")

    for quest_id in item.get("req_quests", []):
        quest = QUESTS.get(quest_id, {})
        title = quest.get("title", quest_id)
        if quest_id not in game.quests.completed:
            missing.append(f"«{title}»")

    if item.get("req_ice_guardian") and not game.ice_guardian_defeated:
        missing.append("Ледяной страж")

    if item.get("req_colossus") and not game.sand_colossus_defeated:
        missing.append("Колосс пустыни")

    return len(missing) == 0, missing


def requirement_hint(item):
    parts = []
    if item.get("req_wave", 1) > 1:
        parts.append(f"Угроза {item['req_wave']}")
    if item.get("req_level", 1) > 1:
        parts.append(f"Ур. {item['req_level']}")
    if item.get("req_zone", 0) > 0:
        parts.append(f"Зона {item['req_zone']}+")
    for quest_id in item.get("req_quests", []):
        quest = QUESTS.get(quest_id, {})
        parts.append(quest.get("title", quest_id))
    if item.get("req_ice_guardian"):
        parts.append("Ледяной страж")
    if item.get("req_colossus"):
        parts.append("Колосс")
    return " · ".join(parts) if parts else "Доступно сразу"


class WeaponShopUI:
    CARD_H = 86
    CARD_GAP = 8
    SCROLL_STEP = 32
    HEADER_H = 118
    TAB_H = 34

    def __init__(self):
        self.tab = "weapons"
        self.scroll = 0
        self.buttons = {}
        self.font_title = pygame.font.SysFont("Arial", 34, bold=True)
        self.font_section = pygame.font.SysFont("Arial", 15, bold=True)
        self.font_label = pygame.font.SysFont("Arial", 16, bold=True)
        self.font_small = pygame.font.SysFont("Arial", 13)
        self.font_tiny = pygame.font.SysFont("Arial", 12)
        self.font_tab = pygame.font.SysFont("Arial", 14, bold=True)
        self._content_height = 0

    def reset_scroll(self):
        self.scroll = 0

    def _panel_rect(self, sw, sh):
        margin = 32
        top = self.HEADER_H + self.TAB_H + 10
        return pygame.Rect(margin, top, sw - margin * 2, sh - top - 78)

    def _visible_height(self, panel):
        return panel.height - 16

    def _clip_text(self, font, text, color, max_width):
        surf = font.render(text, True, color)
        if surf.get_width() <= max_width:
            return surf
        trimmed = text
        while trimmed and font.size(trimmed + "…")[0] > max_width:
            trimmed = trimmed[:-1]
        return font.render((trimmed + "…") if trimmed else "…", True, color)

    def _current_items(self):
        return SHOP_WEAPONS if self.tab == "weapons" else SHOP_ARMOR

    def _draw_tabs(self, screen, sw, mouse):
        tab_y = 96
        tab_w = 160
        gap = 12
        start_x = sw // 2 - tab_w - gap // 2
        for i, (tab_id, label) in enumerate((("weapons", "Оружие"), ("armor", "Броня"))):
            rect = pygame.Rect(start_x + i * (tab_w + gap), tab_y, tab_w, self.TAB_H)
            active = self.tab == tab_id
            hovered = rect.collidepoint(mouse)
            fill = (0, 110, 110) if active else ((50, 70, 50) if hovered else (32, 38, 32))
            border = (0, 220, 200) if active else (80, 100, 80)
            pygame.draw.rect(screen, fill, rect, border_radius=6)
            pygame.draw.rect(screen, border, rect, 2, border_radius=6)
            txt = self.font_tab.render(label, True, (255, 255, 255) if active else (180, 185, 175))
            screen.blit(txt, txt.get_rect(center=rect.center))
            self.buttons[f"tab_{tab_id}"] = rect

    def _draw_item_card(self, screen, game, item, card, is_weapon, mouse):
        unlocked, missing = check_requirements(item, game)
        if is_weapon:
            display_name = item["name"]
            stat_line = f"Урон {item['damage']} · Дальность {item['range']}"
            desc = item["desc"]
            owned = item["name"] in game.player.purchased_weapons
            equipped = game.player.weapon_name == item["name"]
            btn_key = item["id"]
        else:
            eq_id = item["equipment_id"]
            display_name = EQUIPMENT[eq_id]["name"]
            stat_line = format_armor_stats(eq_id)
            desc = item["desc"]
            owned = eq_id in getattr(game.player, "purchased_armor", [])
            equipped = game.equipment.slots.get("armor") == eq_id
            btn_key = item["id"]

        price = effective_price(item, game.player)
        tier_color = TIER_COLORS.get(item["tier"], (180, 180, 180))
        hovered = card.collidepoint(mouse)

        if owned:
            bg, border = (32, 48, 34), (0, 180, 80)
        elif not unlocked:
            bg, border = (28, 26, 30), (70, 60, 75)
        elif game.player.gold >= price:
            bg = (38, 50, 36) if hovered else (30, 38, 30)
            border = (255, 215, 0) if hovered else (150, 130, 0)
        else:
            bg, border = (28, 28, 28), (110, 60, 60)

        pygame.draw.rect(screen, bg, card, border_radius=8)
        pygame.draw.rect(screen, border, card, 2, border_radius=8)

        badge = pygame.Rect(card.x + 10, card.y + 10, 34, 22)
        pygame.draw.rect(screen, (*tier_color, 80), badge, border_radius=4)
        pygame.draw.rect(screen, tier_color, badge, 1, border_radius=4)
        tier_txt = self.font_tiny.render(TIER_LABELS.get(item["tier"], "?"), True, tier_color)
        screen.blit(tier_txt, tier_txt.get_rect(center=badge.center))

        name_color = (255, 255, 255) if unlocked or owned else (120, 118, 125)
        screen.blit(
            self.font_label.render(display_name, True, name_color),
            (card.x + 52, card.y + 10),
        )
        screen.blit(
            self._clip_text(self.font_small, stat_line, (170, 175, 165), card.width - 170),
            (card.x + 52, card.y + 32),
        )
        screen.blit(
            self._clip_text(self.font_tiny, desc, (130, 135, 125), card.width - 24),
            (card.x + 52, card.y + 50),
        )

        if owned:
            status = "НАДЕТО" if equipped else "КУПЛЕНО"
            status_color = (120, 255, 160) if equipped else (0, 200, 120)
        elif not unlocked:
            status = "Нужно: " + ", ".join(missing)
            status_color = (150, 130, 160)
        elif game.player.gold >= price:
            status = f"Купить · {price} G"
            status_color = (255, 220, 80)
        else:
            status = f"Нужно {price} G"
            status_color = (220, 100, 100)

        status_surf = self._clip_text(self.font_small, status, status_color, card.width - 120)
        screen.blit(status_surf, (card.right - status_surf.get_width() - 12, card.y + 28))

        if unlocked or owned:
            self.buttons[btn_key] = card

    def draw(self, screen, game):
        sw, sh = screen.get_size()
        mouse = pygame.mouse.get_pos()
        self.buttons = {}

        screen.fill((18, 22, 18))
        title = self.font_title.render("ЛАВКА ТОРГОВЦА", True, (255, 215, 0))
        screen.blit(title, title.get_rect(center=(sw // 2, 34)))

        threat = self.font_small.render(
            f"Угроза {game.difficulty.wave} · Ур. {game.player.level} · "
            f"Зона {getattr(game, 'max_zone_tier_reached', 0)}",
            True,
            (140, 150, 130),
        )
        screen.blit(threat, threat.get_rect(center=(sw // 2, 62)))

        gold_txt = self.font_section.render(f"Золото: {game.player.gold} G", True, (255, 240, 80))
        screen.blit(gold_txt, (sw // 2 - gold_txt.get_width() // 2, 82))

        self._draw_tabs(screen, sw, mouse)

        panel = self._panel_rect(sw, sh)
        panel_border = (80, 110, 70) if self.tab == "weapons" else (90, 100, 130)
        draw_rounded_panel(screen, panel, (22, 28, 22), panel_border, radius=12, alpha=235)

        list_top = panel.y + 8
        list_h = self._visible_height(panel)
        content_y = list_top - self.scroll
        items = self._current_items()
        is_weapon = self.tab == "weapons"
        self._content_height = len(items) * (self.CARD_H + self.CARD_GAP) + 8

        clip = screen.get_clip()
        screen.set_clip(pygame.Rect(panel.x + 4, list_top, panel.width - 8, list_h))

        for item in items:
            card = pygame.Rect(panel.x + 16, content_y, panel.width - 32, self.CARD_H)
            content_y += self.CARD_H + self.CARD_GAP
            if card.bottom < list_top or card.y > list_top + list_h:
                continue
            self._draw_item_card(screen, game, item, card, is_weapon, mouse)

        screen.set_clip(clip)

        max_scroll = max(0, self._content_height - list_h)
        self.scroll = max(0, min(max_scroll, self.scroll))
        if max_scroll > 0:
            bar_h = max(24, int(list_h * list_h / self._content_height))
            bar_y = list_top + int((list_h - bar_h) * self.scroll / max_scroll)
            pygame.draw.rect(screen, (40, 48, 40), (panel.right - 7, list_top, 4, list_h), border_radius=2)
            pygame.draw.rect(screen, (255, 215, 0), (panel.right - 7, bar_y, 4, bar_h), border_radius=2)

        footer_y = panel.bottom + 10
        armor_name = get_equipped_armor_name(game.equipment)
        cur = self.font_small.render(
            f"Оружие: {game.player.weapon_name} ({game.player.attack_damage} ур.)  ·  "
            f"Броня: {armor_name}  ·  HP {game.player.hp}/{game.player.max_hp}",
            True,
            (180, 185, 170),
        )
        screen.blit(cur, cur.get_rect(center=(sw // 2, footer_y)))

        potion_rect = pygame.Rect(sw // 2 - 220, footer_y + 18, 180, 36)
        back_rect = pygame.Rect(sw // 2 + 40, footer_y + 18, 180, 36)
        self.buttons["potion"] = potion_rect
        self.buttons["back"] = back_rect

        potion_hover = potion_rect.collidepoint(mouse)
        potion_price = effective_price({"price": POTION_PRICE}, game.player)
        can_potion = game.player.gold >= potion_price
        p_bg = (40, 55, 40) if potion_hover and can_potion else (28, 34, 28)
        p_border = (0, 180, 120) if can_potion else (90, 60, 60)
        pygame.draw.rect(screen, p_bg, potion_rect, border_radius=6)
        pygame.draw.rect(screen, p_border, potion_rect, 2, border_radius=6)
        potion_label = f"Зелье +{POTION_HEAL} HP · {potion_price} G"
        potion_surf = self.font_small.render(potion_label, True, (220, 240, 210))
        screen.blit(potion_surf, potion_surf.get_rect(center=potion_rect.center))

        back_hover = back_rect.collidepoint(mouse)
        pygame.draw.rect(screen, (35, 40, 35) if back_hover else (28, 32, 28), back_rect, border_radius=6)
        pygame.draw.rect(screen, (160, 160, 160), back_rect, 2, border_radius=6)
        back_surf = self.font_small.render("Назад в игру", True, (240, 240, 240))
        screen.blit(back_surf, back_surf.get_rect(center=back_rect.center))

        hint = self.font_tiny.render(
            "Вкладки Оружие / Броня · открывается по угрозе, уровню, зонам и квестам · колёсико — прокрутка",
            True,
            (95, 100, 90),
        )
        screen.blit(hint, hint.get_rect(center=(sw // 2, sh - 14)))

    def _try_buy_weapon(self, game, weapon):
        unlocked, _missing = check_requirements(weapon, game)
        if not unlocked:
            game.quests._notify(f"«{weapon['name']}» пока недоступно")
            return
        if weapon["name"] in game.player.purchased_weapons:
            game.player.weapon_name = weapon["name"]
            game.player.set_weapon_stats(weapon["damage"], weapon["range"])
            game._sync_player_build()
            game.quests._notify(f"Экипировано: {weapon['name']}")
            return
        price = effective_price(weapon, game.player)
        if game.player.gold < price:
            game.quests._notify(f"Нужно {price} G")
            return
        game.player.gold -= price
        game.player.purchased_weapons.append(weapon["name"])
        game.player.weapon_name = weapon["name"]
        game.player.set_weapon_stats(weapon["damage"], weapon["range"])
        game._sync_player_build()
        game.audio.play_sfx("coin")
        game.quests._notify(f"Куплено: {weapon['name']} (−{price} G)")

    def _try_buy_armor(self, game, armor):
        eq_id = armor["equipment_id"]
        name = EQUIPMENT[eq_id]["name"]
        unlocked, _missing = check_requirements(armor, game)
        if not unlocked:
            game.quests._notify(f"«{name}» пока недоступно")
            return
        purchased = getattr(game.player, "purchased_armor", [])
        if eq_id in purchased:
            game.equipment.equip(game.player, eq_id)
            game.quests._notify(f"Надето: {name}")
            return
        price = effective_price(armor, game.player)
        if game.player.gold < price:
            game.quests._notify(f"Нужно {price} G")
            return
        game.player.gold -= price
        if eq_id not in purchased:
            purchased.append(eq_id)
            game.player.purchased_armor = purchased
        game.equipment.equip(game.player, eq_id)
        game.audio.play_sfx("coin")
        game.quests._notify(f"Куплено: {name} (−{price} G)")

    def handle_event(self, event, game):
        panel = self._panel_rect(game.current_w, game.current_h)
        list_h = self._visible_height(panel)
        max_scroll = max(0, self._content_height - list_h)

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return "back"

        if event.type == pygame.MOUSEWHEEL:
            self.scroll = max(0, min(max_scroll, self.scroll - event.y * self.SCROLL_STEP))
            return None

        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return None

        pos = event.pos

        for tab_id in ("weapons", "armor"):
            tab_btn = self.buttons.get(f"tab_{tab_id}")
            if tab_btn and tab_btn.collidepoint(pos):
                if self.tab != tab_id:
                    self.tab = tab_id
                    self.scroll = 0
                return None

        if self.buttons.get("back") and self.buttons["back"].collidepoint(pos):
            return "back"

        if self.buttons.get("potion") and self.buttons["potion"].collidepoint(pos):
            price = effective_price({"price": POTION_PRICE}, game.player)
            if game.player.gold >= price:
                game.player.gold -= price
                game.player.potions_count += 1
                game.audio.play_sfx("potion_pickup")
                game.effects.spawn_potion_pickup(
                    game.player.rect.centerx, game.player.rect.centery
                )
                game.quests._notify(f"Зелье куплено (+{POTION_HEAL} HP при использовании)")
            return None

        if self.tab == "weapons":
            for weapon in SHOP_WEAPONS:
                if self.buttons.get(weapon["id"]) and self.buttons[weapon["id"]].collidepoint(pos):
                    self._try_buy_weapon(game, weapon)
                    return None
        else:
            for armor in SHOP_ARMOR:
                if self.buttons.get(armor["id"]) and self.buttons[armor["id"]].collidepoint(pos):
                    self._try_buy_armor(game, armor)
                    return None

        return None
