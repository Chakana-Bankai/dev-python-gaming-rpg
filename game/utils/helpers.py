import random
from pygame.math import Vector2

from game.settings import HEIGHT, WIDTH


def random_pos_away(origin: Vector2, min_dist: float) -> Vector2:
    for _ in range(40):
        p = Vector2(random.randint(40, WIDTH - 40), random.randint(40, HEIGHT - 40))
        if p.distance_to(origin) > min_dist:
            return p
    return Vector2(random.randint(40, WIDTH - 40), random.randint(40, HEIGHT - 40))
