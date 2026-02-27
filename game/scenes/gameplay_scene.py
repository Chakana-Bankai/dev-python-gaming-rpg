from __future__ import annotations

import pygame
from pygame.math import Vector2

from game.config import GRID, HEIGHT, WHITE, WIDTH
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
        self.tutorial_t = 0.0
        self.didactic_tips = [
            "WASD mover · Shift dash · Click izq arma · Click der limpieza",
            "Geo Fase cambia rebotes/cortes: mira el panel inferior",
            "Puertas cercanas alteran bioma y ritmo de combate",
            "Boss final muta por arquetipo: prioriza espacio y timing",
        ]

        archetype = self.ctx["state"].run.active_archetype
        if archetype == "Guerrero":
            self.gm.player.set_style((118, 168, 255), "diamond")
        elif archetype == "Testigo":
            self.gm.player.set_style((122, 230, 210), "circle")
        elif archetype == "Sombra":
            self.gm.player.set_style((178, 128, 245), "hex")

    def _handle_level_up_input(self, key):
        options = self.gm._build_levelup_options()

        if key in (pygame.K_1, pygame.K_KP1) and len(options) >= 1:
            options[0][1]()
            self.gm.player.hp = min(self.gm.player.max_hp, self.gm.player.hp + 8)
            self.gm.sm.set(GameState.RUNNING)
        elif key in (pygame.K_2, pygame.K_KP2) and len(options) >= 2:
            options[1][1]()
            self.gm.player.hp = min(self.gm.player.max_hp, self.gm.player.hp + 8)
            self.gm.sm.set(GameState.RUNNING)
        elif key in (pygame.K_3, pygame.K_KP3) and len(options) >= 3:
            options[2][1]()
            self.gm.player.hp = min(self.gm.player.max_hp, self.gm.player.hp + 8)
            self.gm.sm.set(GameState.RUNNING)

    def handle_event(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_p and self.gm.sm.current in (GameState.RUNNING, GameState.BOSS):
                self.gm.sm.set(GameState.PAUSED)
            elif e.key == pygame.K_p and self.gm.sm.is_state(GameState.PAUSED):
                self.gm.sm.set(GameState.RUNNING)

            if self.gm.sm.current in (GameState.RUNNING, GameState.BOSS) and e.key in (pygame.K_LSHIFT, pygame.K_RSHIFT):
                self.gm.player.try_dash()
                self.gm.profile.register_dash()
                self.gm.world_memory.register_action("dash")
                self.gm.audio.play_sfx("dash")
            elif self.gm.sm.is_state(GameState.LEVEL_UP):
                self._handle_level_up_input(e.key)

        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            if self.gm.sm.current in (GameState.RUNNING, GameState.BOSS):
                if self.gm.player.shoot(pygame.mouse.get_pos(), self.gm.player_bullets, self.gm.all_sprites):
                    self.gm.profile.register_shot()
                    self.gm.world_memory.register_action("shoot")
                    self.gm.audio.play_sfx("shoot")
                    self.ctx["camera"].nudge_to_shot(Vector2(pygame.mouse.get_pos()) - self.gm.player.pos)
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 3:
            if self.gm.sm.current in (GameState.RUNNING, GameState.BOSS):
                # Secundario claro: primero limpieza de mapa; poder activo solo como fallback.
                if not self.gm.player.cast_secondary(self.gm.player_bullets, self.gm.all_sprites):
                    self.gm.power_system.activate_primary_owned(self.gm)
                self.gm.world_memory.register_action("secondary")

    def update(self, dt: float):
        if self.gm.sm.current in (GameState.RUNNING, GameState.BOSS):
            self.room_timer += dt
            self.gm._update_simulation(dt)

        self.ctx["camera"].set_boss_zoom(self.gm.sm.is_state(GameState.BOSS))
        self.tutorial_t += dt

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

        if len(self.gm.enemies) == 0 and self.room_timer > 0.0:
            self.ctx["save"].register_room_time(self.room_timer)
            self.ctx["progression"].on_room_cleared()
            self.ctx["state"].run.rooms_cleared += 1
            self.room_timer = 0.0

        if self.gm.sm.is_state(GameState.GAME_OVER):
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

        for d in self.gm.doors:
            pygame.draw.rect(screen, d.color, d.rect, border_radius=6)
            pygame.draw.rect(screen, WHITE, d.rect, 2, border_radius=6)
            label = self.ctx["small"].render(d.type.value, True, WHITE)
            if d.rect.width < d.rect.height:
                lx = d.rect.right + 12 if d.rect.centerx < WIDTH // 2 else d.rect.left - 12 - label.get_width()
                ly = d.rect.centery - label.get_height() // 2
            else:
                lx = d.rect.centerx - label.get_width() // 2
                ly = d.rect.bottom + 8
            bubble = pygame.Rect(lx - 8, ly - 4, label.get_width() + 16, label.get_height() + 8)
            pygame.draw.rect(screen, (12, 14, 22), bubble, border_radius=6)
            pygame.draw.rect(screen, d.color, bubble, 1, border_radius=6)
            screen.blit(label, (lx, ly))

        for ft in self.gm.floating_texts:
            txt = self.ctx["small"].render(ft.text, True, ft.color)
            screen.blit(txt, txt.get_rect(center=(int(ft.pos.x), int(ft.pos.y))))

        self.gm.hud.draw(
            screen,
            self.ctx["small"],
            self.gm.player,
            self.gm.level,
            self.gm.tension.tension_level,
            self.gm.profile.final_evaluation(),
            self.gm.message,
            len(self.gm.enemies),
            self.gm.difficulty,
            sorted(self.gm.owned_powers),
            self.gm.power_system.get_primary_active_power_name(self.gm.owned_powers),
            self.gm.player.secondary_timer,
        )

        if self.gm.sm.is_state(GameState.LEVEL_UP):
            self.gm._draw_level_up_cards()
        elif self.gm.sm.is_state(GameState.PAUSED):
            self.gm.menus.draw_pause(screen, self.ctx["font"], self.ctx["small"])

        geo = self.gm.geometry
        geo_text = (
            f"{geo.biome_name} · Fase {geo.phase} | Reflectores {len(geo.active_reflectors)} | "
            f"Gravedad {'ON' if geo.active_gravity else 'OFF'} | Cortes {len(geo.active_cutlines)}"
        )
        geo_label = self.ctx["small"].render(geo_text, True, (205, 216, 240))
        geo_rect = geo_label.get_rect(center=(WIDTH // 2, HEIGHT - 22))
        pygame.draw.rect(screen, (8, 10, 16), geo_rect.inflate(18, 10), border_radius=7)
        screen.blit(geo_label, geo_rect)


        tip_idx = int(self.tutorial_t // 6) % len(self.didactic_tips)
        tip_text = self.didactic_tips[tip_idx]
        tip = self.ctx["small"].render(f"✧ {tip_text}", True, (220, 226, 248))
        tip_rect = pygame.Rect(WIDTH - tip.get_width() - 44, HEIGHT - 76, tip.get_width() + 20, tip.get_height() + 10)
        pygame.draw.rect(screen, (10, 12, 18), tip_rect, border_radius=7)
        pygame.draw.rect(screen, (96, 118, 190), tip_rect, 1, border_radius=7)
        screen.blit(tip, (tip_rect.x + 10, tip_rect.y + 5))

        meta = self.ctx["small"].render(
            f"◬{str(self.ctx['state'].run.seed)[-4:]} · {self.ctx['state'].run.active_archetype[:3].upper()} · λ{self.ctx['progression'].lucidez:.2f}",
            True,
            WHITE,
        )
        screen.blit(meta, (WIDTH - meta.get_width() - 24, 12))
