import pygame
from pygame.math import Vector2

from game.settings import RED


class Enemy(pygame.sprite.Sprite):
    def __init__(self, pos: Vector2, hp: float, speed: float, damage: float):
        super().__init__()
        self.base_image = pygame.Surface((26, 26), pygame.SRCALPHA)
        self.base_image.fill(RED)
        self.image = self.base_image.copy()
        self.rect = self.image.get_rect(center=(int(pos.x), int(pos.y)))

        self.pos = Vector2(pos)
        self.vel = Vector2()
        self.knock = Vector2()
        self.max_hp = hp
        self.hp = hp
        self.speed = speed
        self.damage = damage

    def take_damage(self, amount: float) -> bool:
        self.hp -= amount
        if self.hp <= 0:
            self.kill()
            return True
        return False

    def apply_knock(self, direction: Vector2, force: float):
        if direction.length_squared() > 0:
            self.knock += direction.normalize() * force

    def update(self, dt: float, player_pos: Vector2):
        d = player_pos - self.pos
        self.vel = d.normalize() * self.speed if d.length_squared() > 0 else Vector2()
        self.pos += (self.vel + self.knock) * dt
        self.knock *= max(0.0, 1 - 8 * dt)
        self.rect.center = (int(self.pos.x), int(self.pos.y))
