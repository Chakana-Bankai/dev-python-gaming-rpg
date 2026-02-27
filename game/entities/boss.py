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
        kind = "Overlord"

        if player is not None:
            if player.damage >= 28:
                kind = "Duelist"
                speed *= 1.25
                damage *= 1.2
            elif player.dash_cd <= 0.7:
                kind = "Colossus"
                hp *= 1.45
                speed *= 0.78
            elif "fan_shot" in player.weapon_modes or player.pierce > 1:
                kind = "Oracle"
                hp *= 1.15
                damage *= 1.15

        super().__init__(pos, hp=hp, speed=speed, damage=damage, kind="boss")
        self.kind = kind
        size = {"Duelist": 40, "Colossus": 62, "Oracle": 50, "Overlord": 46}[kind]
        color = {
            "Duelist": (196, 86, 220),
            "Colossus": (120, 80, 210),
            "Oracle": (92, 200, 220),
            "Overlord": (145, 95, 215),
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


class OmegaFragment(Enemy):
    def __init__(self, pos: Vector2, hp: float, speed: float, damage: float, frag_type: str):
        super().__init__(pos, hp=hp, speed=speed, damage=damage, kind="omega_frag")
        self.frag_type = frag_type
        size = 38 if frag_type == "Shadow" else 34
        col = (225, 70, 120) if frag_type == "Shadow" else (140, 220, 230)
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        self.image.fill(col)
        self.rect = self.image.get_rect(center=(int(pos.x), int(pos.y)))
        self.timer = 0.0

    def update(self, dt: float, player_pos: Vector2):
        self.timer += dt
        d = player_pos - self.pos
        if d.length_squared() == 0:
            return
        direction = d.normalize()
        if self.frag_type == "Shadow":
            # aggression amplified
            self.pos += direction * self.speed * 1.25 * dt
        else:
            # predictive-like wobble
            side = Vector2(-direction.y, direction.x) * (0.35 + 0.15 * abs(math.sin(self.timer * 3)))
            move = (direction * 0.8 + side)
            if move.length_squared() > 0:
                move = move.normalize()
            self.pos += move * self.speed * dt
        self.rect.center = (int(self.pos.x), int(self.pos.y))


class OmegaBoss(Enemy):
    """Omega final boss con 3 fases: Reflection -> Inversion -> Dual Manifestation."""

    def __init__(self, pos: Vector2, difficulty: int):
        super().__init__(pos, hp=1100 + difficulty * 140, speed=120 + difficulty * 6, damage=28 + difficulty * 1.4, kind="omega")
        self.image = pygame.Surface((76, 76), pygame.SRCALPHA)
        self.image.fill((235, 88, 140))
        self.rect = self.image.get_rect(center=(int(pos.x), int(pos.y)))
        self.phase = 1
        self.timer = 0.0
        self.arena_shrink = 0.0
        self._mimic_fire_cd = 0.16
        self._split_done = False

    def update(self, dt: float, player_pos: Vector2, player, action_buffer: list[str]):
        self.timer += dt
        ratio = self.hp / self.max_hp if self.max_hp else 0

        if ratio < 0.66 and self.phase == 1:
            self.phase = 2
        if ratio < 0.33 and self.phase == 2:
            self.phase = 3

        d = player_pos - self.pos
        direction = d.normalize() if d.length_squared() > 0 else Vector2(1, 0)

        if self.phase == 1:
            # Reflection: mimic player build intensity
            boost = 1.0 + min(0.35, len(action_buffer) / 600)
            self.pos += direction * self.speed * boost * dt
        elif self.phase == 2:
            # Inversion: reverse logic + arena shrink
            inv = -direction
            orbit = Vector2(-inv.y, inv.x) * 0.4
            mv = (inv + orbit)
            if mv.length_squared() > 0:
                mv = mv.normalize()
            self.pos += mv * self.speed * 1.15 * dt
            self.arena_shrink = min(120.0, self.arena_shrink + 22 * dt)
        else:
            # Dual Manifestation body gets erratic while fragments take over
            zig = Vector2(math.sin(self.timer * 4.5), math.cos(self.timer * 3.2)) * 0.7
            mv = (direction * 0.6 + zig)
            if mv.length_squared() > 0:
                mv = mv.normalize()
            self.pos += mv * self.speed * 1.2 * dt

        self.rect.center = (int(self.pos.x), int(self.pos.y))

    def split_fragments(self):
        if self._split_done:
            return []
        self._split_done = True
        shadow = OmegaFragment(Vector2(self.pos.x - 70, self.pos.y), self.max_hp * 0.22, self.speed * 1.25, self.damage * 1.2, "Shadow")
        silence = OmegaFragment(Vector2(self.pos.x + 70, self.pos.y), self.max_hp * 0.25, self.speed * 0.85, self.damage * 0.9, "Silence")
        return [shadow, silence]
