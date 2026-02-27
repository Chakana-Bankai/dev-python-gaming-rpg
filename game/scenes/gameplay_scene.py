from __future__ import annotations

import pygame
from pygame.math import Vector2

from game.config import BG, GRID, HEIGHT, WHITE, WIDTH
from game.core.game_manager import GameManager
from game.core.state_machine import GameState
from game.scenes.base_scene import BaseScene
from game.scenes.ending_scene import EndingScene


class GameplayScene(BaseScene):
    def __init__(self, ctx: dict):
        super().__init__(ctx)
        self.gm = ctx.get("gm")
        if self.gm is None:
            self.gm = GameManager(ctx["screen"], audio=ctx["audio"])
            self.gm.sm.set(GameState.RUNNING)
            self.gm.audio.play_music("gameplay")
            ctx["gm"] = self.gm
        self.room_timer = 0.0
        self.last_floating_count = 0

    def handle_event(self, e):
        if e.type == pygame.KEYDOWN and e.key in (pygame.K_LSHIFT, pygame.K_RSHIFT):
            self.gm.player.try_dash()
            self.gm.profile.register_dash()
            self.gm.world_memory.register_action("dash")
            self.gm.audio.play_sfx("dash")
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            if self.gm.player.shoot(pygame.mouse.get_pos(), self.gm.player_bullets, self.gm.all_sprites):
                self.gm.profile.register_shot()
                self.gm.world_memory.register_action("shoot")
                self.gm.audio.play_sfx("shoot")
                self.ctx["camera"].nudge_to_shot(Vector2(pygame.mouse.get_pos()) - self.gm.player.pos)
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 3:
            if not self.gm.power_system.activate_random_owned(self.gm):
                self.gm.player.cast_secondary(self.gm.player_bullets, self.gm.all_sprites)
            self.gm.world_memory.register_action("secondary")

    def update(self, dt: float):
        self.room_timer += dt
        self.gm._update_simulation(dt)
        self.ctx["camera"].set_boss_zoom(self.gm.sm.is_state(GameState.BOSS))

        if len(self.gm.floating_texts) > self.last_floating_count:
            self.ctx["particles"].spawn_impact(self.gm.player.pos)
            self.ctx["camera"].add_shake(0.4)
        self.last_floating_count = len(self.gm.floating_texts)

        self.ctx["particles"].update(dt)
        self.ctx["camera"].update(dt)

        shots = max(1, self.gm.player.shots_fired)
        precision = min(1.0, (self.gm.kill_streak + 1) / shots)
        damage_taken_rate = min(1.0, self.gm.damage_taken / max(1.0, self.gm.player.max_hp))
        self.ctx["difficulty"].evaluate(precision, damage_taken_rate, self.room_timer)

        if len(self.gm.enemies) == 0:
            self.ctx["save"].register_room_time(self.room_timer)
            self.ctx["progression"].on_room_cleared()
            self.ctx["state"].run.rooms_cleared += 1
            self.room_timer = 0.0

        if self.gm.sm.is_state(GameState.BOSS):
            from game.scenes.boss_scene import BossScene

            self._next = BossScene(self.ctx)
        elif self.gm.sm.is_state(GameState.GAME_OVER):
            self.ctx["state"].run.finished = True
            self.ctx["state"].run.victory = False
            self._next = EndingScene(self.ctx)
        elif self.gm.sm.is_state(GameState.FINAL):
            self.ctx["state"].run.finished = True
            self.ctx["state"].run.victory = True
            self._next = EndingScene(self.ctx)

    def render(self, screen):
        palette = self.ctx["progression"].palette()
        screen.fill(palette["bg"])
        for x in range(0, WIDTH, 48):
            pygame.draw.line(screen, GRID, (x, 0), (x, HEIGHT), 1)
        for y in range(0, HEIGHT, 48):
            pygame.draw.line(screen, GRID, (0, y), (WIDTH, y), 1)

        self.gm._draw_spiritual_overlays()
        self.gm.geometry.draw(screen)
        self.gm.all_sprites.draw(screen)
        self.ctx["particles"].draw(screen)

        self.gm.hud.draw(
            screen,
            self.ctx["small"],
            self.gm.player,
            self.gm.level,
            self.gm.tension.tension_level,
            self.gm.profile.final_evaluation(),
            f"Estado: {self.ctx['progression'].symbolic_state} | Seed: {self.ctx['state'].run.seed}",
            len(self.gm.enemies),
            self.gm.difficulty,
            sorted(self.gm.owned_powers),
        )

        meta = self.ctx["small"].render(
            f"Arquetipo: {self.ctx['state'].run.active_archetype}  Lucidez: {self.ctx['progression'].lucidez:.2f}",
            True,
            WHITE,
        )
        screen.blit(meta, (12, 12))
