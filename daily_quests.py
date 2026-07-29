"""
botyarajump - Daily Quests & Challenges Manager
Generates daily quests, tracks progress, and grants coin rewards.
"""

import datetime
import random
from settings import save_manager


QUEST_POOL = [
    {
        "id": "score_1000",
        "title_ru": "Набери 1000 очков",
        "title_en": "Score 1,000 points",
        "target": 1000,
        "reward": 100,
        "type": "score"
    },
    {
        "id": "score_2500",
        "title_ru": "Набери 2500 очков",
        "title_en": "Score 2,500 points",
        "target": 2500,
        "reward": 200,
        "type": "score"
    },
    {
        "id": "coins_30",
        "title_ru": "Собери 30 монет",
        "title_en": "Collect 30 coins",
        "target": 30,
        "reward": 80,
        "type": "coins"
    },
    {
        "id": "coins_60",
        "title_ru": "Собери 60 монет",
        "title_en": "Collect 60 coins",
        "target": 60,
        "reward": 150,
        "type": "coins"
    },
    {
        "id": "kill_5_enemies",
        "title_ru": "Победи 5 врагов",
        "title_en": "Defeat 5 enemies",
        "target": 5,
        "reward": 120,
        "type": "kills"
    },
    {
        "id": "land_50_platforms",
        "title_ru": "Прыгни на 50 платформ",
        "title_en": "Land on 50 platforms",
        "target": 50,
        "reward": 90,
        "type": "platforms"
    },
    {
        "id": "land_10_special",
        "title_ru": "Прыгни на 10 пружин или порталов",
        "title_en": "Land on 10 springs or portals",
        "target": 10,
        "reward": 110,
        "type": "special_platforms"
    }
]


class DailyQuestManager:
    """Manages daily quests."""

    def __init__(self):
        self.quests = []
        self.check_and_load_quests()

    def check_and_load_quests(self):
        """Check current date and load or generate 3 daily quests."""
        today_str = datetime.date.today().isoformat()
        saved = save_manager.save_data.get("daily_quests_data", {})

        if saved.get("date") == today_str and "quests" in saved:
            self.quests = saved["quests"]
        else:
            selected = random.sample(QUEST_POOL, 3)
            self.quests = []
            for q in selected:
                self.quests.append({
                    "id": q["id"],
                    "title_ru": q["title_ru"],
                    "title_en": q["title_en"],
                    "target": q["target"],
                    "current": 0,
                    "reward": q["reward"],
                    "type": q["type"],
                    "completed": False,
                    "claimed": False
                })
            self._save()

    def _save(self):
        """Save quest state to save_data.json."""
        today_str = datetime.date.today().isoformat()
        save_manager.save_data["daily_quests_data"] = {
            "date": today_str,
            "quests": self.quests
        }
        save_manager.save()

    def on_score(self, score):
        """Update score quests."""
        for q in self.quests:
            if q["type"] == "score" and not q["completed"]:
                q["current"] = max(q["current"], score)
                if q["current"] >= q["target"]:
                    q["completed"] = True
        self._save()

    def on_coin(self, amount=1):
        """Update coin quests."""
        for q in self.quests:
            if q["type"] == "coins" and not q["completed"]:
                q["current"] += amount
                if q["current"] >= q["target"]:
                    q["completed"] = True
        self._save()

    def on_kill(self, amount=1):
        """Update enemy kill quests."""
        for q in self.quests:
            if q["type"] == "kills" and not q["completed"]:
                q["current"] += amount
                if q["current"] >= q["target"]:
                    q["completed"] = True
        self._save()

    def on_platform(self, ptype):
        """Update platform landing quests."""
        for q in self.quests:
            if q["type"] == "platforms" and not q["completed"]:
                q["current"] += 1
                if q["current"] >= q["target"]:
                    q["completed"] = True
            elif q["type"] == "special_platforms" and not q["completed"]:
                if ptype in ("spring", "portal"):
                    q["current"] += 1
                    if q["current"] >= q["target"]:
                        q["completed"] = True
        self._save()

    def claim_reward(self, quest_index):
        """Claim coins for a completed quest."""
        if 0 <= quest_index < len(self.quests):
            q = self.quests[quest_index]
            if q["completed"] and not q["claimed"]:
                q["claimed"] = True
                save_manager.add_coins(q["reward"])
                self._save()
                return q["reward"]
        return 0


quest_manager = DailyQuestManager()
