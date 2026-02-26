import random

import pygame
from pygame.math import Vector2

from game.config import BLUE, HEIGHT, WIDTH, YELLOW


class Bullet(pygame.sprite.Sprite):
    def __init__(
        self,
        pos: Vector2,
        direction: Vector2,
        damage: float,
        owner: str,
        life: float = 1.1,
        pierce: int = 0,
        bounces: int = 0,
    ):
        super().__init__()
        self.image = pygame.Surface((8, 4), pygame.SRCALPHA)
        self.image.fill(YELLOW)
        self.rect = self.image.get_rect(center=(int(pos.x), int(pos.y)))
        self.pos = Vector2(pos)
        self.dir = direction.normalize() if direction.length_squared() else Vector2(1, 0)
        self.damage = damage
        self.owner = owner
        self.life = life
        self.pierce = pierce
        self.bounces = bounces

    def update(self, dt: float):
        self.life -= dt
        if self.life <= 0:
            self.kill()
            return
        self.pos += self.dir * 560 * dt

        # rebote básico en límites
        if self.pos.x <= 0 or self.pos.x >= WIDTH:
            if self.bounces > 0:
                self.bounces -= 1
                self.dir.x *= -1
            else:
                self.kill()
                return
        if self.pos.y <= 0 or self.pos.y >= HEIGHT:
            if self.bounces > 0:
                self.bounces -= 1
                self.dir.y *= -1
            else:
                self.kill()
                return

        self.rect.center = (int(self.pos.x), int(self.pos.y))
        if self.pos.x < -20 or self.pos.x > WIDTH + 20 or self.pos.y < -20 or self.pos.y > HEIGHT + 20:
            self.kill()


class Player(pygame.sprite.Sprite):
    def __init__(self, pos: Vector2):
        super().__init__()
        self.image = pygame.Surface((28, 28), pygame.SRCALPHA)
        self.image.fill(BLUE)
        self.rect = self.image.get_rect(center=(int(pos.x), int(pos.y)))
        self.pos = Vector2(pos)
        self.vel = Vector2()

        self.max_hp = 120
        self.hp = 120
        self.speed = 220
        self.damage = 16

        # progresión
        self.level = 1
        self.exp = 0
        self.exp_next = 45

        # rasgos secundarios / modular weapon
        self.triple_shot = False
        self.pierce = 0
        self.bounce = 0
        self.crit_bonus = 0.0
        self.lifesteal = 0.0

        self.fire_cd = 0.16
        self.fire_timer = 0.0
        self.shots_fired = 0

        # dash por shift
        self.dash_speed = 620
        self.dash_duration = 0.12
        self.dash_cd = 1.0
        self.dash_timer = 0.0
        self.dash_cd_timer = 0.0
        self.last_move_dir = Vector2(1, 0)

    def move_input(self, keys, invert=False):
        x = (1 if keys[pygame.K_d] else 0) - (1 if keys[pygame.K_a] else 0)
        y = (1 if keys[pygame.K_s] else 0) - (1 if keys[pygame.K_w] else 0)
        m = Vector2(x, y)
        if invert:
            m *= -1
        self.vel = m.normalize() * self.speed if m.length_squared() else Vector2()
        if m.length_squared() > 0:
            self.last_move_dir = m.normalize()

    def try_dash(self):
        if self.dash_cd_timer <= 0:
            self.dash_timer = self.dash_duration
            self.dash_cd_timer = self.dash_cd

    def gain_exp(self, amount: int) -> bool:
        self.exp += amount
        leveled = False
        while self.exp >= self.exp_next:
            self.exp -= self.exp_next
            self.level += 1
            self.exp_next = int(self.exp_next * 1.3)
            leveled = True
        return leveled

    def shoot(self, mouse_pos, bullet_group, all_sprites):
        if self.fire_timer > 0:
            return False
        d = Vector2(mouse_pos) - self.pos
        if d.length_squared() == 0:
            d = Vector2(1, 0)

        dirs = [d.normalize()]
        if self.triple_shot:
            dirs = [d.normalize().rotate(-12), d.normalize(), d.normalize().rotate(12)]

        for direction in dirs:
            crit = random.random() < (0.1 + self.crit_bonus)
            b = Bullet(
                self.pos + direction * 18,
                direction,
                self.damage * (1.8 if crit else 1),
                "player",
                pierce=self.pierce,
                bounces=self.bounce,
            )
            bullet_group.add(b)
            all_sprites.add(b)

        self.fire_timer = self.fire_cd
        self.shots_fired += 1
        return True

    def update(self, dt: float):
        self.fire_timer = max(0, self.fire_timer - dt)
        self.dash_cd_timer = max(0, self.dash_cd_timer - dt)

        v = self.vel
        if self.dash_timer > 0:
            self.dash_timer -= dt
            v = self.last_move_dir * self.dash_speed

        self.pos += v * dt
        self.pos.x = max(14, min(WIDTH - 14, self.pos.x))
        self.pos.y = max(14, min(HEIGHT - 14, self.pos.y))
        self.rect.center = (int(self.pos.x), int(self.pos.y))
