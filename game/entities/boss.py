from pygame.math import Vector2
import pygame

from game.entities.bullet import Bullet
from game.entities.enemy import Enemy
from game.settings import PURPLE, ShotTrait


class BossOne(Enemy):
    """Boss nivel 3: patrón simple progresivo."""

    def __init__(self, pos: Vector2):
        super().__init__(pos, hp=260, speed=100, damage=18)
        self.base_image = pygame.Surface((40, 40), pygame.SRCALPHA)
        self.base_image.fill(PURPLE)
        self.image = self.base_image.copy()
        self.rect = self.image.get_rect(center=(int(pos.x), int(pos.y)))
        self.shot_cd = 1.2
        self.shot_timer = 0.0

    def update(self, dt: float, player_pos: Vector2, bullets, all_sprites):
        if self.hp < self.max_hp * 0.5:
            self.shot_cd = 0.7
            self.speed = 120
        super().update(dt, player_pos)
        self.shot_timer -= dt
        if self.shot_timer <= 0:
            self.shot_timer = self.shot_cd
            d = (player_pos - self.pos).normalize() if (player_pos - self.pos).length_squared() else Vector2(1, 0)
            b = Bullet(self.pos + d * 24, d, self.damage, 340, "enemy", color=PURPLE, life=1.8)
            bullets.add(b)
            all_sprites.add(b)


class BossTwo(Enemy):
    """Boss nivel 6: fases múltiples."""

    def __init__(self, pos: Vector2):
        super().__init__(pos, hp=420, speed=95, damage=20)
        self.base_image = pygame.Surface((44, 44), pygame.SRCALPHA)
        self.base_image.fill((200, 90, 180))
        self.image = self.base_image.copy()
        self.rect = self.image.get_rect(center=(int(pos.x), int(pos.y)))
        self.phase = 1
        self.shot_timer = 0.0

    def update(self, dt: float, player_pos: Vector2, bullets, all_sprites):
        ratio = self.hp / self.max_hp
        if ratio < 0.66 and self.phase == 1:
            self.phase = 2
            self.speed = 120
        if ratio < 0.33 and self.phase == 2:
            self.phase = 3
            self.speed = 140
        super().update(dt, player_pos)

        self.shot_timer -= dt
        if self.shot_timer <= 0:
            self.shot_timer = max(0.28, 1.1 - self.phase * 0.22)
            d = (player_pos - self.pos).normalize() if (player_pos - self.pos).length_squared() else Vector2(1, 0)
            spread = [0] if self.phase == 1 else [-12, 0, 12] if self.phase == 2 else [-18, -8, 0, 8, 18]
            for angle in spread:
                v = d.rotate(angle)
                b = Bullet(self.pos + v * 26, v, self.damage, 350 + self.phase * 20, "enemy", color=(215, 105, 200), life=1.8)
                bullets.add(b)
                all_sprites.add(b)


class ReflectBoss(Enemy):
    """Boss nivel 8: copia stats y rasgos del jugador."""

    def __init__(self, pos: Vector2, player):
        super().__init__(pos, hp=player.max_hp * 2.2, speed=max(100, player.speed * 0.85), damage=player.damage_value() * 0.8)
        self.base_image = pygame.Surface((46, 46), pygame.SRCALPHA)
        self.base_image.fill((145, 98, 220))
        self.image = self.base_image.copy()
        self.rect = self.image.get_rect(center=(int(pos.x), int(pos.y)))
        self.copied_traits = set(player.traits)
        self.shot_timer = 0.0

    def update(self, dt: float, player_pos: Vector2, bullets, all_sprites):
        super().update(dt, player_pos)
        self.shot_timer -= dt
        if self.shot_timer <= 0:
            self.shot_timer = 0.8
            d = (player_pos - self.pos).normalize() if (player_pos - self.pos).length_squared() else Vector2(1, 0)
            dirs = [d]
            if ShotTrait.TRIPLE in self.copied_traits:
                dirs = [d.rotate(-12), d, d.rotate(12)]
            for v in dirs:
                b = Bullet(
                    self.pos + v * 26,
                    v,
                    self.damage,
                    380,
                    "enemy",
                    color=(170, 90, 230),
                    life=1.8,
                    pierce=1 if ShotTrait.PIERCE in self.copied_traits else 0,
                    bounces=1 if ShotTrait.BOUNCE in self.copied_traits else 0,
                )
                bullets.add(b)
                all_sprites.add(b)
