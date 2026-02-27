from __future__ import annotations

import random


class ProceduralSystem:
    EVENTS = [
        "sala_silenciosa",
        "vision_reducida",
        "sin_disparo_3s",
        "sala_espejo",
        None,
        None,
    ]

    def __init__(self):
        self.seed = None
        self.rng = random.Random()

    def start_run(self, explicit_seed: int | None = None):
        self.seed = explicit_seed if explicit_seed is not None else random.randint(10000, 999999)
        self.rng.seed(self.seed)
        return self.seed

    def room_event(self):
        return self.rng.choice(self.EVENTS)

    def layout_variation(self):
        return {
            "enemy_spread": self.rng.uniform(0.8, 1.25),
            "cover_shift": self.rng.uniform(-25, 25),
        }
