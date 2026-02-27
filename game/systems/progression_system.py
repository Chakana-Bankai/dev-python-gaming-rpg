from __future__ import annotations


class ProgressionSystem:
    PALETTES = {
        "Caos": {"bg": (16, 18, 24), "ui": (220, 110, 120)},
        "Purificación": {"bg": (14, 22, 26), "ui": (140, 220, 200)},
        "Integración": {"bg": (20, 16, 30), "ui": (195, 185, 240)},
    }

    def __init__(self, save_data: dict):
        self.lucidez = float(save_data.get("lucidez", 0.0))
        self.symbolic_state = "Caos"
        self.hidden_text_unlocked = self.lucidez > 0.45

    def on_new_run(self):
        self.lucidez += 0.03
        self._update_symbolic_state()

    def on_room_cleared(self):
        self.lucidez += 0.02
        self._update_symbolic_state()

    def _update_symbolic_state(self):
        if self.lucidez > 1.0:
            self.symbolic_state = "Integración"
        elif self.lucidez > 0.45:
            self.symbolic_state = "Purificación"
        else:
            self.symbolic_state = "Caos"
        self.hidden_text_unlocked = self.lucidez > 0.45

    def palette(self):
        return self.PALETTES[self.symbolic_state]
