from __future__ import annotations

import pygame

from game.config import HEIGHT, WHITE, WIDTH
from game.scenes.base_scene import BaseScene
from game.scenes.gameplay_scene import GameplayScene


class TransitionScene(BaseScene):
    def __init__(self, ctx: dict):
        super().__init__(ctx)
        self.t = 0.0

    def update(self, dt: float):
        self.t += dt
        if self.t > 0.7:
            self._next = GameplayScene(self.ctx)

    def render(self, screen):
        screen.fill((4, 5, 8))
        a = int(255 * min(1.0, self.t / 0.7))
        txt = self.ctx["small"].render("Reconfigurando sala...", True, WHITE)
        txt.set_alpha(a)
        screen.blit(txt, txt.get_rect(center=(WIDTH // 2, HEIGHT // 2)))
