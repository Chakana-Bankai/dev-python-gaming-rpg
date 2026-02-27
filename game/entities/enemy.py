import math
import random

import pygame
from pygame.math import Vector2


class Enemy(pygame.sprite.Sprite):
    """Enemigo base con variantes ligeras para mejorar variedad de combate."""

    def __init__(self, pos: Vector2, hp: float, speed: float, damage: float, kind: str = "chaser"):
        super().__init__()
        self.kind = kind
        self.image = pygame.Surface((28, 28), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(int(pos.x), int(pos.y)))
        self.pos = Vector2(pos)
        self.max_hp = hp
        self.hp = hp
        self.speed = speed
        self.damage = damage
        self.phase = random.random() * 6.28
        self.style = random.choice(["feral", "cautious", "erratic"])

        if self.kind == "rusher":
            self._draw_shape((240, 120, 90), "triangle")
            self.speed *= 1.35
            self.hp *= 0.8
        elif self.kind == "tank":
            self._draw_shape((170, 80, 180), "hex")
            self.speed *= 0.75
            self.hp *= 1.55
            self.damage *= 1.15
        else:
            self._draw_shape((220, 78, 96), "circle")

    def _draw_shape(self, color: tuple[int, int, int], shape: str):
        self.image.fill((0, 0, 0, 0))
        if shape == "triangle":
            pygame.draw.polygon(self.image, color, [(14, 2), (26, 24), (2, 24)])
        elif shape == "hex":
            pygame.draw.polygon(self.image, color, [(14, 1), (24, 7), (24, 21), (14, 27), (4, 21), (4, 7)])
        else:
            pygame.draw.circle(self.image, color, (14, 14), 12)

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

        if self.style == "cautious":
            direction = (direction * 0.85 + Vector2(-direction.y, direction.x) * 0.15).normalize()
        elif self.style == "erratic":
            wob = Vector2(math.sin(self.phase * 1.7), math.cos(self.phase * 1.3)) * 0.25
            direction = (direction + wob).normalize()
        self.pos += direction * self.speed * dt
        self.rect.center = (int(self.pos.x), int(self.pos.y))
