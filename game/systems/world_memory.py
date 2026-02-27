import json

from game.config import DATA_DIR, WORLD_MEMORY_PATH


class WorldMemory:
    def __init__(self):
        self.data = {
            "runs": 0,
            "best_level": 1,
            "final_types": [],
            "action_buffer": [],
            "permanent_distortion_level": 0.0,
            "total_rupturas": 0,
            "total_integraciones": 0,
        }
        self.load()

    def load(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        if WORLD_MEMORY_PATH.exists():
            self.data.update(json.loads(WORLD_MEMORY_PATH.read_text()))
        else:
            self.save()

    def save(self):
        WORLD_MEMORY_PATH.write_text(json.dumps(self.data, indent=2))

    def register_action(self, action: str):
        self.data["action_buffer"].append(action)
        self.data["action_buffer"] = self.data["action_buffer"][-160:]

    def complete_run(self, reached_level: int, archetype: str):
        self.data["runs"] += 1
        self.data["best_level"] = max(self.data["best_level"], reached_level)
        self.data["final_types"].append(archetype)

        if archetype in ("Duelist", "Overlord"):
            self.data["total_rupturas"] += 1
            self.data["permanent_distortion_level"] = min(1.0, self.data["permanent_distortion_level"] + 0.05)
        else:
            self.data["total_integraciones"] += 1
            self.data["permanent_distortion_level"] = max(0.0, self.data["permanent_distortion_level"] - 0.03)

        self.save()
