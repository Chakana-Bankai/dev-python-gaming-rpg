from __future__ import annotations

import pygame

from game.config import HEIGHT, WHITE, WIDTH
from game.core.state_machine import GameState
from game.scenes.gameplay_scene import GameplayScene


class BossScene(GameplayScene):
    def update(self, dt: float):
        super().update(dt)
        self.ctx["camera"].set_boss_zoom(True)
        if self.gm.sm.is_state(GameState.RUNNING):
            self._next = GameplayScene(self.ctx)

    def render(self, screen):
        super().render(screen)
        warn = self.ctx["small"].render("EL GUARDIÁN TE OBSERVA", True, WHITE)
        screen.blit(warn, warn.get_rect(center=(WIDTH // 2, HEIGHT - 20)))
