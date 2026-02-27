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
        color: tuple[int, int, int] = YELLOW,
        shape: str = "bar",
    ):
        super().__init__()
        w, h = (8, 4) if shape == "bar" else (7, 7) if shape == "orb" else (10, 10)
        self.image = pygame.Surface((w, h), pygame.SRCALPHA)
        if shape == "orb":
            pygame.draw.circle(self.image, color, (w // 2, h // 2), min(w, h) // 2)
        elif shape == "diamond":
            pygame.draw.polygon(self.image, color, [(w // 2, 0), (w - 1, h // 2), (w // 2, h - 1), (0, h // 2)])
        else:
            self.image.fill(color)

        self.rect = self.image.get_rect(center=(int(pos.x), int(pos.y)))
        self.pos = Vector2(pos)
        self.dir = direction.normalize() if direction.length_squared() else Vector2(1, 0)
        self.damage = damage
        self.owner = owner
        self.life = life
        self.pierce = pierce
        self.bounces = bounces
        self.speed = 560
        self.prev_pos = Vector2(self.pos)

    def update(self, dt: float):
        self.life -= dt
        if self.life <= 0:
            self.kill()
            return
        self.prev_pos = Vector2(self.pos)
        self.speed = max(260, min(680, self.speed + (560 - self.speed) * dt * 2.0))
        self.pos += self.dir * self.speed * dt

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

        self.level = 1
        self.exp = 0
        self.exp_next = 45

        self.weapon_modes: set[str] = set()
        self.pierce = 0
        self.bounce = 0
        self.crit_bonus = 0.0
        self.lifesteal = 0.0

        self.fire_cd = 0.16
        self.fire_timer = 0.0
        self.shots_fired = 0
        self._shot_phase = 0

        self.secondary_cd = 2.0
        self.secondary_timer = 0.0

        self.dash_speed = 620
        self.dash_duration = 0.12
        self.dash_cd = 1.0
        self.dash_timer = 0.0
        self.dash_cd_timer = 0.0
        self.last_move_dir = Vector2(1, 0)
        self.prev_pos = Vector2(self.pos)

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

    def _build_dirs(self, base: Vector2) -> list[Vector2]:
        dirs = [base]
        if "triple" in self.weapon_modes:
            dirs += [base.rotate(-12), base.rotate(12)]
        if "fan_shot" in self.weapon_modes:
            dirs += [base.rotate(-24), base.rotate(24)]
        if "cross_shot" in self.weapon_modes:
            dirs += [base.rotate(90), base.rotate(-90)]
        if "backfire" in self.weapon_modes:
            dirs.append(base.rotate(180))
        if "chaos" in self.weapon_modes:
            dirs += [base.rotate(random.uniform(-40, 40)) for _ in range(2)]
        if "spiral" in self.weapon_modes:
            self._shot_phase = (self._shot_phase + 18) % 360
            dirs += [base.rotate(self._shot_phase), base.rotate(-self._shot_phase)]
        if "sigil" in self.weapon_modes:
            dirs += [base.rotate(a) for a in (45, 135, -45, -135)]
        if "lattice" in self.weapon_modes:
            dirs += [base.rotate(a) for a in (-60, -30, 30, 60)]
        if "prism" in self.weapon_modes:
            dirs += [base.rotate(a) for a in (-75, -45, -15, 15, 45, 75)]
        if "helix" in self.weapon_modes:
            self._shot_phase = (self._shot_phase + 28) % 360
            dirs += [base.rotate(self._shot_phase * 0.5), base.rotate(-self._shot_phase * 0.5)]
        out = []
        for d in dirs:
            if d.length_squared() > 0:
                out.append(d.normalize())
        return out

    def _bullet_style(self):
        if "helix" in self.weapon_modes:
            return (120, 210, 255), "orb"
        if "prism" in self.weapon_modes:
            return (240, 160, 255), "diamond"
        if "sigil" in self.weapon_modes:
            return (255, 210, 120), "diamond"
        if "chaos" in self.weapon_modes:
            return random.choice([(255, 180, 100), (120, 255, 200), (255, 120, 210)]), "bar"
        return YELLOW, "bar"

    def shoot(self, mouse_pos, bullet_group, all_sprites):
        if self.fire_timer > 0:
            return False
        d = Vector2(mouse_pos) - self.pos
        if d.length_squared() == 0:
            d = Vector2(1, 0)
        base = d.normalize()

        dirs = self._build_dirs(base)
        mult = 1.0
        if "heavy_rounds" in self.weapon_modes:
            mult *= 1.35
        if "sniper" in self.weapon_modes:
            mult *= 1.45

        color, shape = self._bullet_style()
        for direction in dirs:
            crit = random.random() < (0.1 + self.crit_bonus + (0.08 if "storm_crit" in self.weapon_modes else 0.0))
            b = Bullet(
                self.pos + direction * 18,
                direction,
                self.damage * mult * (1.8 if crit else 1),
                "player",
                pierce=self.pierce + (1 if "pierce_plus" in self.weapon_modes else 0),
                bounces=self.bounce + (1 if "ricochet_plus" in self.weapon_modes else 0),
                life=1.35 if "long_life" in self.weapon_modes else 1.1,
                color=color,
                shape=shape,
            )
            bullet_group.add(b)
            all_sprites.add(b)

        if "rapid_fire" in self.weapon_modes:
            self.fire_timer = max(0.06, self.fire_cd * 0.75)
        else:
            self.fire_timer = self.fire_cd
        self.shots_fired += 1
        return True

    def cast_secondary(self, bullet_group, all_sprites):
        if self.secondary_timer > 0:
            return False
        count = 12 if "nova_plus" in self.weapon_modes else 9
        for i in range(count):
            direction = Vector2(1, 0).rotate(i * (360 / count))
            b = Bullet(
                self.pos + direction * 16,
                direction,
                self.damage * (0.82 if "nova_plus" in self.weapon_modes else 0.72),
                "player",
                life=1.05,
                pierce=max(0, self.pierce - 1),
                bounces=self.bounce,
                color=(130, 220, 255),
                shape="orb",
            )
            bullet_group.add(b)
            all_sprites.add(b)
        self.secondary_timer = self.secondary_cd
        return True

    def update(self, dt: float):
        self.fire_timer = max(0, self.fire_timer - dt)
        self.secondary_timer = max(0, self.secondary_timer - dt)
        self.dash_cd_timer = max(0, self.dash_cd_timer - dt)

        v = self.vel
        if self.dash_timer > 0:
            self.dash_timer -= dt
            v = self.last_move_dir * self.dash_speed

        self.prev_pos = Vector2(self.pos)
        self.pos += v * dt
        self.pos.x = max(14, min(WIDTH - 14, self.pos.x))
        self.pos.y = max(14, min(HEIGHT - 14, self.pos.y))
        self.rect.center = (int(self.pos.x), int(self.pos.y))
