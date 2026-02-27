import pygame
from pygame.math import Vector2

from game.settings import HEIGHT, WIDTH, YELLOW


class Bullet(pygame.sprite.Sprite):
    def __init__(
        self,
        pos: Vector2,
        direction: Vector2,
        damage: float,
        speed: float,
        owner: str,
        color=YELLOW,
        life=1.0,
        pierce=0,
        bounces=0,
        crit=False,
    ):
        super().__init__()
        self.image = pygame.Surface((8, 4), pygame.SRCALPHA)
        self.image.fill(color)
        self.rect = self.image.get_rect(center=(int(pos.x), int(pos.y)))

        self.pos = Vector2(pos)
        self.dir = direction.normalize() if direction.length_squared() > 0 else Vector2(1, 0)
        self.damage = damage * (1.8 if crit else 1.0)
        self.speed = speed
        self.owner = owner
        self.life = life
        self.pierce = pierce
        self.bounces = bounces

    def update(self, dt: float):
        self.life -= dt
        if self.life <= 0:
            self.kill()
            return

        self.pos += self.dir * self.speed * dt

        if self.pos.x <= 0 or self.pos.x >= WIDTH:
            if self.bounces > 0:
                self.dir.x *= -1
                self.bounces -= 1
            else:
                self.kill()
        if self.pos.y <= 0 or self.pos.y >= HEIGHT:
            if self.bounces > 0:
                self.dir.y *= -1
                self.bounces -= 1
            else:
                self.kill()

        if not self.alive():
            return

        if self.pos.x < -25 or self.pos.x > WIDTH + 25 or self.pos.y < -25 or self.pos.y > HEIGHT + 25:
            self.kill()
            return

        self.rect.center = (int(self.pos.x), int(self.pos.y))
