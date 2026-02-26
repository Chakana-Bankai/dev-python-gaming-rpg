import random
from dataclasses import dataclass

import pygame

from game.settings import CYAN, DoorType, GREEN, HEIGHT, PURPLE, RED, WIDTH


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
    def create_three_doors(self) -> list[Door]:
        choices = list(DoorType)
        random.shuffle(choices)
        selected = choices[:3]
        w, h = 90, 24
        rects = [
            pygame.Rect(WIDTH // 2 - w // 2, 0, w, h),
            pygame.Rect(0, HEIGHT // 2 - w // 2, h, w),
            pygame.Rect(WIDTH - h, HEIGHT // 2 - w // 2, h, w),
        ]
        return [Door(rects[i], selected[i]) for i in range(3)]

    def apply_effect(self, door_type, player, difficulty: int):
        msg = ""
        if door_type == DoorType.CONFLICT:
            difficulty += 2
            player.base_damage += 3
            msg = "Conflict: pain becomes power."
        elif door_type == DoorType.CONTEMPLATION:
            player.heal(28)
            player.fire_cd = max(0.08, player.fire_cd - 0.015)
            msg = "Contemplation: breath restores rhythm."
        elif door_type == DoorType.SHADOW:
            difficulty += 1
            player.base_damage += 5
            player.max_hp = max(70, player.max_hp - 6)
            player.hp = min(player.hp, player.max_hp)
            msg = "Shadow: strength demands sacrifice."
        elif door_type == DoorType.ASCENT:
            player.max_hp += 14
            player.heal(14)
            difficulty = max(1, difficulty - 1)
            msg = "Ascent: burden turns into clarity."
        return difficulty, msg
