class TensionSystem:
    """Calcula tensión dinámica según conducta del jugador."""

    def __init__(self):
        self.tension_level = 0.0

    def update(self, shots_fired: int, damage_taken: float, enemies_alive: int, dt: float):
        target = shots_fired * 0.01 + damage_taken * 0.03 + enemies_alive * 0.06
        self.tension_level += (target - self.tension_level) * min(1.0, dt * 4.0)
        self.tension_level = max(0.0, min(10.0, self.tension_level))
        return self.tension_level
