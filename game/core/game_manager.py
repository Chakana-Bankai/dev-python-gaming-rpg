import random
from dataclasses import dataclass

import pygame
from pygame.math import Vector2

from game.config import BG, FPS, GRID, HEIGHT, MAX_LEVELS, RED, WHITE, WIDTH, YELLOW
from game.core.state_machine import GameState, StateMachine
from game.core.tension_system import TensionSystem
from game.entities.boss import Boss, OmegaBoss
from game.entities.enemy import Enemy
from game.entities.pickup import RelicPickup
from game.entities.player import Player
from game.entities.reflection import Reflection
from game.systems.audio_system import AudioSystem
from game.systems.door_system import DoorSystem
from game.systems.geometry_system import GeometrySystem
from game.systems.mirror_mode import MirrorMode
from game.systems.power_system import PowerSystem
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
    def __init__(self, screen, audio: AudioSystem | None = None):
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("consolas", 22)
        self.small = pygame.font.SysFont("consolas", 16)
        self.symbol_font = pygame.font.SysFont("segoeuisymbol,dejavusans,arial", 16)

        self.sm = StateMachine()
        self.tension = TensionSystem()
        self.world_memory = WorldMemory()
        self.profile = PsychologicalProfile()
        self.door_system = DoorSystem()
        self.mirror_mode = MirrorMode()
        self.audio = audio or AudioSystem()
        self.power_system = PowerSystem()
        self.geometry = GeometrySystem()

        self.hud = HUD()
        self.menus = Menus()

        self.all_sprites = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.player_bullets = pygame.sprite.Group()
        self.pickups = pygame.sprite.Group()

        self.player = Player(Vector2(WIDTH // 2, HEIGHT // 2))
        self.all_sprites.add(self.player)

        self.level = 1
        self.difficulty = 1
        self.doors = []
        self.message = ""
        self.final_text = ""
        self.spawn_reflection_next = False
        self.door_history: list[str] = []
        self.secret_unlocked = False
        self.sacred_key = False
        self.spawn_angel_next = False
        self.pending_door = None
        self.door_decisions = []
        self.pause_options = ["Resume", "Audio: ON", "Music Vol +", "Music Vol -", "Restart Run", "Quit"]
        self.pause_selected = 0
        self.damage_taken = 0.0
        self.consecutive_hits = 0
        self.focus_accumulator = Vector2(self.player.pos)
        self.focus_samples = 1

        self.card_options = []
        self.power_options = []
        self.owned_powers: set[str] = set()

        self.base_player_damage = self.player.damage
        self.base_player_speed = self.player.speed
        self.base_player_pierce = self.player.pierce

        self.time_since_last_shot = 0.0
        self.kill_streak = 0
        self.mirror_skin_chance = 0.0
        self.echo_shot_timer = 0.0
        self.rift_trail_timer = 0.0
        self.silence_field_timer = 0.0
        self.invert_timer = 0.0
        self.entropy_mult = 1.0

        self.door_lock_timer = 0.0
        self.floating_texts = []
        self.spiritual_symbols = ["✦", "☾", "∆", "☉", "⚚"]

        self.final_freeze_timer = 0.0

    def _weapon_label(self) -> str:
        if not self.player.weapon_modes:
            return "Pulse"
        priority = ["helix", "prism", "sigil", "chaos", "triple", "fan_shot", "cross_shot", "spiral"]
        for mode in priority:
            if mode in self.player.weapon_modes:
                return mode.replace("_", " ").title()
        return sorted(self.player.weapon_modes)[0].replace("_", " ").title()

    def apply_pause_option(self):
        choice = self.pause_options[self.pause_selected]
        if choice.startswith("Resume"):
            self.sm.set(GameState.RUNNING)
        elif choice.startswith("Audio"):
            mute = "ON" in choice
            self.audio.set_muted(mute)
            self.pause_options[1] = "Audio: OFF" if mute else "Audio: ON"
            if not mute:
                self.audio.play_music("gameplay")
        elif choice.startswith("Music Vol +"):
            self.audio.set_mix_gain(self.audio.mix_gain + 0.1)
        elif choice.startswith("Music Vol -"):
            self.audio.set_mix_gain(self.audio.mix_gain - 0.1)
        elif choice.startswith("Restart"):
            self._reset_to_menu()
        elif choice.startswith("Quit"):
            pygame.event.post(pygame.event.Event(pygame.QUIT))

        self._spawn_level()
        self.sm.set(GameState.MENU)
        self.audio.play_music("menu")

    def _roll_cards(self):
        p = self.player

        def _inc_damage(amount: float):
            self.base_player_damage += amount
            p.damage = self.base_player_damage

        stat_pool = [
            ("+25 HP max", lambda: setattr(p, "max_hp", p.max_hp + 25)),
            ("+4 Damage", lambda: _inc_damage(4)),
            ("Mode: Triple", lambda: p.weapon_modes.add("triple")),
            ("Mode: Fan Shot", lambda: p.weapon_modes.add("fan_shot")),
            ("Mode: Cross Shot", lambda: p.weapon_modes.add("cross_shot")),
            ("Mode: Chaos", lambda: p.weapon_modes.add("chaos")),
            ("Mode: Spiral", lambda: p.weapon_modes.add("spiral")),
            ("Mode: Rapid Fire", lambda: p.weapon_modes.add("rapid_fire")),
            ("Mode: Nova+", lambda: p.weapon_modes.add("nova_plus")),
            ("Mode: Storm Crit", lambda: p.weapon_modes.add("storm_crit")),
            ("Mode: Sigil", lambda: p.weapon_modes.add("sigil")),
            ("Mode: Lattice", lambda: p.weapon_modes.add("lattice")),
            ("Mode: Prism", lambda: p.weapon_modes.add("prism")),
            ("Mode: Helix", lambda: p.weapon_modes.add("helix")),
        ]
        random.shuffle(stat_pool)
        self.card_options = stat_pool[:2]
        self.power_options = self.power_system.roll_power_cards(self.owned_powers, n=1)

    def _build_levelup_options(self):
        options = list(self.card_options)
        if self.power_options:
            power = self.power_options[0]
            label = f"Power: {power.name} [{power.rarity}] - {self.power_system.describe(power.name)}"
            options.append((label, lambda: self.owned_powers.add(power.name)))
        return options

    def _spawn_level(self):
        for g in (self.enemies, self.player_bullets, self.pickups):
            for s in list(g):
                s.kill()
        self.doors.clear()
        self.door_lock_timer = 0.65
        self.player.pos = Vector2(WIDTH // 2, HEIGHT // 2)
        self.player.rect.center = (int(self.player.pos.x), int(self.player.pos.y))
        self.consecutive_hits = 0
        self.focus_accumulator = Vector2(self.player.pos)
        self.focus_samples = 1
        self.geometry.randomize_biome(self.level, self.difficulty, self.door_history[-1] if self.door_history else None)

        if self.level in (3, 6, 8):
            self.sm.set(GameState.BOSS)
            self.audio.play_sfx("boss_spawn")
            if self.level == 8:
                boss = OmegaBoss(Vector2(WIDTH // 2, 120), self.difficulty)
                self.message = f"☠ OMEGA FINAL [{boss.variant}]: el abismo te mira de vuelta."
            elif self.spawn_reflection_next:
                style = self.mirror_mode.infer_style(self.world_memory.data.get("action_buffer", []))
                boss = Reflection(Vector2(WIDTH // 2, 140), style)
                self.spawn_reflection_next = False
                self.message = "∆ El reflejo aprende tus pasos."
            else:
                boss = Boss(Vector2(WIDTH // 2, 120), self.level, player=self.player)
                self.message = f"☠ Boss {self.level}: {boss.kind.upper()}"
            self.enemies.add(boss)
            self.all_sprites.add(boss)
            self.audio.play_music("gameplay")
            return

        if self.spawn_angel_next:
            self.spawn_angel_next = False
            self.sm.set(GameState.BOSS)
            self.audio.play_sfx("boss_spawn")
            angel = Boss(Vector2(WIDTH // 2, 120), self.level + 2, player=self.player)
            angel.kind = "Angelus"
            angel.image.fill((245, 238, 170))
            angel.damage *= 1.18
            angel.speed *= 1.12
            self.enemies.add(angel)
            self.all_sprites.add(angel)
            self.message = "✞ ANGELUS desciende: juicio sagrado activado."
            self.audio.play_music("gameplay")
            return

        self.sm.set(GameState.RUNNING)
        count = min(34, 8 + self.difficulty + random.randint(2, 8))
        for _ in range(count):
            p = Vector2(random.randint(40, WIDTH - 40), random.randint(40, HEIGHT - 40))
            kind_roll = random.random()
            kind = "chaser" if kind_roll < 0.45 else "rusher" if kind_roll < 0.78 else "tank"
            e = Enemy(p, 20 + self.difficulty * 2.8, 92 + self.difficulty * 4, 9 + self.difficulty, kind=kind)
            if random.random() < min(0.26, 0.06 + self.level * 0.02):
                e.promote_elite("elite")
            if random.random() < min(0.10, 0.015 * self.level):
                e.promote_elite("chaos")
                self.message = "☣ Enemigo caótico detectado"
            self.enemies.add(e)
            self.all_sprites.add(e)
        if random.random() < 0.42:
            relic = RelicPickup(Vector2(random.randint(220, WIDTH - 220), random.randint(180, HEIGHT - 220)))
            self.pickups.add(relic)
            self.all_sprites.add(relic)
        self.audio.play_music("gameplay")

    def _advance(self):
        if self.level >= MAX_LEVELS:
            archetype = self.profile.final_evaluation()
            self.world_memory.complete_run(self.level, archetype)
            distortion = self.world_memory.data.get("permanent_distortion_level", 0.0)
            self.final_text = (
                f"ARCHETYPE: {archetype} | WORLD DISTORTION: {distortion:.2f} | "
                f"RUNS: {self.world_memory.data.get('runs', 0)} | "
                f"RUPTURAS: {self.world_memory.data.get('total_rupturas', 0)} | "
                f"INTEGRACIONES: {self.world_memory.data.get('total_integraciones', 0)}"
            )
            self.final_freeze_timer = 1.0
            self.sm.set(GameState.FINAL)
            self.audio.stop_music()
            self.audio.play_final(archetype)
            return
        self.level += 1
        self._spawn_level()

    def _build_door_decisions(self, door):
        def risk_path():
            self.difficulty += 2
            self.base_player_damage += 1.5
            self.player.hp = min(self.player.max_hp, self.player.hp + 10)
            self.geometry.set_fragmentation(True)

        def ritual_path():
            self.difficulty = max(1, self.difficulty - 1)
            self.player.fire_cd = max(0.07, self.player.fire_cd * 0.9)
            self.player.crit_bonus += 0.04
            self.geometry.set_fragmentation(door.type.name in ("SHADOW", "SACRED"))

        return [
            ("1) Desafiar (+dificultad, +daño, bioma fracturado)", risk_path),
            ("2) Ritual (+cadencia, +crit, atmósfera estable)", ritual_path),
        ]

    def choose_door_decision(self, idx: int):
        if self.pending_door is None or idx >= len(self.door_decisions):
            return
        self.door_decisions[idx][1]()
        d = self.pending_door
        self.pending_door = None
        self.message = self.door_system.apply(d.type, self)
        self.geometry.set_door_theme(d.type.name)
        self.door_history.append(d.type.name)
        if len(self.door_history) > 5:
            self.door_history = self.door_history[-5:]
        if self.door_history[-3:] == ["SHADOW", "CONFLICT", "ASCENT"] and not self.secret_unlocked:
            self.secret_unlocked = True
            self.sacred_key = True
            self.message = "🗝 Llave Sagrada obtenida: se revelará un umbral inferior."
            self.difficulty += 2
            self.player.max_hp += 20
            self.player.hp = min(self.player.max_hp, self.player.hp + 20)
        if d.type.name == "SACRED":
            self.spawn_angel_next = True
        self.sm.set(GameState.RUNNING)
        self._advance()

    def _reset_to_menu(self):
        self.__init__(self.screen, audio=self.audio)

    def _on_enemy_killed(self, enemy):
        xp = 60 if isinstance(enemy, OmegaBoss) else 35 if isinstance(enemy, (Boss, Reflection)) else 10 + self.difficulty
        self.kill_streak += 1
        if self.player.gain_exp(xp):
            self._roll_cards()
            self.sm.set(GameState.LEVEL_UP)
            self.audio.play_sfx("level_up")

    def _update_power_timers(self, dt: float):
        self.time_since_last_shot += dt
        self.echo_shot_timer = max(0.0, self.echo_shot_timer - dt)
        self.rift_trail_timer = max(0.0, self.rift_trail_timer - dt)
        self.silence_field_timer = max(0.0, self.silence_field_timer - dt)
        self.invert_timer = max(0.0, self.invert_timer - dt)

    def _update_simulation(self, dt: float):
        self._update_power_timers(dt)
        self.door_lock_timer = max(0.0, self.door_lock_timer - dt)

        # reset derived base every frame before passive powers
        self.player.damage = self.base_player_damage
        self.player.speed = self.base_player_speed
        self.player.pierce = self.base_player_pierce
        self.mirror_skin_chance = 0.0
        self.entropy_mult = 1.0

        self.power_system.apply_passives(self, dt)

        # coherencia de daño: multiplica por entropía y limita picos extremos
        target_damage = self.player.damage * self.entropy_mult
        cap = self.base_player_damage * 2.1 + self.level * 1.2
        self.player.damage = max(self.base_player_damage * 0.75, min(cap, target_damage))

        keys = pygame.key.get_pressed()
        invert = any(isinstance(e, Reflection) for e in self.enemies) or self.invert_timer > 0
        self.player.move_input(keys, invert=invert)
        self.player.update(dt)

        boss_ref = None
        for e in list(self.enemies):
            if isinstance(e, (Boss, OmegaBoss)):
                boss_ref = e

        if boss_ref:
            hp_ratio = boss_ref.hp / boss_ref.max_hp if boss_ref.max_hp else 0
            if self.geometry.request_phase_from_boss(hp_ratio):
                self.audio.play_sfx("geom_phase_shift")

        for e in list(self.enemies):
            if isinstance(e, OmegaBoss):
                prev_phase = e.phase
                e.update(dt, self.player.pos, self.player, self.world_memory.data.get("action_buffer", []), self.geometry.get_context_for_boss())
                if e.phase != prev_phase:
                    self.tension.tension_level = min(10.0, self.tension.tension_level + 1.0)
                    self.audio.play_sfx("geom_phase_shift")
                if e.phase >= 3:
                    for f in e.split_fragments():
                        self.enemies.add(f)
                        self.all_sprites.add(f)
            elif isinstance(e, Boss):
                e.update(dt, self.player.pos, self.geometry.get_context_for_boss())
            else:
                e.update(dt, self.player.pos)

        self.player_bullets.update(dt)
        self.focus_accumulator += self.player.pos
        self.focus_samples += 1

        self.geometry.update(
            dt,
            self.player,
            boss_ref,
            self.player_bullets,
            self.world_memory.data,
            self.consecutive_hits,
            self.focus_accumulator / max(1, self.focus_samples),
            self._apply_cutline_damage,
            self.audio,
        )

        # silence field: enemies can't hit while active by contact reduction
        contact_scale = 0.0 if self.silence_field_timer > 0 else 1.0

        hits = pygame.sprite.groupcollide(self.enemies, self.player_bullets, False, False)
        for enemy, bullets in hits.items():
            for b in bullets:
                self.floating_texts.append(FloatingText(str(int(b.damage)), Vector2(enemy.rect.center), YELLOW))
                self.audio.play_sfx("damage")
                if enemy.take_damage(b.damage):
                    self.profile.register_room_clear()
                    self._on_enemy_killed(enemy)

                if self.player.lifesteal > 0:
                    self.player.hp = min(self.player.max_hp, self.player.hp + b.damage * self.player.lifesteal * 0.15)

                if b.pierce > 0:
                    b.pierce -= 1
                else:
                    b.kill()

        for relic in pygame.sprite.spritecollide(self.player, self.pickups, dokill=True):
            bonus = relic.apply(self)
            self.message = f"◆ Reliquia {relic.name} [{relic.rarity.upper()}]: {bonus}"
            self.floating_texts.append(FloatingText(f"{relic.name}", Vector2(self.player.rect.center), (140, 240, 220)))

        for e in pygame.sprite.spritecollide(self.player, self.enemies, False):
            if self.player.hp > 0:
                delta = e.damage * dt * 4.0 * contact_scale
                if random.random() < self.mirror_skin_chance:
                    e.take_damage(delta * 1.5)
                self.player.hp -= delta
                self.damage_taken += delta
                self.profile.register_hit_taken()
                self.audio.play_sfx("damage")
                self.floating_texts.append(FloatingText(f"-{int(delta)}", Vector2(self.player.rect.center), RED))
                self.consecutive_hits += 1
            if self.player.hp <= 0:
                self.world_memory.complete_run(self.level, "Overlord")
                self.sm.set(GameState.GAME_OVER)

        if not pygame.sprite.spritecollide(self.player, self.enemies, False):
            self.consecutive_hits = 0

        if len(self.enemies) == 0 and not self.doors:
            self.doors = self.door_system.create_doors(sacred_unlocked=self.sacred_key)
            self.kill_streak = 0

        if self.door_lock_timer <= 0:
            for d in self.doors:
                if self.player.rect.colliderect(d.rect):
                    self.pending_door = d
                    self.door_decisions = self._build_door_decisions(d)
                    self.sm.set(GameState.DOOR_CHOICE)
                    break

        self.tension.update(self.player.shots_fired, self.damage_taken, len(self.enemies), dt)
        boss_ratio = boss_ref.hp / boss_ref.max_hp if boss_ref else None
        self.audio.update_dynamic(self.tension.tension_level, boss_ratio)

        for ft in list(self.floating_texts):
            ft.update(dt)
            if ft.life <= 0:
                self.floating_texts.remove(ft)

    def _draw_level_up_cards(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((8, 10, 16, 220))
        self.screen.blit(overlay, (0, 0))
        title = self.font.render("LEVEL UP - Choose (1/2/3)", True, WHITE)
        self.screen.blit(title, title.get_rect(center=(WIDTH // 2, 140)))

        options = self._build_levelup_options()

        for i, (label, _) in enumerate(options[:3], start=1):
            r = pygame.Rect(WIDTH // 2 - 220, 180 + (i - 1) * 72, 440, 52)
            pygame.draw.rect(self.screen, (40, 44, 58), r, border_radius=8)
            pygame.draw.rect(self.screen, (95, 130, 220), r, 2, border_radius=8)
            txt = self.small.render(f"{i}. {label}", True, WHITE)
            self.screen.blit(txt, (r.x + 16, r.y + 16))

    def _draw_spiritual_overlays(self):
        pulse = (pygame.time.get_ticks() % 1200) / 1200.0
        alpha = int(min(140, 18 + self.difficulty * 6 + self.tension.tension_level * 8 + self.world_memory.data.get("permanent_distortion_level", 0) * 80))
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((35, 14, 56, alpha))
        self.screen.blit(overlay, (0, 0))

        symbol_count = min(22, 5 + self.difficulty + int(self.tension.tension_level))
        for i in range(symbol_count):
            x = (i * 137 + pygame.time.get_ticks() // 9) % WIDTH
            y = (i * 79 + pygame.time.get_ticks() // 13) % HEIGHT
            s = self.spiritual_symbols[i % len(self.spiritual_symbols)]
            col = (170, 120 + int(80 * pulse), 220)
            txt = self.symbol_font.render(s, True, col)
            self.screen.blit(txt, (x, y))

    def _apply_cutline_damage(self, amount: float):
        self.player.hp -= amount
        self.damage_taken += amount
        self.profile.register_hit_taken()
        self.audio.play_sfx("damage")
        self.floating_texts.append(FloatingText(f"-{int(amount)}", Vector2(self.player.rect.center), RED))

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
                        self.audio.play_music("gameplay")
                    elif self.sm.current in (GameState.RUNNING, GameState.BOSS) and e.key == pygame.K_p:
                        self.sm.set(GameState.PAUSED)
                    elif self.sm.is_state(GameState.PAUSED) and e.key == pygame.K_p:
                        self.sm.set(GameState.RUNNING)

                    if self.sm.current in (GameState.RUNNING, GameState.BOSS) and e.key in (pygame.K_LSHIFT, pygame.K_RSHIFT):
                        self.player.try_dash()
                        self.profile.register_dash()
                        self.world_memory.register_action("dash")
                        self.audio.play_sfx("dash")
                    if self.sm.is_state(GameState.PAUSED) and e.key == pygame.K_r:
                        self._reset_to_menu()
                    if self.sm.is_state(GameState.GAME_OVER) and e.key == pygame.K_r:
                        self._reset_to_menu()
                    if self.sm.is_state(GameState.FINAL) and e.key == pygame.K_r:
                        self._reset_to_menu()
                    if self.sm.is_state(GameState.LEVEL_UP):
                        options = self._build_levelup_options()
                        if e.key in (pygame.K_1, pygame.K_KP1) and len(options) >= 1:
                            options[0][1]()
                            self.player.hp = min(self.player.max_hp, self.player.hp + 8)
                            self.sm.set(GameState.RUNNING)
                        elif e.key in (pygame.K_2, pygame.K_KP2) and len(options) >= 2:
                            options[1][1]()
                            self.player.hp = min(self.player.max_hp, self.player.hp + 8)
                            self.sm.set(GameState.RUNNING)
                        elif e.key in (pygame.K_3, pygame.K_KP3) and len(options) >= 3:
                            options[2][1]()
                            self.player.hp = min(self.player.max_hp, self.player.hp + 8)
                            self.sm.set(GameState.RUNNING)

                elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    if self.sm.current in (GameState.RUNNING, GameState.BOSS):
                        if self.player.shoot(pygame.mouse.get_pos(), self.player_bullets, self.all_sprites):
                            self.profile.register_shot()
                            self.world_memory.register_action("shoot")
                            self.audio.play_sfx("shoot")
                            self.time_since_last_shot = 0.0
                            if self.echo_shot_timer > 0:
                                self.player.shoot(pygame.mouse.get_pos(), self.player_bullets, self.all_sprites)
                elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 3:
                    if self.sm.current in (GameState.RUNNING, GameState.BOSS):
                        if not self.player.cast_secondary(self.player_bullets, self.all_sprites):
                            self.power_system.activate_primary_owned(self)
                        self.world_memory.register_action("secondary")
                        self.audio.play_sfx("dash")

            if self.sm.current in (GameState.RUNNING, GameState.BOSS):
                self._update_simulation(dt)

            if self.sm.is_state(GameState.FINAL) and self.final_freeze_timer > 0:
                self.final_freeze_timer = max(0.0, self.final_freeze_timer - dt)

            # Draw
            self.screen.fill(BG)
            for x in range(0, WIDTH, 48):
                pygame.draw.line(self.screen, GRID, (x, 0), (x, HEIGHT), 1)
            for y in range(0, HEIGHT, 48):
                pygame.draw.line(self.screen, GRID, (0, y), (WIDTH, y), 1)

            if self.sm.current in (GameState.RUNNING, GameState.BOSS, GameState.LEVEL_UP, GameState.PAUSED, GameState.FINAL):
                self._draw_spiritual_overlays()

            if self.sm.is_state(GameState.MENU):
                distortion = self.world_memory.data.get("permanent_distortion_level", 0.0)
                tint = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                tint.fill((70, 20, 80, int(120 * distortion)))
                self.screen.blit(tint, (0, 0))
                self.menus.draw_menu(self.screen, self.font, self.small)
            else:
                self.geometry.draw(self.screen)
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
                    sorted(self.owned_powers),
                    self.power_system.get_primary_active_power_name(self.owned_powers),
                    self.player.secondary_timer,
                    self._weapon_label(),
                    self.sacred_key,
                )

                if self.sm.is_state(GameState.LEVEL_UP):
                    self._draw_level_up_cards()
                if self.sm.is_state(GameState.PAUSED):
                    self.menus.draw_pause(self.screen, self.font, self.small)
                if self.sm.is_state(GameState.GAME_OVER):
                    self.menus.draw_end(self.screen, self.font, self.small, "GAME OVER", "Tu sombra te venció.")
                if self.sm.is_state(GameState.FINAL):
                    self.menus.draw_end(self.screen, self.font, self.small, "ARCHETYPE RESOLUTION", self.final_text)

            pygame.display.flip()
