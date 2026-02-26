import random
from dataclasses import dataclass

import pygame
from pygame.math import Vector2

from game.config import BG, FPS, GRID, HEIGHT, MAX_LEVELS, RED, WHITE, WIDTH, YELLOW
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


@dataclass
class FloatingText:
    text: str
    pos: Vector2
    color: tuple[int, int, int]
    life: float = 0.6

    def update(self, dt: float):
        self.life -= dt
        self.pos.y -= 36 * dt


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

        self.card_options: list[tuple[str, callable]] = []
        self.door_lock_timer = 0.0
        self.floating_texts: list[FloatingText] = []
        self.spiritual_symbols = ["✦", "☾", "🜏", "☉", "⚚"]

        self._spawn_level()
        self.sm.set(GameState.MENU)

    def _roll_cards(self):
        p = self.player
        pool = [
            ("+25 HP max", lambda: setattr(p, "max_hp", p.max_hp + 25)),
            ("+4 Damage", lambda: setattr(p, "damage", p.damage + 4)),
            ("Triple Shot", lambda: setattr(p, "triple_shot", True)),
            ("Piercing +1", lambda: setattr(p, "pierce", min(3, p.pierce + 1))),
            ("Bounce +1", lambda: setattr(p, "bounce", min(3, p.bounce + 1))),
            ("Critical +10%", lambda: setattr(p, "crit_bonus", min(0.4, p.crit_bonus + 0.10))),
            ("Lifesteal +5%", lambda: setattr(p, "lifesteal", min(0.25, p.lifesteal + 0.05))),
            ("Dash CD -15%", lambda: setattr(p, "dash_cd", max(0.4, p.dash_cd * 0.85))),
        ]
        random.shuffle(pool)
        self.card_options = pool[:3]

    def _spawn_level(self):
        for g in (self.enemies, self.player_bullets):
            for s in list(g):
                s.kill()
        self.doors.clear()
        self.door_lock_timer = 0.65
        self.player.pos = Vector2(WIDTH // 2, HEIGHT // 2)
        self.player.rect.center = (int(self.player.pos.x), int(self.player.pos.y))

        if self.level in (3, 6, 8):
            self.sm.set(GameState.BOSS)
            if self.spawn_reflection_next:
                style = self.mirror_mode.infer_style(self.world_memory.data.get("action_buffer", []))
                boss = Reflection(Vector2(WIDTH // 2, 140), style)
                self.spawn_reflection_next = False
                self.message = "🜏 El reflejo aprende tus pasos."
            else:
                boss = Boss(Vector2(WIDTH // 2, 120), self.level, player=self.player)
                self.message = f"☠ Boss {self.level}: {boss.kind.upper()}"
            self.enemies.add(boss)
            self.all_sprites.add(boss)
            return

        self.sm.set(GameState.RUNNING)
        count = min(12, 3 + self.difficulty // 2 + random.randint(0, 2))
        for _ in range(count):
            p = Vector2(random.randint(40, WIDTH - 40), random.randint(40, HEIGHT - 40))
            kind_roll = random.random()
            kind = "chaser" if kind_roll < 0.55 else "rusher" if kind_roll < 0.8 else "tank"
            e = Enemy(
                p,
                20 + self.difficulty * 2.8,
                92 + self.difficulty * 4,
                9 + self.difficulty,
                kind=kind,
            )
            self.enemies.add(e)
            self.all_sprites.add(e)

    def _advance(self):
        if self.level >= MAX_LEVELS:
            final_type = "SECRET" if self.damage_taken == 0 else self.profile.final_evaluation()
            self.world_memory.complete_run(self.level, final_type)
            self.final_text = "✦ Final secreto: el drama se disuelve en luz." if final_type == "SECRET" else f"Final archetype: {final_type}"
            self.sm.set(GameState.FINAL)
            return
        self.level += 1
        self._spawn_level()

    def _reset(self):
        self.__init__(self.screen)
        self.sm.set(GameState.RUNNING)

    def _on_enemy_killed(self, enemy):
        xp = 35 if isinstance(enemy, (Boss, Reflection)) else 10 + self.difficulty
        if self.player.gain_exp(xp):
            self._roll_cards()
            self.sm.set(GameState.LEVEL_UP)

    def _update_simulation(self, dt: float):
        self.door_lock_timer = max(0.0, self.door_lock_timer - dt)

        keys = pygame.key.get_pressed()
        invert = any(isinstance(e, Reflection) for e in self.enemies)
        self.player.move_input(keys, invert=invert)
        self.player.update(dt)

        for e in list(self.enemies):
            e.update(dt, self.player.pos)

        self.player_bullets.update(dt)

        hits = pygame.sprite.groupcollide(self.enemies, self.player_bullets, False, False)
        for enemy, bullets in hits.items():
            for b in bullets:
                self.floating_texts.append(FloatingText(str(int(b.damage)), Vector2(enemy.rect.center), YELLOW))
                if enemy.take_damage(b.damage):
                    self.profile.register_room_clear()
                    self._on_enemy_killed(enemy)

                if self.player.lifesteal > 0:
                    self.player.hp = min(self.player.max_hp, self.player.hp + b.damage * self.player.lifesteal * 0.15)

                if b.pierce > 0:
                    b.pierce -= 1
                else:
                    b.kill()

        for e in pygame.sprite.spritecollide(self.player, self.enemies, False):
            if self.player.hp > 0:
                delta = e.damage * dt * 4.0
                self.player.hp -= delta
                self.damage_taken += delta
                self.profile.register_hit_taken()
                self.floating_texts.append(FloatingText(f"-{int(delta)}", Vector2(self.player.rect.center), RED))
            if self.player.hp <= 0:
                self.world_memory.complete_run(self.level, "DEFEAT")
                self.sm.set(GameState.GAME_OVER)

        if len(self.enemies) == 0 and not self.doors:
            self.doors = self.door_system.create_doors()

        if self.door_lock_timer <= 0:
            for d in self.doors:
                if self.player.rect.colliderect(d.rect):
                    self.message = self.door_system.apply(d.type, self)
                    self._advance()
                    break

        self.tension.update(self.player.shots_fired, self.damage_taken, len(self.enemies), dt)

        for ft in list(self.floating_texts):
            ft.update(dt)
            if ft.life <= 0:
                self.floating_texts.remove(ft)

    def _draw_level_up_cards(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((8, 10, 16, 220))
        self.screen.blit(overlay, (0, 0))
        title = self.font.render("LEVEL UP - Choose a card (1/2/3)", True, WHITE)
        self.screen.blit(title, title.get_rect(center=(WIDTH // 2, 140)))

        for i, (label, _) in enumerate(self.card_options, start=1):
            r = pygame.Rect(WIDTH // 2 - 220, 180 + (i - 1) * 72, 440, 52)
            pygame.draw.rect(self.screen, (40, 44, 58), r, border_radius=8)
            pygame.draw.rect(self.screen, (95, 130, 220), r, 2, border_radius=8)
            txt = self.small.render(f"{i}. {label}", True, WHITE)
            self.screen.blit(txt, (r.x + 16, r.y + 16))


    def _draw_spiritual_overlays(self):
        # Capa visual reactiva: más tensión/dificultad => más presencia cromática y simbólica
        pulse = (pygame.time.get_ticks() % 1200) / 1200.0
        alpha = int(min(120, 18 + self.difficulty * 6 + self.tension.tension_level * 7))
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((35, 14, 56, alpha))
        self.screen.blit(overlay, (0, 0))

        symbol_count = min(18, 5 + self.difficulty + int(self.tension.tension_level))
        for i in range(symbol_count):
            x = (i * 137 + pygame.time.get_ticks() // 9) % WIDTH
            y = (i * 79 + pygame.time.get_ticks() // 13) % HEIGHT
            s = self.spiritual_symbols[i % len(self.spiritual_symbols)]
            col = (170, 120 + int(80 * pulse), 220)
            txt = self.small.render(s, True, col)
            self.screen.blit(txt, (x, y))

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
                    elif self.sm.current in (GameState.RUNNING, GameState.BOSS) and e.key == pygame.K_p:
                        self.sm.set(GameState.PAUSED)
                    elif self.sm.is_state(GameState.PAUSED) and e.key == pygame.K_p:
                        self.sm.set(GameState.RUNNING)

                    if self.sm.current in (GameState.RUNNING, GameState.BOSS) and e.key in (pygame.K_LSHIFT, pygame.K_RSHIFT):
                        self.player.try_dash()
                        self.profile.register_dash()
                        self.world_memory.register_action("dash")
                    if self.sm.is_state(GameState.PAUSED) and e.key == pygame.K_r:
                        self._reset()
                    if self.sm.is_state(GameState.GAME_OVER) and e.key == pygame.K_r:
                        self._reset()
                    if self.sm.is_state(GameState.FINAL) and e.key == pygame.K_r:
                        self._reset()
                    if self.sm.is_state(GameState.LEVEL_UP):
                        if e.key in (pygame.K_1, pygame.K_KP1) and len(self.card_options) >= 1:
                            self.card_options[0][1]()
                            self.player.hp = min(self.player.max_hp, self.player.hp + 8)
                            self.sm.set(GameState.RUNNING)
                        elif e.key in (pygame.K_2, pygame.K_KP2) and len(self.card_options) >= 2:
                            self.card_options[1][1]()
                            self.player.hp = min(self.player.max_hp, self.player.hp + 8)
                            self.sm.set(GameState.RUNNING)
                        elif e.key in (pygame.K_3, pygame.K_KP3) and len(self.card_options) >= 3:
                            self.card_options[2][1]()
                            self.player.hp = min(self.player.max_hp, self.player.hp + 8)
                            self.sm.set(GameState.RUNNING)

                elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    if self.sm.current in (GameState.RUNNING, GameState.BOSS):
                        if self.player.shoot(pygame.mouse.get_pos(), self.player_bullets, self.all_sprites):
                            self.profile.register_shot()
                            self.world_memory.register_action("shoot")
                elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 3:
                    if self.sm.current in (GameState.RUNNING, GameState.BOSS):
                        if self.player.cast_secondary(self.player_bullets, self.all_sprites):
                            self.world_memory.register_action("secondary")

            if self.sm.current in (GameState.RUNNING, GameState.BOSS):
                self._update_simulation(dt)

            self.screen.fill(BG)
            for x in range(0, WIDTH, 48):
                pygame.draw.line(self.screen, GRID, (x, 0), (x, HEIGHT), 1)
            for y in range(0, HEIGHT, 48):
                pygame.draw.line(self.screen, GRID, (0, y), (WIDTH, y), 1)

            if self.sm.current in (GameState.RUNNING, GameState.BOSS, GameState.LEVEL_UP, GameState.PAUSED):
                self._draw_spiritual_overlays()

            if self.sm.is_state(GameState.MENU):
                self.menus.draw_menu(self.screen, self.font, self.small)
            else:
                self.all_sprites.draw(self.screen)
                for d in self.doors:
                    pygame.draw.rect(self.screen, d.color, d.rect)
                    label = self.small.render(d.type.value, True, WHITE)
                    self.screen.blit(label, label.get_rect(center=d.rect.center))

                for ft in self.floating_texts:
                    txt = self.small.render(ft.text, True, ft.color)
                    self.screen.blit(txt, txt.get_rect(center=(int(ft.pos.x), int(ft.pos.y))))

                self.hud.draw(
                    self.screen,
                    self.small,
                    self.player,
                    self.level,
                    self.tension.tension_level,
                    self.profile.final_evaluation(),
                    self.message,
                    len(self.enemies),
                    self.difficulty,
                )

                if self.sm.is_state(GameState.LEVEL_UP):
                    self._draw_level_up_cards()
                if self.sm.is_state(GameState.PAUSED):
                    self.menus.draw_pause(self.screen, self.font, self.small)
                if self.sm.is_state(GameState.GAME_OVER):
                    self.menus.draw_end(self.screen, self.font, self.small, "GAME OVER", "Tu sombra te venció.")
                if self.sm.is_state(GameState.FINAL):
                    self.menus.draw_end(self.screen, self.font, self.small, "FINAL", self.final_text)

            pygame.display.flip()
