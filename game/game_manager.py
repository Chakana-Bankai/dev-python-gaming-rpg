import random

import pygame
from pygame.math import Vector2

from game.entities.boss import BossOne, BossTwo, ReflectBoss
from game.entities.enemy import Enemy
from game.entities.player import Player
from game.entities.super_boss import SuperBoss
from game.settings import BG, DARK_OVERLAY, FPS, GRID, HEIGHT, GameState, WIDTH
from game.systems.combat_system import CombatSystem
from game.systems.door_system import DoorSystem
from game.systems.item_system import ItemSystem
from game.systems.level_system import LevelMeta, LevelSystem
from game.systems.narrative_system import NarrativeSystem
from game.systems.upgrade_system import UpgradeSystem
from game.ui.end_screen import EndScreen
from game.ui.hud import HUD
from game.ui.level_up_screen import LevelUpScreen
from game.utils.helpers import random_pos_away


class GameManager:
    """Orquestador principal:
    - Mantiene estados globales de run
    - Coordina sistemas de dominio
    - Separa render/UI de la lógica de simulación
    """

    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Symbolic Roguelike")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("consolas", 22)
        self.small_font = pygame.font.SysFont("consolas", 16)

        self.running = True
        self.state = GameState.MENU

        self.door_system = DoorSystem()
        self.level_system = LevelSystem()
        self.upgrade_system = UpgradeSystem(max_upgrades=4)
        self.item_system = ItemSystem()
        self.combat_system = CombatSystem()
        self.narrative_system = NarrativeSystem()

        self.hud = HUD()
        self.level_up_screen = LevelUpScreen()
        self.end_screen = EndScreen()

        self.all_sprites = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.player_bullets = pygame.sprite.Group()
        self.enemy_bullets = pygame.sprite.Group()
        self.pickups = pygame.sprite.Group()

        self.player = Player(Vector2(WIDTH // 2, HEIGHT // 2))
        self.all_sprites.add(self.player)

        self.level_meta = LevelMeta(index=1, is_boss=False, is_final_boss=False, is_shadow_event=False)
        self.difficulty = 1
        self.doors = []
        self.level_up_options = []
        self.message = ""
        self.message_timer = 0.0

        self.final_title = ""
        self.final_body = ""

        self.spawn_level_content()

    def clean_reset(self):
        self.all_sprites.empty()
        self.enemies.empty()
        self.player_bullets.empty()
        self.enemy_bullets.empty()
        self.pickups.empty()

        self.player = Player(Vector2(WIDTH // 2, HEIGHT // 2))
        self.all_sprites.add(self.player)

        self.level_meta = LevelMeta(index=1, is_boss=False, is_final_boss=False, is_shadow_event=False)
        self.difficulty = 1
        self.doors = []
        self.level_up_options = []
        self.message = ""
        self.message_timer = 0.0
        self.final_title = ""
        self.final_body = ""
        self.state = GameState.PLAYING
        self.spawn_level_content()

    def to_game_over(self):
        self.state = GameState.GAME_OVER

    def advance_level(self):
        if self.level_meta.index >= 8:
            if self.player.damage_taken_total == 0:
                self.state = GameState.SECRET_FINAL
                self.final_title = "SECRET FINAL"
                self.final_body = self.narrative_system.secret_final()
            else:
                self.state = GameState.GAME_OVER
                self.final_title = "FINAL"
                self.final_body = self.narrative_system.normal_final()
            return

        self.level_meta = self.level_system.next_level(self.level_meta.index)
        self.spawn_level_content()

    def spawn_level_content(self):
        for g in (self.enemies, self.player_bullets, self.enemy_bullets, self.pickups):
            for s in list(g):
                s.kill()
        self.doors.clear()

        if self.level_meta.is_boss:
            self.state = GameState.BOSS
            if self.player.damage_taken_total == 0 and self.level_meta.index == 8:
                b = SuperBoss(Vector2(WIDTH // 2, 120))
            elif self.level_meta.index == 3:
                b = BossOne(Vector2(WIDTH // 2, 120))
            elif self.level_meta.index == 6:
                b = BossTwo(Vector2(WIDTH // 2, 120))
            else:
                b = ReflectBoss(Vector2(WIDTH // 2, 120), self.player)
            self.enemies.add(b)
            self.all_sprites.add(b)
            return

        self.state = GameState.PLAYING
        count = min(10, 2 + self.difficulty // 2 + random.randint(0, 2))
        for _ in range(count):
            p = random_pos_away(self.player.pos, 130)
            enemy = Enemy(p, 18 + self.difficulty * 3.2, 90 + min(130, self.difficulty * 4), 10 + self.difficulty * 0.8)
            self.enemies.add(enemy)
            self.all_sprites.add(enemy)

    def open_doors(self):
        self.doors = self.door_system.create_three_doors()

    def update(self, dt: float):
        if self.state in (GameState.GAME_OVER, GameState.SECRET_FINAL, GameState.MENU, GameState.LEVEL_UP):
            return

        keys = pygame.key.get_pressed()
        self.player.move_input(keys)
        # Super boss: invert controls by inverting velocity each frame
        if any(isinstance(e, SuperBoss) for e in self.enemies):
            self.player.vel *= -1
        self.player.update(dt)

        for e in list(self.enemies):
            if isinstance(e, (BossOne, BossTwo, ReflectBoss)):
                e.update(dt, self.player.pos, self.enemy_bullets, self.all_sprites)
            elif isinstance(e, SuperBoss):
                e.update(dt, self.player.pos)
            else:
                e.update(dt, self.player.pos)

        self.player_bullets.update(dt)
        self.enemy_bullets.update(dt)

        self.combat_system.handle(self, dt)

        if len(self.enemies) == 0 and not self.doors:
            self.open_doors()

        for d in self.doors:
            if self.player.rect.colliderect(d.rect):
                self.difficulty, self.message = self.door_system.apply_effect(d.type, self.player, self.difficulty)
                self.message_timer = 2.8
                if d.type.value == "Shadow" and random.random() < 0.85:
                    item = self.item_system.spawn_shadow_item(Vector2(WIDTH // 2, HEIGHT // 2))
                    self.pickups.add(item)
                    self.all_sprites.add(item)
                self.advance_level()
                break

        for i in pygame.sprite.spritecollide(self.player, self.pickups, True):
            msg = self.item_system.apply_item(self.player, i)
            if msg:
                self.message = msg
                self.message_timer = 3.0

        if self.message_timer > 0:
            self.message_timer -= dt

    def draw(self):
        self.screen.fill(BG)
        for x in range(0, WIDTH, 48):
            pygame.draw.line(self.screen, GRID, (x, 0), (x, HEIGHT), 1)
        for y in range(0, HEIGHT, 48):
            pygame.draw.line(self.screen, GRID, (0, y), (WIDTH, y), 1)

        if self.state == GameState.MENU:
            t = self.font.render("SYMBOLIC ROGUELIKE", True, (230, 233, 240))
            s = self.small_font.render(self.narrative_system.menu_intro(), True, (180, 186, 200))
            p = self.small_font.render("ENTER to start", True, (72, 196, 114))
            self.screen.blit(t, t.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 34)))
            self.screen.blit(s, s.get_rect(center=(WIDTH // 2, HEIGHT // 2)))
            self.screen.blit(p, p.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 34)))
        else:
            self.all_sprites.draw(self.screen)
            for d in self.doors:
                pygame.draw.rect(self.screen, d.color, d.rect)
                label = self.small_font.render(d.type.value, True, (230, 233, 240))
                self.screen.blit(label, label.get_rect(center=d.rect.center))

            self.hud.draw(self.screen, self.small_font, self.player, self.level_meta.index, self.upgrade_system.max_upgrades, self.message, self.message_timer)

            if any(isinstance(e, SuperBoss) for e in self.enemies):
                overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                overlay.fill(DARK_OVERLAY)
                self.screen.blit(overlay, (0, 0))

            if self.state == GameState.LEVEL_UP:
                self.level_up_screen.draw(self.screen, self.font, self.small_font, self.level_up_options)
            if self.state == GameState.GAME_OVER:
                if self.final_title:
                    self.end_screen.draw_final(self.screen, self.font, self.small_font, self.final_title, self.final_body)
                else:
                    self.end_screen.draw_game_over(self.screen, self.font, self.small_font)
            if self.state == GameState.SECRET_FINAL:
                self.end_screen.draw_final(self.screen, self.font, self.small_font, "SECRET FINAL", self.final_body)

        pygame.display.flip()

    def handle_events(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                self.running = False
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    self.running = False
                if self.state == GameState.MENU and e.key == pygame.K_RETURN:
                    self.state = GameState.PLAYING
                elif self.state == GameState.GAME_OVER and e.key == pygame.K_r:
                    self.clean_reset()
                elif self.state == GameState.SECRET_FINAL and e.key == pygame.K_r:
                    self.clean_reset()
                elif self.state == GameState.LEVEL_UP:
                    if e.key in (pygame.K_1, pygame.K_KP1) and len(self.level_up_options) >= 1:
                        _, self.message = self.upgrade_system.apply_upgrade(self.player, self.level_up_options[0])
                        self.state = GameState.PLAYING
                    elif e.key in (pygame.K_2, pygame.K_KP2) and len(self.level_up_options) >= 2:
                        _, self.message = self.upgrade_system.apply_upgrade(self.player, self.level_up_options[1])
                        self.state = GameState.PLAYING
                    elif e.key in (pygame.K_3, pygame.K_KP3) and len(self.level_up_options) >= 3:
                        _, self.message = self.upgrade_system.apply_upgrade(self.player, self.level_up_options[2])
                        self.state = GameState.PLAYING
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if self.state in (GameState.PLAYING, GameState.BOSS):
                    self.player.shoot(pygame.mouse.get_pos(), self.player_bullets, self.all_sprites)

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            dt = min(dt, 0.033)
            self.handle_events()
            self.update(dt)
            self.draw()
        pygame.quit()
