import pygame
from pygame.math import Vector2

from game.entities.enemy import Enemy


class Reflection(Enemy):
    def __init__(self, pos: Vector2, style: dict):
        speed = 140 if style.get("mobile") else 110
        hp = 90 if style.get("aggressive") else 120
        super().__init__(pos, hp=hp, speed=speed, damage=20)
        self.image.fill((170, 110, 220))
