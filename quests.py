"""Система квестов — цели, награды, прогресс."""



QUESTS = {

    "first_steps": {

        "title": "Первые шаги",

        "description": "Старейшина просит очистить лес от слаймов.",

        "objective": "Убить 5 слаймов",

        "type": "kill_slime",

        "target": 5,

        "reward_gold": 20,

        "reward_text": "Научился рывку [Shift]",

        "unlocks_dash": True,

        "prerequisite": None,

    },

    "desert_hunt": {

        "title": "Охота на стражей",

        "description": "Пустынные боссы угрожают караванам.",

        "objective": "Убить 2 синих боссов",

        "type": "kill_boss",

        "target": 2,

        "reward_gold": 45,

        "reward_text": "+15 макс. HP",

        "reward_max_hp": 15,

        "prerequisite": "first_steps",

    },

    "frost_peak": {

        "title": "Ледяная вершина",

        "description": "Разведчик просит уничтожить ледяных слаймов.",

        "objective": "Убить 8 ледяных слаймов",

        "type": "kill_frost",

        "target": 8,

        "reward_gold": 60,

        "reward_text": "Звание «Страж рубежа»",

        "reward_title": "Страж рубежа",

        "prerequisite": "desert_hunt",

    },

    "frost_lord": {

        "title": "Повелитель льда",

        "description": "Ледяной страж пробудился на крайнем севере.",

        "objective": "Убить Ледяного стража",

        "type": "kill_ice_lord",

        "target": 1,

        "reward_gold": 100,

        "reward_text": "Звание «Покоритель Рубежа»",

        "reward_title": "Покоритель Рубежа",

        "reward_max_hp": 20,

        "prerequisite": "frost_peak",

    },

    "ruins_awakening": {

        "title": "Пробуждение руин",

        "description": "Мистик просит очистить древние руины от призраков.",

        "objective": "Убить 6 призраков руин",

        "type": "kill_wraith",

        "target": 6,

        "reward_gold": 80,

        "reward_text": "Разблокирована молния [1]",

        "prerequisite": "frost_lord",

    },

    "sand_titan": {

        "title": "Песчаный титан",

        "description": "Колосс пустыни блокирует торговые пути.",

        "objective": "Убить Песчаного колосса",

        "type": "kill_colossus",

        "target": 1,

        "reward_gold": 150,

        "reward_text": "Звание «Легенда Рубежа»",

        "reward_title": "Легенда Рубежа",

        "reward_max_hp": 25,

        "prerequisite": "ruins_awakening",

    },

}





class QuestManager:

    def __init__(self):

        self.active_quest = None

        self.completed = []

        self.progress = {}

        self.notifications = []

        self.player_title = ""



    def reset(self):

        self.active_quest = None

        self.completed = []

        self.progress = {}

        self.notifications = []

        self.player_title = ""



    def to_dict(self):

        return {

            "active_quest": self.active_quest,

            "completed": list(self.completed),

            "progress": dict(self.progress),

            "player_title": self.player_title,

        }



    def load_dict(self, data):

        if not data:

            return

        self.active_quest = data.get("active_quest")

        self.completed = list(data.get("completed", []))

        self.progress = dict(data.get("progress", {}))

        self.player_title = data.get("player_title", "")



    def available_quests(self):

        result = []

        for qid, quest in QUESTS.items():

            if qid in self.completed:

                continue

            prereq = quest.get("prerequisite")

            if prereq and prereq not in self.completed:

                continue

            if self.active_quest == qid:

                continue

            result.append(qid)

        return result



    def start_quest(self, quest_id):

        if quest_id not in QUESTS or quest_id in self.completed:

            return False

        if self.active_quest:

            return False

        prereq = QUESTS[quest_id].get("prerequisite")

        if prereq and prereq not in self.completed:

            return False

        self.active_quest = quest_id

        self.progress[quest_id] = 0

        self._notify(f"Квест: {QUESTS[quest_id]['title']}")

        return True



    def increment(self, event_type, amount=1):

        if not self.active_quest:

            return None

        quest = QUESTS[self.active_quest]

        if quest["type"] != event_type:

            return None

        self.progress[self.active_quest] = self.progress.get(self.active_quest, 0) + amount

        if self.progress[self.active_quest] >= quest["target"]:

            return self.complete_active()

        return None



    def complete_active(self):

        if not self.active_quest:

            return None

        qid = self.active_quest

        quest = QUESTS[qid]

        self.completed.append(qid)

        self.active_quest = None

        rewards = {

            "gold": quest.get("reward_gold", 0),

            "max_hp": quest.get("reward_max_hp", 0),

            "unlocks_dash": quest.get("unlocks_dash", False),

            "title": quest.get("reward_title", ""),

            "text": quest.get("reward_text", ""),

            "quest_id": qid,

        }

        if rewards["title"]:

            self.player_title = rewards["title"]

        self._notify(f"Завершено: {quest['title']}")

        return rewards



    def active_progress_text(self):

        if not self.active_quest:

            return None

        quest = QUESTS[self.active_quest]

        current = self.progress.get(self.active_quest, 0)

        return f"{quest['title']}: {current}/{quest['target']}"



    def active_objective(self):

        if not self.active_quest:

            return None

        return QUESTS[self.active_quest]["objective"]



    def _notify(self, text):

        self.notifications.append({"text": text, "timer": 180})



    def update(self):

        for note in self.notifications:

            note["timer"] -= 1

        self.notifications = [n for n in self.notifications if n["timer"] > 0]

