import random

import pygame
from pygame.math import Vector2

from game.config import BG, FPS, GRID, HEIGHT, MAX_LEVELS, WHITE, WIDTH
from game.core.state_machine import GameState, StateMachine
from game.core.tension_system import TensionSystem
from game.entities.boss import Boss
from game.entities.enemy import Enemy
from game.entities.player import Player
from game.entities.reflection import Reflection
from game.systems.door_system import DoorSystem
from game.systems.mirror_mode import MirrorMode
from game.systems.psychological_profile import PsychologicalProfile
from game.systems.world_memory import WorldMemory
from game.ui.hud import HUD
from game.ui.menus import Menus


class GameManager:
    def __init__(self, screen):
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("consolas", 22)
        self.small = pygame.font.SysFont("consolas", 16)

        self.sm = StateMachine()
        self.tension = TensionSystem()
        self.world_memory = WorldMemory()
        self.profile = PsychologicalProfile()
        self.door_system = DoorSystem()
        self.mirror_mode = MirrorMode()
        self.hud = HUD()
        self.menus = Menus()

        self.all_sprites = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.player_bullets = pygame.sprite.Group()

        self.player = Player(Vector2(WIDTH // 2, HEIGHT // 2))
        self.all_sprites.add(self.player)

        self.level = 1
        self.difficulty = 1
        self.doors = []
        self.message = ""
        self.final_text = ""
        self.spawn_reflection_next = False
        self.damage_taken = 0.0

        self._spawn_level()

    def _spawn_level(self):
        for g in (self.enemies, self.player_bullets):
            for s in list(g):
                s.kill()
        self.doors.clear()

        if self.level in (3, 6, 8):
            self.sm.set(GameState.BOSS)
            if self.spawn_reflection_next:
                style = self.mirror_mode.infer_style(self.world_memory.data.get("action_buffer", []))
                boss = Reflection(Vector2(WIDTH // 2, 140), style)
                self.spawn_reflection_next = False
            else:
                boss = Boss(Vector2(WIDTH // 2, 120), self.level)
            self.enemies.add(boss)
            self.all_sprites.add(boss)
            return

        self.sm.set(GameState.RUNNING)
        count = min(10, 2 + self.difficulty // 2 + random.randint(0, 2))
        for _ in range(count):
            p = Vector2(random.randint(40, WIDTH - 40), random.randint(40, HEIGHT - 40))
            e = Enemy(p, 22 + self.difficulty * 2.5, 90 + self.difficulty * 4, 10 + self.difficulty)
            self.enemies.add(e)
            self.all_sprites.add(e)

    def _advance(self):
        if self.level >= MAX_LEVELS:
            final_type = "SECRET" if self.damage_taken == 0 else self.profile.final_evaluation()
            self.world_memory.complete_run(self.level, final_type)
            self.final_text = "Secret ending unlocked." if final_type == "SECRET" else f"Final archetype: {final_type}"
            self.sm.set(GameState.FINAL)
            return
        self.level += 1
        self._spawn_level()

    def _reset(self):
        self.__init__(self.screen)
        self.sm.set(GameState.RUNNING)

    def _update_simulation(self, dt: float):
        keys = pygame.key.get_pressed()
        invert = any(isinstance(e, Reflection) for e in self.enemies)
        self.player.move_input(keys, invert=invert)
        self.player.update(dt)

        for e in list(self.enemies):
            e.update(dt, self.player.pos)

        self.player_bullets.update(dt)

        for e, bullets in pygame.sprite.groupcollide(self.enemies, self.player_bullets, False, True).items():
            for b in bullets:
                if e.take_damage(b.damage):
                    self.profile.register_room_clear()

        for e in pygame.sprite.spritecollide(self.player, self.enemies, False):
            if self.player.hp > 0:
                self.player.hp -= e.damage * dt * 4.0
                self.damage_taken += e.damage * dt * 4.0
                self.profile.register_hit_taken()
            if self.player.hp <= 0:
                self.world_memory.complete_run(self.level, "DEFEAT")
                self.sm.set(GameState.GAME_OVER)

        if len(self.enemies) == 0 and not self.doors:
            self.doors = self.door_system.create_doors()

        for d in self.doors:
            if self.player.rect.colliderect(d.rect):
                self.message = self.door_system.apply(d.type, self)
                self._advance()
                break

        self.tension.update(self.player.shots_fired, self.damage_taken, len(self.enemies), dt)

    def run(self):
        running = True
        while running:
            dt = min(0.033, self.clock.tick(FPS) / 1000.0)
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    running = False
                elif e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_ESCAPE:
                        running = False
                    if self.sm.is_state(GameState.MENU) and e.key == pygame.K_RETURN:
                        self.sm.set(GameState.RUNNING)
                    if self.sm.is_state(GameState.GAME_OVER) and e.key == pygame.K_r:
                        self._reset()
                    if self.sm.is_state(GameState.FINAL) and e.key == pygame.K_r:
                        self._reset()
                elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    if self.sm.current in (GameState.RUNNING, GameState.BOSS):
                        if self.player.shoot(pygame.mouse.get_pos(), self.player_bullets, self.all_sprites):
                            self.profile.register_shot()
                            self.world_memory.register_action("shoot")

            if self.sm.current in (GameState.RUNNING, GameState.BOSS):
                self._update_simulation(dt)

            self.screen.fill(BG)
            for x in range(0, WIDTH, 48):
                pygame.draw.line(self.screen, GRID, (x, 0), (x, HEIGHT), 1)
            for y in range(0, HEIGHT, 48):
                pygame.draw.line(self.screen, GRID, (0, y), (WIDTH, y), 1)

            if self.sm.is_state(GameState.MENU):
                self.menus.draw_menu(self.screen, self.font, self.small)
            else:
                self.all_sprites.draw(self.screen)
                for d in self.doors:
                    pygame.draw.rect(self.screen, d.color, d.rect)
                    label = self.small.render(d.type.value, True, WHITE)
                    self.screen.blit(label, label.get_rect(center=d.rect.center))
                self.hud.draw(self.screen, self.small, self.player, self.level, self.tension.tension_level, self.profile.final_evaluation(), self.message)

                if self.sm.is_state(GameState.GAME_OVER):
                    self.menus.draw_end(self.screen, self.font, self.small, "GAME OVER", "You were consumed by your own conflict.")
                if self.sm.is_state(GameState.FINAL):
                    self.menus.draw_end(self.screen, self.font, self.small, "FINAL", self.final_text)

            pygame.display.flip()
