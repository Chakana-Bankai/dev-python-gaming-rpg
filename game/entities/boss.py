import math

import pygame
from pygame.math import Vector2

from game.entities.enemy import Enemy


class Boss(Enemy):
    """Boss adaptativo según build del jugador (poder, movilidad, técnica)."""

    def __init__(self, pos: Vector2, level: int, player=None):
        hp = 220 + level * 55
        speed = 95 + level * 5
        damage = 20 + level
        kind = "overlord"

        if player is not None:
            if player.damage >= 28:
                kind = "duelist"
                speed *= 1.25
                damage *= 1.2
            elif player.dash_cd <= 0.7:
                kind = "colossus"
                hp *= 1.45
                speed *= 0.78
            elif "fan_shot" in player.weapon_modes or player.pierce > 1:
                kind = "oracle"
                hp *= 1.15
                damage *= 1.15

        super().__init__(pos, hp=hp, speed=speed, damage=damage, kind="boss")
        self.kind = kind
        size = {"duelist": 40, "colossus": 62, "oracle": 50, "overlord": 46}[kind]
        color = {
            "duelist": (196, 86, 220),
            "colossus": (120, 80, 210),
            "oracle": (92, 200, 220),
            "overlord": (145, 95, 215),
        }[kind]
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        self.image.fill(color)
        self.rect = self.image.get_rect(center=(int(pos.x), int(pos.y)))
        self.phase = 1

    def update(self, dt: float, player_pos: Vector2):
        ratio = self.hp / self.max_hp if self.max_hp else 0
        if ratio < 0.66 and self.phase == 1:
            self.phase = 2
            self.speed *= 1.18
            self.damage *= 1.12
        if ratio < 0.33 and self.phase == 2:
            self.phase = 3
            self.speed *= 1.2
            self.damage *= 1.16
        super().update(dt, player_pos)


class OmegaBoss(Enemy):
    """Super omega duper final boss: más agresivo, varias fases y movimiento errático."""

    def __init__(self, pos: Vector2, difficulty: int):
        super().__init__(pos, hp=1100 + difficulty * 140, speed=120 + difficulty * 6, damage=28 + difficulty * 1.4, kind="omega")
        self.image = pygame.Surface((76, 76), pygame.SRCALPHA)
        self.image.fill((235, 88, 140))
        self.rect = self.image.get_rect(center=(int(pos.x), int(pos.y)))
        self.phase = 1
        self.timer = 0.0

    def update(self, dt: float, player_pos: Vector2):
        self.timer += dt
        ratio = self.hp / self.max_hp if self.max_hp else 0
        if ratio < 0.75 and self.phase == 1:
            self.phase = 2
            self.speed *= 1.12
            self.damage *= 1.08
        if ratio < 0.50 and self.phase == 2:
            self.phase = 3
            self.speed *= 1.18
            self.damage *= 1.12
        if ratio < 0.25 and self.phase == 3:
            self.phase = 4
            self.speed *= 1.22
            self.damage *= 1.16

        d = player_pos - self.pos
        if d.length_squared() > 0:
            direction = d.normalize()
        else:
            direction = Vector2(1, 0)

        # Movimiento “hiper final”: orbit + zigzag + persecución
        orbit = Vector2(-direction.y, direction.x) * (0.55 + 0.08 * self.phase)
        zig = Vector2(math.sin(self.timer * (3 + self.phase)), math.cos(self.timer * (2 + self.phase))) * 0.35
        move = (direction + orbit + zig)
        if move.length_squared() > 0:
            move = move.normalize()
        self.pos += move * self.speed * dt
        self.rect.center = (int(self.pos.x), int(self.pos.y))
