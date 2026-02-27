from __future__ import annotations

import random
from dataclasses import dataclass

import pygame
from pygame.math import Vector2


@dataclass
class Particle:
    pos: Vector2
    vel: Vector2
    life: float
    color: tuple[int, int, int]


class ParticleSystem:
    def __init__(self):
        self.particles: list[Particle] = []

    def spawn_impact(self, pos: Vector2, color=(240, 196, 83), amount: int = 6):
        for _ in range(amount):
            self.particles.append(
                Particle(
                    pos=Vector2(pos),
                    vel=Vector2(random.uniform(-70, 70), random.uniform(-70, 70)),
                    life=random.uniform(0.2, 0.45),
                    color=color,
                )
            )

    def update(self, dt: float):
        alive = []
        for p in self.particles:
            p.life -= dt
            if p.life <= 0:
                continue
            p.pos += p.vel * dt
            p.vel *= 0.9
            alive.append(p)
        self.particles = alive

    def draw(self, screen):
        for p in self.particles:
            pygame.draw.circle(screen, p.color, (int(p.pos.x), int(p.pos.y)), 2)
