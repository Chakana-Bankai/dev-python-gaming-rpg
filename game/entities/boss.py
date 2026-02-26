import pygame
from pygame.math import Vector2

from game.entities.enemy import Enemy


class Boss(Enemy):
    """Boss progresivo con fases por vida."""

    def __init__(self, pos: Vector2, level: int):
        super().__init__(pos, hp=220 + level * 55, speed=95 + level * 5, damage=20 + level)
        self.image = pygame.Surface((46, 46), pygame.SRCALPHA)
        self.image.fill((120, 80, 210))
        self.rect = self.image.get_rect(center=(int(pos.x), int(pos.y)))
        self.phase = 1

    def update(self, dt: float, player_pos: Vector2):
        ratio = self.hp / self.max_hp if self.max_hp else 0
        if ratio < 0.66 and self.phase == 1:
            self.phase = 2
            self.speed *= 1.2
            self.damage *= 1.1
        if ratio < 0.33 and self.phase == 2:
            self.phase = 3
            self.speed *= 1.2
            self.damage *= 1.15
        super().update(dt, player_pos)
