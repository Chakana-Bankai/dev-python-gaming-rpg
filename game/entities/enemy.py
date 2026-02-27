import math
import random

import pygame
from pygame.math import Vector2


class Enemy(pygame.sprite.Sprite):
    """Enemigo base con variantes ligeras para mejorar variedad de combate."""

    def __init__(self, pos: Vector2, hp: float, speed: float, damage: float, kind: str = "chaser"):
        super().__init__()
        self.kind = kind
        self.image = pygame.Surface((24, 24), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(int(pos.x), int(pos.y)))
        self.pos = Vector2(pos)
        self.max_hp = hp
        self.hp = hp
        self.speed = speed
        self.damage = damage
        self.phase = random.random() * 6.28

        if self.kind == "rusher":
            self.image.fill((240, 120, 90))
            self.speed *= 1.35
            self.hp *= 0.8
        elif self.kind == "tank":
            self.image.fill((170, 80, 180))
            self.speed *= 0.75
            self.hp *= 1.55
            self.damage *= 1.15
        else:
            self.image.fill((220, 78, 96))

    def take_damage(self, dmg: float):
        self.hp -= dmg
        if self.hp <= 0:
            self.kill()
            return True
        return False

    def update(self, dt: float, player_pos: Vector2):
        d = player_pos - self.pos
        if d.length_squared() == 0:
            return

        direction = d.normalize()
        if self.kind == "rusher":
            self.phase += dt * 8
            strafe = Vector2(-direction.y, direction.x) * (0.35 * abs(math.sin(self.phase)))
            direction = (direction + strafe).normalize()
        elif self.kind == "tank":
            self.phase += dt * 2.5
            direction = (direction * (0.9 + 0.1 * abs(math.sin(self.phase)))).normalize()

        self.pos += direction * self.speed * dt
        self.rect.center = (int(self.pos.x), int(self.pos.y))
