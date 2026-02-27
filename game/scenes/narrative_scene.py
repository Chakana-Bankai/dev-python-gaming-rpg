from __future__ import annotations

import random

import pygame

from game.config import HEIGHT, WHITE, WIDTH
from game.scenes.base_scene import BaseScene
from game.scenes.transition_scene import TransitionScene


class NarrativeScene(BaseScene):
    def __init__(self, ctx: dict, fragment_index: int):
        super().__init__(ctx)
        self.fragment_index = fragment_index
        self.time = 0.0
        self.advance = False
        self.fragments = ctx["narrative_data"]["fragments"]
        self.text = self._resolve_text()

    def _resolve_text(self):
        frag = self.fragments[self.fragment_index]
        base = random.choice(frag["base"])
        lucidez = self.ctx["progression"].lucidez
        if lucidez > 0.6 and frag.get("unlocked"):
            base += " " + random.choice(frag["unlocked"])
        return base

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE):
            self.advance = True

    def update(self, dt: float):
        self.time += dt
        if self.advance and self.time > 0.5:
            self._next = TransitionScene(self.ctx)

    def render(self, screen):
        screen.fill((10, 12, 18))
        title_font = self.ctx["font"]
        txt_font = self.ctx["small"]

        phase = self.fragments[self.fragment_index]["title"]
        t = min(1.0, self.time / 0.8)
        out = max(0.0, (self.time - 2.5) / 1.0)
        alpha = int(255 * min(t, 1.0 - out if self.advance else t))

        title = title_font.render(phase, True, WHITE)
        body = txt_font.render(self.text, True, (220, 225, 235))
        title.set_alpha(alpha)
        body.set_alpha(alpha)
        screen.blit(title, title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 26)))
        screen.blit(body, body.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 16)))
