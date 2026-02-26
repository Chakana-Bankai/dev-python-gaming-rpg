import pygame
from pygame.math import Vector2

from game.entities.enemy import Enemy


class Boss(Enemy):
    def __init__(self, pos: Vector2, level: int):
        super().__init__(pos, hp=180 + level * 40, speed=100 + level * 4, damage=18 + level)
        self.image = pygame.Surface((46, 46), pygame.SRCALPHA)
        self.image.fill((120, 80, 210))
        self.rect = self.image.get_rect(center=(int(pos.x), int(pos.y)))
