from __future__ import annotations

import random

import pygame

from game.config import HEIGHT, WHITE, WIDTH
from game.scenes.base_scene import BaseScene


class EndingScene(BaseScene):
    def __init__(self, ctx: dict):
        super().__init__(ctx)
        self.t = 0.0
        self.messages = [
            "El ciclo no termina: aprende.",
            "La geometría interior vuelve a llamarte.",
            "Cada run deja memoria en la conciencia.",
            "El Guardián cayó, pero el espejo sigue abierto.",
        ]
        self.msg = random.choice(self.messages)
        self.persisted = False

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN and self.t > 1.1:
            self.ctx["progression"].on_new_run()
            seed = self.ctx["procedural"].start_run()
            self.ctx["state"].reset_run(self.ctx["save"].data.get("archetype_unlocked", "Iniciado"), seed)
            self.ctx["gm"] = None
            from game.scenes.narrative_scene import NarrativeScene

            self._next = NarrativeScene(self.ctx, fragment_index=min(5, self.ctx["save"].data["runs_completed"]))

    def update(self, dt: float):
        self.t += dt
        if not self.persisted and self.t > 0.4:
            st = self.ctx["state"].run
            self.ctx["save"].register_run_end(st.victory, st.seed or 0)
            self.persisted = True

    def render(self, screen):
        screen.fill((0, 0, 0))

        alpha = min(255, int(self.t * 170))
        veil = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        veil.fill((0, 0, 0, 200))
        screen.blit(veil, (0, 0))

        title = "FINALIZACIÓN" if self.ctx["state"].run.victory else "FIN DE CICLO"
        t = self.ctx["font"].render(title, True, WHITE)
        t.set_alpha(alpha)

        summary = self.ctx["small"].render(self.msg, True, (220, 224, 240))
        summary.set_alpha(alpha)

        s = self.ctx["save"].data
        stats = self.ctx["small"].render(
            f"Runs: {s['runs_completed']}  Muertes: {s['total_deaths']}  Lucidez: {s['lucidez']:.2f}",
            True,
            (188, 198, 232),
        )
        stats.set_alpha(alpha)

        prompt = self.ctx["small"].render("ENTER para continuar el siguiente ciclo", True, (170, 175, 200))
        prompt.set_alpha(alpha)

        screen.blit(t, t.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 40)))
        screen.blit(summary, summary.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 8)))
        screen.blit(stats, stats.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 42)))
        if self.t > 1.1:
            screen.blit(prompt, prompt.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 78)))
