import pygame
from pygame.math import Vector2

from game.entities.enemy import Enemy


class SuperBoss(Enemy):
    """Arquitecto:
    - Invierte controles
    - Oscurece pantalla (manejado en UI)
    - Vulnerable solo cuando jugador NO dispara recientemente
    """

    def __init__(self, pos: Vector2):
        super().__init__(pos, hp=700, speed=150, damage=24)
        self.base_image = pygame.Surface((54, 54), pygame.SRCALPHA)
        self.base_image.fill((240, 240, 240))
        self.image = self.base_image.copy()
        self.rect = self.image.get_rect(center=(int(pos.x), int(pos.y)))

    def can_take_damage(self, player_fire_timer_value: float) -> bool:
        return player_fire_timer_value <= 0.0
