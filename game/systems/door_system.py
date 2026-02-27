import random
from dataclasses import dataclass
from enum import Enum

import pygame

from game.config import CYAN, GREEN, HEIGHT, PURPLE, RED, WIDTH


class DoorType(Enum):
    CONFLICT = "[⚔] Conflict"
    CONTEMPLATION = "[☾] Contemplation"
    SHADOW = "[∆] Shadow"
    ASCENT = "[✦] Ascent"
    SACRED = "[✞] Sacred"


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
            DoorType.SACRED: (250, 236, 165),
        }[self.type]


class DoorSystem:
    def create_doors(self, sacred_unlocked: bool = False):
        pool = list(DoorType)
        pool.remove(DoorType.SACRED)
        random.shuffle(pool)
        # Puertas dentro de la arena jugable: visibles y alcanzables sin tocar bordes del mapa.
        w, h = 120, 26
        top_y = 90
        center_y = HEIGHT // 2
        side_x = 126
        rects = [
            pygame.Rect(WIDTH // 2 - w // 2, top_y, w, h),
            pygame.Rect(side_x, center_y - w // 2, h, w),
            pygame.Rect(WIDTH - side_x - h, center_y - w // 2, h, w),
        ]
        doors = [Door(rects[i], pool[i]) for i in range(3)]
        if sacred_unlocked:
            doors.append(Door(pygame.Rect(WIDTH // 2 - w // 2, HEIGHT - top_y - h, w, h), DoorType.SACRED))
        return doors

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
            return "∆ Sombra asumida: lo que niegas ahora aprende tu forma."
        if door_type == DoorType.SACRED:
            gm.difficulty += 3
            gm.player.max_hp += 30
            gm.player.hp = min(gm.player.max_hp, gm.player.hp + 30)
            gm.base_player_damage += 5
            gm.player.weapon_modes.add("prism")
            return "✞ Umbral Sagrado: el Ángel juzga y te bendice con poder brutal."
        gm.difficulty = max(1, gm.difficulty - 1)
        gm.player.max_hp += 8
        gm.player.hp = min(gm.player.max_hp, gm.player.hp + 8)
        return "✦ Ascenso: dejas peso atrás y avanzas más liviano."
