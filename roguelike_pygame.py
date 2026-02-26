import math
import random
from dataclasses import dataclass
from enum import Enum, auto

import pygame
from pygame.math import Vector2

# =========================================================
# Config global
# =========================================================
WIDTH, HEIGHT = 960, 540
FPS = 60

BG = (14, 16, 22)
GRID = (24, 28, 38)
WHITE = (230, 233, 240)
RED = (220, 78, 96)
GREEN = (72, 196, 114)
BLUE = (92, 130, 230)
YELLOW = (240, 196, 83)
PURPLE = (160, 110, 220)
CYAN = (80, 210, 220)
ORANGE = (237, 153, 74)


class GameState(Enum):
    MENU = auto()
    PLAYING = auto()
    LEVEL_UP = auto()
    GAME_OVER = auto()


class DoorType(Enum):
    CONFLICTO = "Conflicto"
    CONTEMPLACION = "Contemplacion"
    SOMBRA = "Sombra"
    ASCENSO = "Ascenso"


class ShotTrait(Enum):
    TRIPLE = "Disparo triple"
    PIERCE = "Perforante"
    BOUNCE = "Rebote"
    CRIT = "Critico"
    LIFESTEAL = "Drenaje"


@dataclass
class RoomMeta:
    number: int
    is_boss: bool = False
    is_special: bool = False
    cleared: bool = False


class Bullet(pygame.sprite.Sprite):
    """Proyectil modular:
    - Soporta perforación (pierce)
    - Rebote limitado (bounces)
    - Crítico precalculado por bala
    - Drenaje aplicado por atacante al impactar
    """

    def __init__(self, pos: Vector2, direction: Vector2, damage: float, speed: float, owner: str, color=YELLOW,
                 life=1.0, pierce=0, bounces=0, crit=False):
        super().__init__()
        self.image = pygame.Surface((8, 4), pygame.SRCALPHA)
        self.image.fill(color)
        self.rect = self.image.get_rect(center=(int(pos.x), int(pos.y)))

        self.pos = Vector2(pos)
        self.dir = direction.normalize() if direction.length_squared() > 0 else Vector2(1, 0)
        self.damage = damage * (1.8 if crit else 1.0)
        self.speed = speed
        self.owner = owner
        self.life = life
        self.pierce = pierce
        self.bounces = bounces

    def update(self, dt: float):
        self.life -= dt
        if self.life <= 0:
            self.kill()
            return

        self.pos += self.dir * self.speed * dt

        # Rebote en límites de pantalla
        bounced = False
        if self.pos.x <= 0 or self.pos.x >= WIDTH:
            if self.bounces > 0:
                self.dir.x *= -1
                self.bounces -= 1
                bounced = True
            else:
                self.kill()
        if self.pos.y <= 0 or self.pos.y >= HEIGHT:
            if self.bounces > 0:
                self.dir.y *= -1
                self.bounces -= 1
                bounced = True
            else:
                self.kill()

        if not self.alive():
            return

        if not bounced and (
            self.pos.x < -25 or self.pos.x > WIDTH + 25 or self.pos.y < -25 or self.pos.y > HEIGHT + 25
        ):
            self.kill()
            return

        self.rect.center = (int(self.pos.x), int(self.pos.y))


class Entity(pygame.sprite.Sprite):
    def __init__(self, size: int, color, pos: Vector2):
        super().__init__()
        self.base_image = pygame.Surface((size, size), pygame.SRCALPHA)
        self.base_image.fill(color)
        self.image = self.base_image.copy()
        self.rect = self.image.get_rect(center=(int(pos.x), int(pos.y)))
        self.pos = Vector2(pos)
        self.vel = Vector2()
        self.knock = Vector2()

        self.max_hp = 100.0
        self.hp = 100.0
        self.speed = 120.0

    def take_damage(self, dmg: float) -> bool:
        self.hp -= dmg
        if self.hp <= 0:
            self.kill()
            return True
        return False

    def apply_knock(self, direction: Vector2, force: float):
        if direction.length_squared() > 0:
            self.knock += direction.normalize() * force


class Player(Entity):
    def __init__(self, pos: Vector2):
        super().__init__(28, BLUE, pos)
        self.max_hp = 120
        self.hp = 120
        self.speed = 220
        self.base_damage = 16

        self.fire_cd = 0.16
        self.fire_timer = 0.0

        self.dash_speed = 650
        self.dash_duration = 0.12
        self.dash_cd = 1.0
        self.dash_timer = 0.0
        self.dash_cd_timer = 0.0
        self.dash_dir = Vector2(1, 0)

        self.invuln = 0.0
        self.blink = 0.0

        self.level = 1
        self.exp = 0
        self.exp_next = 50

        self.traits: set[ShotTrait] = set()
        self.lifesteal_ratio = 0.0

        self.upgrades_taken: list[str] = []  # máximo 4 acumulables
        self.rare_items: set[str] = set()

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
        if self.dash_cd_timer <= 0 and self.dash_dir.length_squared() > 0:
            self.dash_timer = self.dash_duration
            self.dash_cd_timer = self.dash_cd

    def gain_exp(self, amount: int):
        self.exp += amount
        leveled = False
        while self.exp >= self.exp_next:
            self.exp -= self.exp_next
            self.level += 1
            self.exp_next = int(self.exp_next * 1.3)
            leveled = True
        return leveled

    def damage_value(self):
        dmg = self.base_damage
        if "Filo Interior" in self.rare_items:
            dmg *= 1.35
        return dmg

    def take_player_damage(self, dmg: float) -> bool:
        if self.invuln > 0:
            return False
        self.hp -= dmg
        self.invuln = 0.75
        self.blink = 0.0
        return self.hp <= 0

    def heal(self, amount: float):
        self.hp = min(self.max_hp, self.hp + amount)

    def update(self, dt: float):
        self.fire_timer = max(0.0, self.fire_timer - dt)
        self.dash_cd_timer = max(0.0, self.dash_cd_timer - dt)

        if self.invuln > 0:
            self.invuln = max(0.0, self.invuln - dt)
            self.blink += dt
            self.image = self.base_image.copy() if int(self.blink * 20) % 2 == 0 else pygame.Surface((28, 28), pygame.SRCALPHA)
            if self.image.get_width() == 28 and self.image.get_at((0, 0)).a == 0:
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


class Enemy(Entity):
    def __init__(self, pos: Vector2, hp: float, speed: float, damage: float):
        super().__init__(26, RED, pos)
        self.max_hp = hp
        self.hp = hp
        self.speed = speed
        self.damage = damage

    def update(self, dt: float, player_pos: Vector2):
        d = player_pos - self.pos
        self.vel = d.normalize() * self.speed if d.length_squared() > 0 else Vector2()
        self.pos += (self.vel + self.knock) * dt
        self.knock *= max(0.0, 1 - 8 * dt)
        self.rect.center = (int(self.pos.x), int(self.pos.y))


class Boss(Enemy):
    """Boss espejo simbólico: copia stats + estilo de disparo del jugador."""

    def __init__(self, pos: Vector2, player: Player):
        hp = player.max_hp * 2.2
        speed = max(100.0, player.speed * 0.85)
        damage = player.damage_value() * 0.75
        super().__init__(pos, hp=hp, speed=speed, damage=damage)
        self.base_image = pygame.Surface((40, 40), pygame.SRCALPHA)
        self.base_image.fill(PURPLE)
        self.image = self.base_image.copy()
        self.rect = self.image.get_rect(center=(int(pos.x), int(pos.y)))

        self.copied_traits = set(player.traits)
        self.phase = 1
        self.shot_cd = 1.0
        self.shot_timer = 0.0
        self.contact_scale = 1.0

    def update(self, dt: float, player_pos: Vector2, enemy_bullets: pygame.sprite.Group, all_sprites: pygame.sprite.Group):
        hp_ratio = self.hp / self.max_hp
        if hp_ratio < 0.35 and self.phase == 1:
            self.phase = 2
            self.speed *= 1.25
            self.shot_cd *= 0.7
            self.contact_scale = 1.25

        super().update(dt, player_pos)

        self.shot_timer -= dt
        if self.shot_timer <= 0:
            self.shot_timer = self.shot_cd
            direction = (player_pos - self.pos)
            if direction.length_squared() == 0:
                direction = Vector2(1, 0)
            dirs = [direction.normalize()]
            if ShotTrait.TRIPLE in self.copied_traits:
                base = direction.normalize()
                dirs = [base.rotate(-14), base, base.rotate(14)]
            for d in dirs:
                b = Bullet(self.pos + d * 24, d, self.damage, 360, owner="enemy", color=PURPLE,
                           life=1.6, pierce=1 if ShotTrait.PIERCE in self.copied_traits else 0,
                           bounces=1 if ShotTrait.BOUNCE in self.copied_traits else 0)
                enemy_bullets.add(b)
                all_sprites.add(b)


class Door(pygame.sprite.Sprite):
    def __init__(self, rect: pygame.Rect, door_type: DoorType):
        super().__init__()
        self.rect = rect
        self.type = door_type

    @property
    def color(self):
        return {
            DoorType.CONFLICTO: RED,
            DoorType.CONTEMPLACION: CYAN,
            DoorType.SOMBRA: PURPLE,
            DoorType.ASCENSO: GREEN,
        }[self.type]


class RareItem(pygame.sprite.Sprite):
    def __init__(self, name: str, desc: str, pos: Vector2):
        super().__init__()
        self.name = name
        self.desc = desc
        self.image = pygame.Surface((20, 20), pygame.SRCALPHA)
        self.image.fill(ORANGE)
        pygame.draw.rect(self.image, YELLOW, (2, 2, 16, 16), 2)
        self.rect = self.image.get_rect(center=(int(pos.x), int(pos.y)))


class UpgradeOption:
    def __init__(self, key: str, label: str, apply_fn):
        self.key = key
        self.label = label
        self.apply_fn = apply_fn


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Roguelike Simbolico")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("consolas", 22)
        self.small = pygame.font.SysFont("consolas", 16)

        self.running = True
        self.state = GameState.MENU

        self.all_sprites = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.player_bullets = pygame.sprite.Group()
        self.enemy_bullets = pygame.sprite.Group()
        self.pickups = pygame.sprite.Group()

        self.player = Player(Vector2(WIDTH // 2, HEIGHT // 2))
        self.all_sprites.add(self.player)

        self.room = RoomMeta(number=1)
        self.difficulty = 1

        self.doors: list[Door] = []
        self.symbolic_message = ""
        self.message_timer = 0.0

        self.level_up_options: list[UpgradeOption] = []
        self.max_upgrades = 4

        self._spawn_room_content()

    # -------------------- reset / flow --------------------
    def clean_reset(self):
        self.all_sprites.empty()
        self.enemies.empty()
        self.player_bullets.empty()
        self.enemy_bullets.empty()
        self.pickups.empty()

        self.player = Player(Vector2(WIDTH // 2, HEIGHT // 2))
        self.all_sprites.add(self.player)

        self.room = RoomMeta(number=1)
        self.difficulty = 1
        self.doors.clear()
        self.symbolic_message = ""
        self.message_timer = 0.0
        self.state = GameState.PLAYING
        self._spawn_room_content()

    def _next_room_meta(self, room_number: int) -> RoomMeta:
        is_boss = room_number % 5 == 0
        is_special = (not is_boss) and random.random() < 0.22
        return RoomMeta(number=room_number, is_boss=is_boss, is_special=is_special)

    # -------------------- room generation --------------------
    def _spawn_room_content(self):
        # Limpieza de entidades de sala
        for s in list(self.enemies):
            s.kill()
        for s in list(self.player_bullets):
            s.kill()
        for s in list(self.enemy_bullets):
            s.kill()
        for s in list(self.pickups):
            s.kill()
        self.doors.clear()

        if self.room.is_special:
            self._spawn_special_pickup_room()
            self.room.cleared = True
            self._spawn_doors_after_clear()
            return

        if self.room.is_boss:
            boss = Boss(Vector2(WIDTH // 2, 140), self.player)
            self.enemies.add(boss)
            self.all_sprites.add(boss)
            return

        count = min(10, 2 + self.difficulty // 2 + random.randint(0, 2))
        for _ in range(count):
            pos = self._random_pos_away(self.player.pos, 130)
            hp = 18 + self.difficulty * 3.2
            spd = 90 + min(130, self.difficulty * 4)
            dmg = 10 + self.difficulty * 0.9
            e = Enemy(pos, hp=hp, speed=spd, damage=dmg)
            self.enemies.add(e)
            self.all_sprites.add(e)

    def _spawn_special_pickup_room(self):
        rare_pool = [
            ("Espejo de Ceniza", "+1 rebote y +10% velocidad"),
            ("Filo Interior", "+35% danio base"),
            ("Pulso Vacio", "+40 HP max y curacion total"),
            ("Ojo del Umbral", "+12% critico"),
            ("Sangre Serena", "+8% drenaje"),
        ]
        name, desc = random.choice(rare_pool)
        item = RareItem(name, desc, Vector2(WIDTH // 2, HEIGHT // 2))
        self.pickups.add(item)
        self.all_sprites.add(item)

    def _spawn_doors_after_clear(self):
        available = list(DoorType)
        random.shuffle(available)
        chosen = available[:3]
        door_w, door_h = 90, 24
        rects = [
            pygame.Rect(WIDTH // 2 - door_w // 2, 0, door_w, door_h),
            pygame.Rect(0, HEIGHT // 2 - door_w // 2, door_h, door_w),
            pygame.Rect(WIDTH - door_h, HEIGHT // 2 - door_w // 2, door_h, door_w),
        ]
        self.doors = [Door(rects[i], chosen[i]) for i in range(3)]

    def _random_pos_away(self, origin: Vector2, min_dist: float) -> Vector2:
        for _ in range(40):
            p = Vector2(random.randint(40, WIDTH - 40), random.randint(40, HEIGHT - 40))
            if p.distance_to(origin) > min_dist:
                return p
        return Vector2(random.randint(40, WIDTH - 40), random.randint(40, HEIGHT - 40))

    # -------------------- symbolic doors --------------------
    def _apply_door_effect(self, door_type: DoorType):
        if door_type == DoorType.CONFLICTO:
            self.difficulty += 2
            self.player.base_damage += 3
            self.symbolic_message = "Conflicto: abrazas el fuego y golpeas mas fuerte."
        elif door_type == DoorType.CONTEMPLACION:
            self.player.heal(28)
            self.player.fire_cd = max(0.08, self.player.fire_cd - 0.015)
            self.symbolic_message = "Contemplacion: respiras y tu pulso se estabiliza."
        elif door_type == DoorType.SOMBRA:
            self.difficulty += 1
            self.player.base_damage += 5
            self.player.max_hp = max(70, self.player.max_hp - 6)
            self.player.hp = min(self.player.hp, self.player.max_hp)
            self.symbolic_message = "Sombra: poder a cambio de fragilidad."
        elif door_type == DoorType.ASCENSO:
            self.player.max_hp += 14
            self.player.heal(14)
            self.difficulty = max(1, self.difficulty - 1)
            self.symbolic_message = "Ascenso: trasciendes y el peso se aligera."

        self.message_timer = 3.2

    # -------------------- upgrades --------------------
    def _build_upgrade_pool(self):
        p = self.player
        return [
            UpgradeOption("hp", "+20 HP max", lambda: setattr(p, "max_hp", p.max_hp + 20)),
            UpgradeOption("dmg", "+4 danio", lambda: setattr(p, "base_damage", p.base_damage + 4)),
            UpgradeOption("firerate", "-10% cooldown disparo", lambda: setattr(p, "fire_cd", max(0.07, p.fire_cd * 0.9))),
            UpgradeOption("speed", "+12% velocidad", lambda: setattr(p, "speed", p.speed * 1.12)),
            UpgradeOption("dash", "Dash mas frecuente", lambda: setattr(p, "dash_cd", max(0.45, p.dash_cd * 0.9))),
            UpgradeOption("triple", "Rasgo: triple", lambda: p.traits.add(ShotTrait.TRIPLE)),
            UpgradeOption("pierce", "Rasgo: perforante", lambda: p.traits.add(ShotTrait.PIERCE)),
            UpgradeOption("bounce", "Rasgo: rebote", lambda: p.traits.add(ShotTrait.BOUNCE)),
            UpgradeOption("crit", "Rasgo: critico", lambda: p.traits.add(ShotTrait.CRIT)),
            UpgradeOption("drain", "Rasgo: drenaje", lambda: (p.traits.add(ShotTrait.LIFESTEAL), setattr(p, "lifesteal_ratio", p.lifesteal_ratio + 0.05))),
        ]

    def _roll_level_up_options(self):
        pool = self._build_upgrade_pool()
        random.shuffle(pool)
        self.level_up_options = pool[:3]

    def _apply_upgrade(self, option: UpgradeOption):
        # Máximo 4 mejoras acumulables (metaprogresión de elecciones)
        if len(self.player.upgrades_taken) >= self.max_upgrades:
            self.player.heal(20)
            self.symbolic_message = "Limite de mejoras alcanzado: conviertes aprendizaje en calma."
            self.message_timer = 3.0
            self.state = GameState.PLAYING
            return

        option.apply_fn()
        self.player.upgrades_taken.append(option.label)
        # Ajustes de consistencia
        self.player.hp = min(self.player.hp, self.player.max_hp)
        self.state = GameState.PLAYING

    # -------------------- shooting --------------------
    def _player_shoot(self):
        if self.player.fire_timer > 0:
            return

        mouse = Vector2(pygame.mouse.get_pos())
        direction = mouse - self.player.pos
        if direction.length_squared() == 0:
            direction = Vector2(1, 0)

        dirs = [direction.normalize()]
        if ShotTrait.TRIPLE in self.player.traits:
            b = direction.normalize()
            dirs = [b.rotate(-14), b, b.rotate(14)]

        crit_enabled = ShotTrait.CRIT in self.player.traits

        for d in dirs:
            crit = crit_enabled and random.random() < (0.10 + (0.12 if "Ojo del Umbral" in self.player.rare_items else 0.0))
            b = Bullet(
                pos=self.player.pos + d * 18,
                direction=d,
                damage=self.player.damage_value(),
                speed=560,
                owner="player",
                color=YELLOW,
                life=1.1,
                pierce=1 if ShotTrait.PIERCE in self.player.traits else 0,
                bounces=1 + (1 if "Espejo de Ceniza" in self.player.rare_items else 0) if ShotTrait.BOUNCE in self.player.traits else 0,
                crit=crit,
            )
            self.player_bullets.add(b)
            self.all_sprites.add(b)

        self.player.fire_timer = self.player.fire_cd

    # -------------------- collisions / update --------------------
    def _apply_rare_item(self, item: RareItem):
        p = self.player
        if item.name in p.rare_items:
            return
        p.rare_items.add(item.name)

        if item.name == "Espejo de Ceniza":
            p.speed *= 1.1
        elif item.name == "Filo Interior":
            pass
        elif item.name == "Pulso Vacio":
            p.max_hp += 40
            p.hp = p.max_hp
        elif item.name == "Ojo del Umbral":
            pass
        elif item.name == "Sangre Serena":
            p.lifesteal_ratio += 0.08

        self.symbolic_message = f"Reliquia hallada: {item.name}."
        self.message_timer = 3.5

    def _handle_collisions(self, dt: float):
        # Player bullets -> enemies
        hits = pygame.sprite.groupcollide(self.enemies, self.player_bullets, False, False)
        for enemy, bullets in hits.items():
            for b in bullets:
                dead = enemy.take_damage(b.damage)
                enemy.apply_knock(b.dir, 120)

                # bala se destruye si no perfora
                if b.pierce > 0:
                    b.pierce -= 1
                else:
                    b.kill()

                # drenaje
                if ShotTrait.LIFESTEAL in self.player.traits or self.player.lifesteal_ratio > 0:
                    self.player.heal(b.damage * self.player.lifesteal_ratio * 0.22)

                if dead:
                    gained = 20 if isinstance(enemy, Boss) else 10 + self.difficulty
                    leveled = self.player.gain_exp(gained)
                    if leveled:
                        self._roll_level_up_options()
                        self.state = GameState.LEVEL_UP

        # Enemy bullets -> player
        for b in pygame.sprite.spritecollide(self.player, self.enemy_bullets, False):
            if self.player.take_player_damage(b.damage):
                self.state = GameState.GAME_OVER
            b.kill()

        # Enemy touch -> player
        for e in pygame.sprite.spritecollide(self.player, self.enemies, False):
            scale = e.contact_scale if isinstance(e, Boss) else 1.0
            if self.player.take_player_damage(e.damage * dt * 4.3 * scale):
                self.state = GameState.GAME_OVER
            push = self.player.pos - e.pos
            e.apply_knock(-push if push.length_squared() > 0 else Vector2(1, 0), 45)

        # Pickups
        for item in pygame.sprite.spritecollide(self.player, self.pickups, True):
            self._apply_rare_item(item)

    def _update_playing(self, dt: float):
        keys = pygame.key.get_pressed()
        self.player.move_input(keys)
        self.player.update(dt)

        for e in list(self.enemies):
            if isinstance(e, Boss):
                e.update(dt, self.player.pos, self.enemy_bullets, self.all_sprites)
            else:
                e.update(dt, self.player.pos)

        self.player_bullets.update(dt)
        self.enemy_bullets.update(dt)

        self._handle_collisions(dt)

        if self.message_timer > 0:
            self.message_timer -= dt

        if len(self.enemies) == 0 and not self.room.cleared:
            self.room.cleared = True
            self._spawn_doors_after_clear()

        if self.room.cleared:
            for d in self.doors:
                if self.player.rect.colliderect(d.rect):
                    self._apply_door_effect(d.type)
                    self.room = self._next_room_meta(self.room.number + 1)
                    self._spawn_room_content()
                    break

    # -------------------- render --------------------
    def _draw_grid(self):
        for x in range(0, WIDTH, 48):
            pygame.draw.line(self.screen, GRID, (x, 0), (x, HEIGHT), 1)
        for y in range(0, HEIGHT, 48):
            pygame.draw.line(self.screen, GRID, (0, y), (WIDTH, y), 1)

    def _draw_ui(self):
        p = self.player
        # HP
        x, y, w, h = 18, 16, 230, 20
        pygame.draw.rect(self.screen, (40, 44, 56), (x, y, w, h), border_radius=5)
        ratio = max(0.0, p.hp / max(1, p.max_hp))
        color = GREEN if ratio > 0.35 else ORANGE if ratio > 0.15 else RED
        pygame.draw.rect(self.screen, color, (x, y, int(w * ratio), h), border_radius=5)
        pygame.draw.rect(self.screen, WHITE, (x, y, w, h), 2, border_radius=5)

        self.screen.blit(self.small.render(f"HP {int(p.hp)}/{int(p.max_hp)}", True, WHITE), (x + 8, y + 2))
        self.screen.blit(self.small.render(f"Sala {self.room.number}", True, WHITE), (18, 42))
        self.screen.blit(self.small.render(f"Nivel {p.level}", True, WHITE), (18, 62))
        self.screen.blit(self.small.render(f"Mejoras {len(p.upgrades_taken)}/{self.max_upgrades}", True, WHITE), (18, 82))

        # EXP
        ex, ey, ew, eh = 18, 105, 230, 10
        pygame.draw.rect(self.screen, (40, 44, 56), (ex, ey, ew, eh), border_radius=4)
        exp_ratio = p.exp / max(1, p.exp_next)
        pygame.draw.rect(self.screen, BLUE, (ex, ey, int(ew * exp_ratio), eh), border_radius=4)

        # Mensaje simbólico
        if self.message_timer > 0 and self.symbolic_message:
            msg = self.small.render(self.symbolic_message, True, CYAN)
            self.screen.blit(msg, msg.get_rect(center=(WIDTH // 2, HEIGHT - 24)))

        if self.room.is_boss and not self.room.cleared:
            btxt = self.small.render("BOSS: reflejo de tu sombra", True, PURPLE)
            self.screen.blit(btxt, btxt.get_rect(center=(WIDTH // 2, 20)))
        elif self.room.is_special:
            stxt = self.small.render("Sala especial: reliquia interior", True, ORANGE)
            self.screen.blit(stxt, stxt.get_rect(center=(WIDTH // 2, 20)))

    def _draw_doors(self):
        for d in self.doors:
            pygame.draw.rect(self.screen, d.color, d.rect)
            name = self.small.render(d.type.value, True, WHITE)
            self.screen.blit(name, name.get_rect(center=d.rect.center))

    def _draw_menu(self):
        title = self.font.render("ROGUELIKE SIMBOLICO", True, WHITE)
        sub = self.small.render("Cruza puertas: Conflicto / Contemplacion / Sombra / Ascenso", True, (175, 185, 200))
        play = self.small.render("ENTER para comenzar", True, GREEN)
        self.screen.blit(title, title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 36)))
        self.screen.blit(sub, sub.get_rect(center=(WIDTH // 2, HEIGHT // 2)))
        self.screen.blit(play, play.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 36)))

    def _draw_level_up(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((8, 10, 16, 220))
        self.screen.blit(overlay, (0, 0))

        title = self.font.render("NIVEL +1  |  Elige una mejora (1/2/3)", True, WHITE)
        self.screen.blit(title, title.get_rect(center=(WIDTH // 2, 150)))

        for i, opt in enumerate(self.level_up_options, start=1):
            rect = pygame.Rect(WIDTH // 2 - 220, 190 + (i - 1) * 72, 440, 52)
            pygame.draw.rect(self.screen, (34, 39, 52), rect, border_radius=8)
            pygame.draw.rect(self.screen, BLUE, rect, 2, border_radius=8)
            txt = self.small.render(f"{i}. {opt.label}", True, WHITE)
            self.screen.blit(txt, (rect.x + 16, rect.y + 16))

    def _draw_game_over(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((6, 8, 12, 200))
        self.screen.blit(overlay, (0, 0))
        t1 = self.font.render("GAME OVER", True, RED)
        t2 = self.small.render("R reiniciar | ESC salir", True, WHITE)
        self.screen.blit(t1, t1.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 14)))
        self.screen.blit(t2, t2.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 24)))

    # -------------------- events --------------------
    def _handle_events(self):
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                self.running = False

            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    self.running = False

                if self.state == GameState.MENU and ev.key == pygame.K_RETURN:
                    self.state = GameState.PLAYING

                elif self.state == GameState.PLAYING:
                    if ev.key in (pygame.K_LSHIFT, pygame.K_RSHIFT):
                        self.player.try_dash()

                elif self.state == GameState.GAME_OVER and ev.key == pygame.K_r:
                    self.clean_reset()

                elif self.state == GameState.LEVEL_UP:
                    if ev.key in (pygame.K_1, pygame.K_KP1) and len(self.level_up_options) >= 1:
                        self._apply_upgrade(self.level_up_options[0])
                    elif ev.key in (pygame.K_2, pygame.K_KP2) and len(self.level_up_options) >= 2:
                        self._apply_upgrade(self.level_up_options[1])
                    elif ev.key in (pygame.K_3, pygame.K_KP3) and len(self.level_up_options) >= 3:
                        self._apply_upgrade(self.level_up_options[2])

            elif ev.type == pygame.MOUSEBUTTONDOWN:
                if self.state == GameState.PLAYING and ev.button == 1:
                    self._player_shoot()

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            dt = min(dt, 0.033)

            self._handle_events()

            if self.state == GameState.PLAYING:
                self._update_playing(dt)

            self.screen.fill(BG)
            self._draw_grid()

            if self.state == GameState.MENU:
                self._draw_menu()
            else:
                self.all_sprites.draw(self.screen)
                self._draw_doors()
                self._draw_ui()

                if self.state == GameState.LEVEL_UP:
                    self._draw_level_up()
                elif self.state == GameState.GAME_OVER:
                    self._draw_game_over()

            pygame.display.flip()

        pygame.quit()


if __name__ == "__main__":
    # Archivo único ejecutable, sin assets externos.
    Game().run()
