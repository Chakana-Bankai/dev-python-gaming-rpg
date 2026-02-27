from __future__ import annotations

import pygame

from game.config import HEIGHT, WHITE, WIDTH
from game.scenes.base_scene import BaseScene
from game.scenes.narrative_scene import NarrativeScene


class IntroScene(BaseScene):
    def __init__(self, ctx: dict):
        super().__init__(ctx)
        self.t = 0.0
        self.ready = False

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and self.ready:
            self._next = NarrativeScene(self.ctx, fragment_index=0)

    def update(self, dt: float):
        self.t += dt
        if self.t > 1.0:
            self.ready = True

    def render(self, screen):
        screen.fill((8, 10, 16))
        alpha = min(255, int(self.t * 180))
        font = self.ctx["font"]
        small = self.ctx["small"]
        title = font.render("Roguelike 2D Iniciático Evolutivo", True, WHITE)
        tip = small.render("Pulsa ENTER para descender", True, (200, 210, 240))
        tt = title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 20))
        screen.blit(title, tt)
        if self.ready:
            screen.blit(tip, tip.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 30)))
        veil = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        veil.fill((20, 8, 30, max(0, 180 - alpha)))
        screen.blit(veil, (0, 0))
