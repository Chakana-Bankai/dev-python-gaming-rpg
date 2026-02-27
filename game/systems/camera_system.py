from __future__ import annotations

import random

from pygame.math import Vector2


class CameraSystem:
    def __init__(self):
        self.offset = Vector2()
        self.shake = 0.0
        self.zoom = 1.0

    def add_shake(self, amount: float):
        self.shake = max(self.shake, amount)

    def nudge_to_shot(self, direction: Vector2):
        if direction.length_squared() > 0:
            self.offset += direction.normalize() * 5

    def set_boss_zoom(self, active: bool):
        self.zoom = 1.04 if active else 1.0

    def update(self, dt: float):
        self.shake = max(0.0, self.shake - dt * 10)
        jitter = Vector2(random.uniform(-1, 1), random.uniform(-1, 1)) * self.shake * 2.0
        self.offset = self.offset * 0.86 + jitter

    def apply_rect(self, rect):
        return rect.move(int(self.offset.x), int(self.offset.y))
