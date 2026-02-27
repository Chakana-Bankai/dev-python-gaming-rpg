import random
import pygame
from pygame.math import Vector2

from game.settings import ORANGE, YELLOW


class RareItem(pygame.sprite.Sprite):
    def __init__(self, name: str, desc: str, pos: Vector2):
        super().__init__()
        self.name = name
        self.desc = desc
        self.image = pygame.Surface((20, 20), pygame.SRCALPHA)
        self.image.fill(ORANGE)
        pygame.draw.rect(self.image, YELLOW, (2, 2, 16, 16), 2)
        self.rect = self.image.get_rect(center=(int(pos.x), int(pos.y)))


class ItemSystem:
    RARE_POOL = [
        ("Ash Mirror", "+1 bounce and +10% speed"),
        ("Inner Edge", "+35% base damage"),
        ("Void Pulse", "+40 max HP and full heal"),
        ("Threshold Eye", "+12% critical chance"),
        ("Calm Blood", "+8% lifesteal"),
    ]

    def spawn_shadow_item(self, center: Vector2):
        name, desc = random.choice(self.RARE_POOL)
        return RareItem(name, desc, center)

    def apply_item(self, player, item: RareItem) -> str:
        if item.name in player.rare_items:
            return ""
        player.rare_items.add(item.name)
        if item.name == "Ash Mirror":
            player.speed *= 1.1
        elif item.name == "Void Pulse":
            player.max_hp += 40
            player.hp = player.max_hp
        elif item.name == "Calm Blood":
            player.lifesteal_ratio += 0.08
        return f"Relic found: {item.name}."
