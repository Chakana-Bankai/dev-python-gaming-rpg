from __future__ import annotations

import random

import pygame

from game.config import HEIGHT, WHITE, WIDTH
from game.scenes.base_scene import BaseScene
from game.scenes.narrative_scene import NarrativeScene


class EndingScene(BaseScene):
    def __init__(self, ctx: dict):
        super().__init__(ctx)
        self.t = 0.0
        self.messages = [
            "El ciclo no termina: aprende.",
            "La geometría interior vuelve a llamarte.",
            "Cada run deja memoria en la conciencia.",
        ]
        self.msg = random.choice(self.messages)
        self.persisted = False

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN and self.t > 0.8:
            self.ctx["progression"].on_new_run()
            self._next = NarrativeScene(self.ctx, fragment_index=min(5, self.ctx["save"].data["runs_completed"]))

    def update(self, dt: float):
        self.t += dt
        if not self.persisted and self.t > 0.4:
            st = self.ctx["state"].run
            self.ctx["save"].register_run_end(st.victory, st.seed or 0)
            self.persisted = True

    def render(self, screen):
        screen.fill((10, 8, 16))
        title = "Integración" if self.ctx["state"].run.victory else "Caída"
        t = self.ctx["font"].render(title, True, WHITE)
        d = self.ctx["small"].render(self.msg, True, (210, 214, 232))
        r = self.ctx["small"].render("ENTER para reiniciar ciclo", True, (170, 175, 200))
        screen.blit(t, t.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 24)))
        screen.blit(d, d.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 16)))
        if self.t > 0.8:
            screen.blit(r, r.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 54)))
