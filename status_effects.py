"""Статус-эффекты: яд, ожог, заморозка."""


STATUS_DEFS = {
    "poison": {"color": (80, 220, 80), "label": "Яд"},
    "burn": {"color": (255, 120, 40), "label": "Ожог"},
    "freeze": {"color": (140, 220, 255), "label": "Лед"},
}


class StatusEffectManager:
    def __init__(self):
        self.effects = {}

    def clear(self):
        self.effects = {}

    def apply(self, name, duration, potency=1):
        if name not in STATUS_DEFS:
            return
        current = self.effects.get(name)
        if current:
            current["duration"] = max(current["duration"], duration)
            current["potency"] = max(current["potency"], potency)
        else:
            self.effects[name] = {"duration": duration, "potency": potency, "tick": 0}

    def has(self, name):
        return name in self.effects

    def speed_multiplier(self):
        if "freeze" in self.effects:
            return max(0.35, 1.0 - 0.45 * self.effects["freeze"]["potency"])
        return 1.0

    def tick(self, target, on_damage=None):
        expired = []
        for name, data in self.effects.items():
            data["duration"] -= 1
            data["tick"] += 1
            if name == "poison" and data["tick"] >= 50:
                data["tick"] = 0
                if on_damage:
                    on_damage(data["potency"] * 3)
            elif name == "burn" and data["tick"] >= 40:
                data["tick"] = 0
                if on_damage:
                    on_damage(data["potency"] * 4)
            if data["duration"] <= 0:
                expired.append(name)
        for name in expired:
            del self.effects[name]

    def active_labels(self):
        result = []
        for name, data in self.effects.items():
            meta = STATUS_DEFS.get(name, {})
            result.append((meta.get("label", name), meta.get("color", (200, 200, 200)), data["duration"]))
        return result

    def to_dict(self):
        return dict(self.effects)

    def load_dict(self, data):
        self.effects = dict(data or {})
