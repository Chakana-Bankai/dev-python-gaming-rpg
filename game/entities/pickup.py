from __future__ import annotations

import random

import pygame
from pygame.math import Vector2


class RelicPickup(pygame.sprite.Sprite):
    """Objeto raro simple para enriquecer la run sin assets externos."""

    RELICS = [
        ("Blood Prism", (245, 94, 112), "diamond"),
        ("Moon Shell", (126, 220, 244), "circle"),
        ("Kinetic Core", (242, 184, 84), "hex"),
        ("Ricochet Idol", (164, 126, 242), "diamond"),
        ("Void Bloom", (126, 244, 196), "circle"),
    ]

    def __init__(self, pos: Vector2):
        super().__init__()
        self.name, self.color, shape = random.choice(self.RELICS)
        self.image = pygame.Surface((24, 24), pygame.SRCALPHA)
        if shape == "circle":
            pygame.draw.circle(self.image, self.color, (12, 12), 9)
        elif shape == "hex":
            pygame.draw.polygon(self.image, self.color, [(12, 2), (20, 7), (20, 17), (12, 22), (4, 17), (4, 7)])
        else:
            pygame.draw.polygon(self.image, self.color, [(12, 2), (22, 12), (12, 22), (2, 12)])
        self.rect = self.image.get_rect(center=(int(pos.x), int(pos.y)))
        self.pos = Vector2(pos)

    def apply(self, gm):
        p = gm.player
        if self.name == "Blood Prism":
            gm.base_player_damage += 2.0
            p.crit_bonus += 0.06
            return "+Daño base + crítico"
        if self.name == "Moon Shell":
            p.max_hp += 18
            p.hp = min(p.max_hp, p.hp + 28)
            return "+vida máxima + cura"
        if self.name == "Kinetic Core":
            gm.base_player_speed += 12
            p.dash_cd = max(0.45, p.dash_cd - 0.1)
            return "+movilidad + dash"
        if self.name == "Ricochet Idol":
            p.bounce += 1
            gm.base_player_pierce += 1
            return "+rebote + perforación"
        p.secondary_cd = max(5.5, p.secondary_cd - 0.8)
        p.weapon_modes.add("nova_plus")
        return "secundario más fuerte"
