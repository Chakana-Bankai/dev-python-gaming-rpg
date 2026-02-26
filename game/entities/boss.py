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
                kind = "duelist"  # rápido/agresivo
                speed *= 1.25
                damage *= 1.2
            elif player.dash_cd <= 0.7:
                kind = "colossus"  # enorme/lento
                hp *= 1.45
                speed *= 0.78
            elif player.triple_shot or player.pierce > 1:
                kind = "oracle"  # técnico
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
