import random
from dataclasses import dataclass
from enum import Enum

import pygame

from game.config import CYAN, GREEN, HEIGHT, PURPLE, RED, WIDTH


class DoorType(Enum):
    CONFLICT = "⚔ Conflict"
    CONTEMPLATION = "☾ Contemplation"
    SHADOW = "🜏 Shadow"
    ASCENT = "✦ Ascent"


@dataclass
class Door:
    rect: pygame.Rect
    type: DoorType

    @property
    def color(self):
        return {
            DoorType.CONFLICT: RED,
            DoorType.CONTEMPLATION: CYAN,
            DoorType.SHADOW: PURPLE,
            DoorType.ASCENT: GREEN,
        }[self.type]


class DoorSystem:
    def create_doors(self):
        pool = list(DoorType)
        random.shuffle(pool)
        w, h = 110, 24
        rects = [
            pygame.Rect(WIDTH // 2 - w // 2, 0, w, h),
            pygame.Rect(0, HEIGHT // 2 - w // 2, h, w),
            pygame.Rect(WIDTH - h, HEIGHT // 2 - w // 2, h, w),
        ]
        return [Door(rects[i], pool[i]) for i in range(3)]

    def apply(self, door_type: DoorType, gm):
        if door_type == DoorType.CONFLICT:
            gm.difficulty += 2
            gm.player.damage += 2
            return "⚔ Sangre y eco: eliges conflicto, el dungeon responde con furia."
        if door_type == DoorType.CONTEMPLATION:
            gm.player.hp = min(gm.player.max_hp, gm.player.hp + 25)
            gm.player.fire_cd = max(0.08, gm.player.fire_cd * 0.94)
            return "☾ Silencio interior: respiras, y el tiempo entre disparos se acorta."
        if door_type == DoorType.SHADOW:
            gm.difficulty += 1
            gm.spawn_reflection_next = True
            return "🜏 Sombra asumida: lo que niegas ahora aprende tu forma."
        gm.difficulty = max(1, gm.difficulty - 1)
        gm.player.max_hp += 8
        gm.player.hp = min(gm.player.max_hp, gm.player.hp + 8)
        return "✦ Ascenso: dejas peso atrás y avanzas más liviano."
