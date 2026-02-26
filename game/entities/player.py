import random

import pygame
from pygame.math import Vector2

from game.entities.bullet import Bullet
from game.settings import BLUE, HEIGHT, ShotTrait, WIDTH, YELLOW
from game.utils.timers import Cooldown


class Player(pygame.sprite.Sprite):
    def __init__(self, pos: Vector2):
        super().__init__()
        self.base_image = pygame.Surface((28, 28), pygame.SRCALPHA)
        self.base_image.fill(BLUE)
        self.image = self.base_image.copy()
        self.rect = self.image.get_rect(center=(int(pos.x), int(pos.y)))

        self.pos = Vector2(pos)
        self.vel = Vector2()
        self.knock = Vector2()

        self.max_hp = 120
        self.hp = 120
        self.speed = 220
        self.base_damage = 16

        self.level = 1
        self.exp = 0
        self.exp_next = 50
        self.upgrades_taken: list[str] = []

        self.traits: set[ShotTrait] = set()
        self.rare_items: set[str] = set()
        self.lifesteal_ratio = 0.0

        self.fire_cd = 0.16
        self.fire_timer = Cooldown(self.fire_cd)

        self.dash_speed = 650
        self.dash_duration = 0.12
        self.dash_cd = 1.0
        self.dash_timer = 0.0
        self.dash_cd_timer = Cooldown(self.dash_cd)
        self.dash_dir = Vector2(1, 0)

        self.invuln = Cooldown(0.75)
        self.blink = 0.0

        self.damage_taken_total = 0.0

    def move_input(self, keys):
        m = Vector2()
        if keys[pygame.K_w]:
            m.y -= 1
        if keys[pygame.K_s]:
            m.y += 1
        if keys[pygame.K_a]:
            m.x -= 1
        if keys[pygame.K_d]:
            m.x += 1
        self.vel = m.normalize() * self.speed if m.length_squared() > 0 else Vector2()
        if m.length_squared() > 0:
            self.dash_dir = m.normalize()

    def try_dash(self):
        if self.dash_cd_timer.ready:
            self.dash_timer = self.dash_duration
            self.dash_cd_timer.start(self.dash_cd)

    def gain_exp(self, value: int) -> bool:
        leveled = False
        self.exp += value
        while self.exp >= self.exp_next:
            self.exp -= self.exp_next
            self.level += 1
            self.exp_next = int(self.exp_next * 1.3)
            leveled = True
        return leveled

    def damage_value(self) -> float:
        dmg = self.base_damage
        if "Inner Edge" in self.rare_items:
            dmg *= 1.35
        return dmg

    def take_damage(self, dmg: float) -> bool:
        if not self.invuln.ready:
            return False
        self.hp -= dmg
        self.damage_taken_total += max(0.0, dmg)
        self.invuln.start(0.75)
        self.blink = 0.0
        return self.hp <= 0

    def heal(self, amount: float):
        self.hp = min(self.max_hp, self.hp + amount)

    def shoot(self, mouse_pos, bullet_group, all_sprites):
        if not self.fire_timer.ready:
            return
        direction = Vector2(mouse_pos) - self.pos
        if direction.length_squared() == 0:
            direction = Vector2(1, 0)
        dirs = [direction.normalize()]
        if ShotTrait.TRIPLE in self.traits:
            base = direction.normalize()
            dirs = [base.rotate(-14), base, base.rotate(14)]

        crit_enabled = ShotTrait.CRIT in self.traits
        for d in dirs:
            crit = crit_enabled and random.random() < (0.10 + (0.12 if "Threshold Eye" in self.rare_items else 0.0))
            bullet = Bullet(
                pos=self.pos + d * 18,
                direction=d,
                damage=self.damage_value(),
                speed=560,
                owner="player",
                color=YELLOW,
                life=1.1,
                pierce=1 if ShotTrait.PIERCE in self.traits else 0,
                bounces=(1 if ShotTrait.BOUNCE in self.traits else 0) + (1 if "Ash Mirror" in self.rare_items else 0),
                crit=crit,
            )
            bullet_group.add(bullet)
            all_sprites.add(bullet)

        self.fire_timer.start(self.fire_cd)

    def update(self, dt: float):
        self.fire_timer.update(dt)
        self.dash_cd_timer.update(dt)
        self.invuln.update(dt)

        if not self.invuln.ready:
            self.blink += dt
            if int(self.blink * 20) % 2 == 0:
                self.image = self.base_image.copy()
            else:
                self.image = pygame.Surface((28, 28), pygame.SRCALPHA)
                self.image.fill((130, 170, 255, 120))
        else:
            self.image = self.base_image.copy()

        v = self.vel
        if self.dash_timer > 0:
            self.dash_timer -= dt
            v = self.dash_dir * self.dash_speed

        self.pos += (v + self.knock) * dt
        self.knock *= max(0.0, 1 - 9 * dt)

        self.pos.x = max(14, min(WIDTH - 14, self.pos.x))
        self.pos.y = max(14, min(HEIGHT - 14, self.pos.y))
        self.rect.center = (int(self.pos.x), int(self.pos.y))
