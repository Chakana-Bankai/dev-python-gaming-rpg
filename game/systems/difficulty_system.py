from __future__ import annotations


class DifficultySystem:
    def __init__(self):
        self.performance_index = 0.0
        self.enemy_speed_mult = 1.0
        self.enemy_density_mult = 1.0
        self.energy_drop_mult = 1.0

    def evaluate(self, precision: float, damage_taken_rate: float, room_time: float):
        skill = (precision * 0.55) + (max(0.0, 1.0 - damage_taken_rate) * 0.3) + (max(0.0, 1.0 - room_time / 75.0) * 0.15)
        self.performance_index = max(0.0, min(1.0, skill))

        if self.performance_index > 0.62:
            self.enemy_speed_mult = 1.12
            self.enemy_density_mult = 1.2
            self.energy_drop_mult = 0.9
        elif self.performance_index < 0.35:
            self.enemy_speed_mult = 0.9
            self.enemy_density_mult = 0.82
            self.energy_drop_mult = 1.25
        else:
            self.enemy_speed_mult = 1.0
            self.enemy_density_mult = 1.0
            self.energy_drop_mult = 1.0

    def apply_to_game_manager(self, gm):
        gm.difficulty = max(1, int(gm.difficulty * self.enemy_density_mult))
        for e in gm.enemies:
            if hasattr(e, "speed"):
                e.speed *= self.enemy_speed_mult
