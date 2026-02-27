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
        self.options = ["Iniciar descenso", "Audio ON/OFF", "Salir"]
        self.selected = 0

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and self.ready:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.selected = (self.selected - 1) % len(self.options)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.selected = (self.selected + 1) % len(self.options)
            elif event.key == pygame.K_RETURN:
                if self.selected == 0:
                    self._next = NarrativeScene(self.ctx, fragment_index=0)
                elif self.selected == 1:
                    self.ctx["audio"].set_muted(not self.ctx["audio"].muted)
                    if not self.ctx["audio"].muted:
                        self.ctx["audio"].play_music("menu")
                elif self.selected == 2:
                    pygame.event.post(pygame.event.Event(pygame.QUIT))

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
        tip = small.render("Menu: ↑/↓ + ENTER", True, (200, 210, 240))
        tt = title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 20))
        screen.blit(title, tt)
        if self.ready:
            screen.blit(tip, tip.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 10)))
            for i, opt in enumerate(self.options):
                col = (120, 230, 170) if i == self.selected else (210, 214, 236)
                label = small.render(("> " if i == self.selected else "  ") + opt, True, col)
                screen.blit(label, label.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 45 + i * 30)))
        veil = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        veil.fill((20, 8, 30, max(0, 180 - alpha)))
        screen.blit(veil, (0, 0))
