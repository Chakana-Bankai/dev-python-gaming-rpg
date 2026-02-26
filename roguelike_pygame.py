import math
import random
from dataclasses import dataclass
from enum import Enum, auto

import pygame
from pygame.math import Vector2


# =============================
# Configuración global
# =============================
SCREEN_WIDTH = 960
SCREEN_HEIGHT = 540
FPS = 60
ROOM_GRID_RADIUS = 3  # Cuántas habitaciones alrededor del origen pueden existir.

# Colores minimalistas
BG_COLOR = (16, 18, 24)
GRID_COLOR = (24, 28, 38)
WHITE = (236, 238, 245)
RED = (220, 78, 96)
GREEN = (75, 200, 115)
YELLOW = (240, 196, 83)
BLUE = (93, 131, 225)
PURPLE = (171, 108, 220)
ORANGE = (237, 154, 74)


class GameState(Enum):
    MENU = auto()
    PLAYING = auto()
    GAME_OVER = auto()


class UpgradeType(Enum):
    MAX_HP = auto()
    DAMAGE = auto()


@dataclass
class Room:
    """Modelo de una habitación procedural.

    Arquitectura limpia básica:
    - Esta clase es solo estado de dominio (datos), sin lógica de render.
    - La lógica de spawn/transición vive en `DungeonManager`.
    """

    coords: tuple[int, int]
    cleared: bool = False
    visited: bool = False


class Bullet(pygame.sprite.Sprite):
    def __init__(self, pos: Vector2, direction: Vector2, damage: int, speed: float = 560.0):
        super().__init__()
        self.image = pygame.Surface((8, 4), pygame.SRCALPHA)
        self.image.fill(YELLOW)
        self.rect = self.image.get_rect(center=(int(pos.x), int(pos.y)))

        self.pos = Vector2(pos)
        self.direction = direction.normalize() if direction.length_squared() > 0 else Vector2(1, 0)
        self.speed = speed
        self.damage = damage
        self.lifetime = 0.9

    def update(self, dt: float):
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.kill()
            return

        self.pos += self.direction * self.speed * dt
        self.rect.center = (int(self.pos.x), int(self.pos.y))

        # Optimización: destruir balas fuera de pantalla
        if (
            self.rect.right < -20
            or self.rect.left > SCREEN_WIDTH + 20
            or self.rect.bottom < -20
            or self.rect.top > SCREEN_HEIGHT + 20
        ):
            self.kill()


class Enemy(pygame.sprite.Sprite):
    def __init__(self, pos: Vector2, hp: float, speed: float, damage: float):
        super().__init__()
        self.base_image = pygame.Surface((26, 26), pygame.SRCALPHA)
        self.base_image.fill(RED)
        self.image = self.base_image.copy()
        self.rect = self.image.get_rect(center=(int(pos.x), int(pos.y)))

        self.pos = Vector2(pos)
        self.velocity = Vector2()
        self.hp = hp
        self.max_hp = hp
        self.speed = speed
        self.damage = damage
        self.knockback = Vector2()

    def apply_knockback(self, direction: Vector2, force: float):
        if direction.length_squared() > 0:
            self.knockback += direction.normalize() * force

    def take_damage(self, amount: float):
        self.hp -= amount
        if self.hp <= 0:
            self.kill()
            return True
        return False

    def update(self, dt: float, player_pos: Vector2):
        to_player = player_pos - self.pos
        if to_player.length_squared() > 0:
            self.velocity = to_player.normalize() * self.speed
        else:
            self.velocity = Vector2()

        # Movimiento con knockback ligero amortiguado
        self.pos += (self.velocity + self.knockback) * dt
        self.knockback *= max(0.0, 1 - 8 * dt)
        self.rect.center = (int(self.pos.x), int(self.pos.y))


class Player(pygame.sprite.Sprite):
    def __init__(self, pos: Vector2):
        super().__init__()
        self.base_image = pygame.Surface((28, 28), pygame.SRCALPHA)
        self.base_image.fill(BLUE)
        self.image = self.base_image.copy()
        self.rect = self.image.get_rect(center=(int(pos.x), int(pos.y)))

        self.pos = Vector2(pos)
        self.velocity = Vector2()

        self.speed = 220.0
        self.hp = 100
        self.max_hp = 100
        self.damage = 18

        self.fire_cooldown = 0.16
        self.fire_timer = 0.0

        self.dash_speed = 620.0
        self.dash_duration = 0.13
        self.dash_cooldown = 1.1
        self.dash_timer = 0.0
        self.dash_cd_timer = 0.0
        self.dash_direction = Vector2(1, 0)

        self.invulnerability = 0.0
        self.blink_timer = 0.0

        self.level = 1
        self.exp = 0
        self.exp_to_next = 40

    def reset_for_new_run(self, pos: Vector2):
        self.pos = Vector2(pos)
        self.rect.center = (int(pos.x), int(pos.y))
        self.velocity = Vector2()
        self.speed = 220.0
        self.hp = 100
        self.max_hp = 100
        self.damage = 18
        self.fire_timer = 0.0
        self.dash_timer = 0.0
        self.dash_cd_timer = 0.0
        self.invulnerability = 0.0
        self.level = 1
        self.exp = 0
        self.exp_to_next = 40

    def gain_exp(self, amount: int):
        self.exp += amount
        while self.exp >= self.exp_to_next:
            self.exp -= self.exp_to_next
            self.level += 1
            self.exp_to_next = int(self.exp_to_next * 1.25)
            self.apply_upgrade()

    def apply_upgrade(self):
        # Mejora simple al subir nivel: alternar entre vida máxima y daño
        if self.level % 2 == 0:
            upgrade = UpgradeType.MAX_HP
        else:
            upgrade = UpgradeType.DAMAGE

        if upgrade == UpgradeType.MAX_HP:
            self.max_hp += 12
            self.hp = min(self.max_hp, self.hp + 10)
        elif upgrade == UpgradeType.DAMAGE:
            self.damage += 4

    def take_damage(self, amount: float):
        if self.invulnerability > 0:
            return False
        self.hp -= amount
        self.invulnerability = 0.7
        self.blink_timer = 0.0
        return self.hp <= 0

    def handle_input(self, keys: pygame.key.ScancodeWrapper):
        move = Vector2(0, 0)
        if keys[pygame.K_w]:
            move.y -= 1
        if keys[pygame.K_s]:
            move.y += 1
        if keys[pygame.K_a]:
            move.x -= 1
        if keys[pygame.K_d]:
            move.x += 1

        if move.length_squared() > 0:
            self.velocity = move.normalize() * self.speed
            self.dash_direction = move.normalize()
        else:
            self.velocity = Vector2()

    def try_dash(self):
        if self.dash_cd_timer <= 0 and self.dash_direction.length_squared() > 0:
            self.dash_timer = self.dash_duration
            self.dash_cd_timer = self.dash_cooldown

    def try_fire(self, bullet_group: pygame.sprite.Group, all_sprites: pygame.sprite.Group):
        if self.fire_timer > 0:
            return

        mouse = Vector2(pygame.mouse.get_pos())
        direction = mouse - self.pos
        if direction.length_squared() == 0:
            direction = Vector2(1, 0)

        bullet = Bullet(self.pos + direction.normalize() * 18, direction, self.damage)
        bullet_group.add(bullet)
        all_sprites.add(bullet)
        self.fire_timer = self.fire_cooldown

    def update(self, dt: float):
        self.fire_timer = max(0.0, self.fire_timer - dt)
        self.dash_cd_timer = max(0.0, self.dash_cd_timer - dt)

        if self.invulnerability > 0:
            self.invulnerability = max(0.0, self.invulnerability - dt)
            self.blink_timer += dt
            if int(self.blink_timer * 20) % 2 == 0:
                self.image = self.base_image.copy()
            else:
                self.image = pygame.Surface((28, 28), pygame.SRCALPHA)
                self.image.fill((130, 170, 255, 110))
        else:
            self.image = self.base_image.copy()

        current_velocity = Vector2(self.velocity)
        if self.dash_timer > 0:
            self.dash_timer -= dt
            current_velocity = self.dash_direction * self.dash_speed

        self.pos += current_velocity * dt

        # Mantener jugador dentro de la habitación (pantalla)
        self.pos.x = max(14, min(SCREEN_WIDTH - 14, self.pos.x))
        self.pos.y = max(14, min(SCREEN_HEIGHT - 14, self.pos.y))
        self.rect.center = (int(self.pos.x), int(self.pos.y))


class DungeonManager:
    """Gestiona generación procedural de habitaciones en grilla y progresión."""

    DIRECTIONS = {
        "N": (0, -1),
        "S": (0, 1),
        "W": (-1, 0),
        "E": (1, 0),
    }

    def __init__(self):
        self.rooms: dict[tuple[int, int], Room] = {}
        self.current_coords = (0, 0)
        self.room_counter = 1
        self.difficulty_index = 1

        self._ensure_room_exists((0, 0))

    def reset(self):
        self.rooms.clear()
        self.current_coords = (0, 0)
        self.room_counter = 1
        self.difficulty_index = 1
        self._ensure_room_exists((0, 0))

    def _ensure_room_exists(self, coords: tuple[int, int]):
        if coords not in self.rooms:
            self.rooms[coords] = Room(coords=coords)

    def _is_in_bounds(self, coords: tuple[int, int]) -> bool:
        return abs(coords[0]) <= ROOM_GRID_RADIUS and abs(coords[1]) <= ROOM_GRID_RADIUS

    def available_doors(self):
        x, y = self.current_coords
        doors = {}
        for name, (dx, dy) in self.DIRECTIONS.items():
            target = (x + dx, y + dy)
            if self._is_in_bounds(target):
                doors[name] = target
        return doors

    def move_to(self, coords: tuple[int, int]):
        self.current_coords = coords
        self.room_counter += 1
        self.difficulty_index += 1
        self._ensure_room_exists(coords)
        self.rooms[coords].visited = True

    def mark_current_cleared(self):
        self.rooms[self.current_coords].cleared = True

    def current_room(self) -> Room:
        return self.rooms[self.current_coords]


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Minimal Procedural Roguelike")
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("consolas", 22)
        self.small_font = pygame.font.SysFont("consolas", 16)

        self.state = GameState.MENU
        self.running = True

        self.all_sprites = pygame.sprite.Group()
        self.enemy_group = pygame.sprite.Group()
        self.bullet_group = pygame.sprite.Group()

        self.player = Player(Vector2(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.all_sprites.add(self.player)

        self.dungeon = DungeonManager()

        # Puertas activas cuando la sala está limpia
        self.door_rects = {}
        self.transition_lock = False

        self._spawn_current_room()

    # -------------------------
    # Ciclo de vida del juego
    # -------------------------
    def reset_run(self):
        """Reinicio limpio de partida sin reiniciar programa."""
        self.all_sprites.empty()
        self.enemy_group.empty()
        self.bullet_group.empty()

        self.player.reset_for_new_run(Vector2(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.all_sprites.add(self.player)

        self.dungeon.reset()
        self.state = GameState.PLAYING
        self.transition_lock = False
        self._spawn_current_room()

    def _spawn_current_room(self):
        """Spawn procedural de enemigos según dificultad / habitación."""
        self.enemy_group.empty()

        room = self.dungeon.current_room()
        if room.cleared:
            self._build_doors(active=True)
            return

        base_count = 2 + self.dungeon.difficulty_index // 2
        enemy_count = min(10, base_count + random.randint(0, 2))

        for _ in range(enemy_count):
            pos = self._random_spawn_position_away_from_player(130)
            hp = 20 + self.dungeon.difficulty_index * 3.5
            speed = 90 + min(130, self.dungeon.difficulty_index * 5)
            damage = 9 + self.dungeon.difficulty_index * 0.8
            enemy = Enemy(pos, hp=hp, speed=speed, damage=damage)
            self.enemy_group.add(enemy)
            self.all_sprites.add(enemy)

        self._build_doors(active=False)

    def _random_spawn_position_away_from_player(self, min_distance: float) -> Vector2:
        for _ in range(40):
            pos = Vector2(
                random.randint(40, SCREEN_WIDTH - 40),
                random.randint(40, SCREEN_HEIGHT - 40),
            )
            if pos.distance_to(self.player.pos) >= min_distance:
                return pos
        return Vector2(random.randint(40, SCREEN_WIDTH - 40), random.randint(40, SCREEN_HEIGHT - 40))

    def _build_doors(self, active: bool):
        self.door_rects.clear()
        if not active:
            return

        # Puertas simples en bordes de pantalla
        door_size = (80, 18)
        doors = self.dungeon.available_doors()

        if "N" in doors:
            self.door_rects["N"] = pygame.Rect((SCREEN_WIDTH - door_size[0]) // 2, 0, *door_size)
        if "S" in doors:
            self.door_rects["S"] = pygame.Rect((SCREEN_WIDTH - door_size[0]) // 2, SCREEN_HEIGHT - door_size[1], *door_size)
        if "W" in doors:
            self.door_rects["W"] = pygame.Rect(0, (SCREEN_HEIGHT - door_size[0]) // 2, door_size[1], door_size[0])
        if "E" in doors:
            self.door_rects["E"] = pygame.Rect(SCREEN_WIDTH - door_size[1], (SCREEN_HEIGHT - door_size[0]) // 2, door_size[1], door_size[0])

    # -------------------------
    # Update
    # -------------------------
    def update_playing(self, dt: float):
        keys = pygame.key.get_pressed()
        self.player.handle_input(keys)
        self.player.update(dt)

        for enemy in list(self.enemy_group):
            enemy.update(dt, self.player.pos)

        self.bullet_group.update(dt)

        self._handle_collisions(dt)

        if len(self.enemy_group) == 0 and not self.dungeon.current_room().cleared:
            self.dungeon.mark_current_cleared()
            self._build_doors(active=True)

        self._check_room_transition()

    def _handle_collisions(self, dt: float):
        # Balas vs enemigos
        hits = pygame.sprite.groupcollide(self.enemy_group, self.bullet_group, False, True)
        for enemy, bullets in hits.items():
            for bullet in bullets:
                dead = enemy.take_damage(bullet.damage)
                enemy.apply_knockback(bullet.direction, 130)
                if dead:
                    self.player.gain_exp(10 + self.dungeon.difficulty_index)

        # Enemigos vs jugador
        enemy_hits = pygame.sprite.spritecollide(self.player, self.enemy_group, False)
        for enemy in enemy_hits:
            to_player = self.player.pos - enemy.pos
            enemy.apply_knockback(-to_player if to_player.length_squared() > 0 else Vector2(1, 0), 35)
            if self.player.take_damage(enemy.damage * dt * 4.8):
                self.state = GameState.GAME_OVER

    def _check_room_transition(self):
        if not self.dungeon.current_room().cleared or self.transition_lock:
            return

        for direction, door_rect in self.door_rects.items():
            if self.player.rect.colliderect(door_rect):
                self.transition_lock = True
                target = self.dungeon.available_doors()[direction]
                self.dungeon.move_to(target)

                # Limpiar balas al cambiar de habitación para evitar basura lógica
                self.bullet_group.empty()
                self.all_sprites = pygame.sprite.Group(self.player, *self.enemy_group.sprites())
                self._spawn_current_room()

                # Reubicar jugador según puerta de entrada
                if direction == "N":
                    self.player.pos = Vector2(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 35)
                elif direction == "S":
                    self.player.pos = Vector2(SCREEN_WIDTH // 2, 35)
                elif direction == "W":
                    self.player.pos = Vector2(SCREEN_WIDTH - 35, SCREEN_HEIGHT // 2)
                elif direction == "E":
                    self.player.pos = Vector2(35, SCREEN_HEIGHT // 2)
                self.player.rect.center = (int(self.player.pos.x), int(self.player.pos.y))

                self.transition_lock = False
                break

    # -------------------------
    # Render
    # -------------------------
    def draw(self):
        self.screen.fill(BG_COLOR)
        self._draw_background_grid()

        if self.state == GameState.MENU:
            self._draw_menu()
        elif self.state == GameState.PLAYING:
            self._draw_playing()
        elif self.state == GameState.GAME_OVER:
            self._draw_playing()
            self._draw_game_over_overlay()

        pygame.display.flip()

    def _draw_background_grid(self):
        for x in range(0, SCREEN_WIDTH, 48):
            pygame.draw.line(self.screen, GRID_COLOR, (x, 0), (x, SCREEN_HEIGHT), 1)
        for y in range(0, SCREEN_HEIGHT, 48):
            pygame.draw.line(self.screen, GRID_COLOR, (0, y), (SCREEN_WIDTH, y), 1)

    def _draw_menu(self):
        title = self.font.render("MINIMAL ROGUELIKE", True, WHITE)
        subtitle = self.small_font.render("WASD mover | Click disparar | Shift dash", True, (180, 186, 200))
        prompt = self.small_font.render("Pulsa ENTER para empezar", True, GREEN)

        self.screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40)))
        self.screen.blit(subtitle, subtitle.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)))
        self.screen.blit(prompt, prompt.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 40)))

    def _draw_playing(self):
        self.all_sprites.draw(self.screen)

        for door_rect in self.door_rects.values():
            pygame.draw.rect(self.screen, PURPLE, door_rect)

        self._draw_ui()

    def _draw_game_over_overlay(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((5, 7, 10, 170))
        self.screen.blit(overlay, (0, 0))

        game_over = self.font.render("GAME OVER", True, RED)
        info = self.small_font.render("Pulsa R para reiniciar o ESC para salir", True, WHITE)
        self.screen.blit(game_over, game_over.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20)))
        self.screen.blit(info, info.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20)))

    def _draw_ui(self):
        # Barra de vida
        bar_x, bar_y, bar_w, bar_h = 20, 20, 220, 22
        pygame.draw.rect(self.screen, (42, 46, 58), (bar_x, bar_y, bar_w, bar_h), border_radius=5)
        hp_ratio = max(0.0, self.player.hp / self.player.max_hp)
        pygame.draw.rect(
            self.screen,
            GREEN if hp_ratio > 0.35 else ORANGE if hp_ratio > 0.15 else RED,
            (bar_x, bar_y, int(bar_w * hp_ratio), bar_h),
            border_radius=5,
        )
        pygame.draw.rect(self.screen, WHITE, (bar_x, bar_y, bar_w, bar_h), 2, border_radius=5)

        hp_text = self.small_font.render(f"HP: {int(self.player.hp)}/{self.player.max_hp}", True, WHITE)
        level_text = self.small_font.render(f"Nivel: {self.player.level}", True, WHITE)
        room_text = self.small_font.render(f"Habitacion: {self.dungeon.room_counter}", True, WHITE)
        dmg_text = self.small_font.render(f"Danio: {self.player.damage}", True, WHITE)

        self.screen.blit(hp_text, (bar_x + 8, bar_y + 2))
        self.screen.blit(level_text, (20, 52))
        self.screen.blit(room_text, (20, 74))
        self.screen.blit(dmg_text, (20, 96))

        # Barra de experiencia
        exp_x, exp_y, exp_w, exp_h = 20, 122, 220, 12
        pygame.draw.rect(self.screen, (42, 46, 58), (exp_x, exp_y, exp_w, exp_h), border_radius=4)
        exp_ratio = self.player.exp / max(1, self.player.exp_to_next)
        pygame.draw.rect(self.screen, BLUE, (exp_x, exp_y, int(exp_w * exp_ratio), exp_h), border_radius=4)
        pygame.draw.rect(self.screen, WHITE, (exp_x, exp_y, exp_w, exp_h), 1, border_radius=4)

    # -------------------------
    # Input / loop principal
    # -------------------------
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False

                if self.state == GameState.MENU and event.key == pygame.K_RETURN:
                    self.state = GameState.PLAYING

                if self.state == GameState.PLAYING:
                    if event.key in (pygame.K_LSHIFT, pygame.K_RSHIFT):
                        self.player.try_dash()

                if self.state == GameState.GAME_OVER and event.key == pygame.K_r:
                    self.reset_run()

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if self.state == GameState.PLAYING and event.button == 1:
                    self.player.try_fire(self.bullet_group, self.all_sprites)

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0  # Delta time para movimiento independiente de FPS
            dt = min(dt, 0.033)  # Clamping anti-spike

            self.handle_events()

            if self.state == GameState.PLAYING:
                self.update_playing(dt)

            self.draw()

        pygame.quit()


if __name__ == "__main__":
    # Entry point único para cumplir requisito de ejecutable en un solo .py
    Game().run()
