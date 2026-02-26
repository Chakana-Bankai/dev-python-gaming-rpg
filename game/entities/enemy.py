import pygame
from pygame.math import Vector2


class Enemy(pygame.sprite.Sprite):
    def __init__(self, pos: Vector2, hp: float, speed: float, damage: float):
        super().__init__()
        self.image = pygame.Surface((24, 24), pygame.SRCALPHA)
        self.image.fill((220, 78, 96))
        self.rect = self.image.get_rect(center=(int(pos.x), int(pos.y)))
        self.pos = Vector2(pos)
        self.max_hp = hp
        self.hp = hp
        self.speed = speed
        self.damage = damage

    def take_damage(self, dmg: float):
        self.hp -= dmg
        if self.hp <= 0:
            self.kill()
            return True
        return False

    def update(self, dt: float, player_pos: Vector2):
        d = player_pos - self.pos
        if d.length_squared():
            self.pos += d.normalize() * self.speed * dt
        self.rect.center = (int(self.pos.x), int(self.pos.y))
