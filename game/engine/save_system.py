from __future__ import annotations

import json
from pathlib import Path


class SaveSystem:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.data = self._load()

    def _default_data(self):
        return {
            "runs_completed": 0,
            "total_deaths": 0,
            "rooms_played": 0,
            "average_room_time": 0.0,
            "unlocked_archetypes": ["Iniciado"],
            "archetype_unlocked": "Iniciado",
            "consciousness_level": 0.0,
            "lucidez": 0.0,
            "last_seed": None,
            "best_room_time": None,
        }

    def _load(self):
        if not self.path.exists():
            d = self._default_data()
            self._save(d)
            return d
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            d = self._default_data()
            self._save(d)
            return d

    def _save(self, payload):
        self.path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    def flush(self):
        self._save(self.data)

    def register_room_time(self, room_time: float):
        d = self.data
        d["rooms_played"] += 1
        n = d["rooms_played"]
        d["average_room_time"] = ((d["average_room_time"] * (n - 1)) + room_time) / max(1, n)
        if d["best_room_time"] is None or room_time < d["best_room_time"]:
            d["best_room_time"] = room_time

    def register_run_end(self, victory: bool, seed: int):
        if victory:
            self.data["runs_completed"] += 1
            self.data["lucidez"] += 0.24
            self.data["consciousness_level"] = min(1.0, self.data["consciousness_level"] + 0.18)
        else:
            self.data["total_deaths"] += 1
            self.data["lucidez"] += 0.08
            self.data["consciousness_level"] = min(1.0, self.data["consciousness_level"] + 0.04)
        self.data["last_seed"] = seed

        if self.data["runs_completed"] >= 1:
            unlocks = {"Iniciado", "Guerrero", "Testigo", "Sombra"}
            self.data["unlocked_archetypes"] = sorted(unlocks)
        self.flush()
