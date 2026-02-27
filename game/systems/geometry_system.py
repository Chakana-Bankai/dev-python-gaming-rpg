from __future__ import annotations

import random
from dataclasses import dataclass

import pygame
from pygame.math import Vector2

from game.config import HEIGHT, WIDTH


@dataclass
class PhaseConfig:
    reflectors: list[dict]
    gravity_zone: dict | None
    cut_lines: list[dict]
    global_rotation_speed: float | None = None
    space_shrink: int = 0


class ReflectiveTriangle:
    def __init__(self):
        self.active = False
        self.center = Vector2()
        self.radius = 56
        self.rotation = 0.0

    def configure(self, center: Vector2, rotation: float):
        self.active = True
        self.center = Vector2(center)
        self.rotation = rotation

    def deactivate(self):
        self.active = False

    def points(self) -> list[Vector2]:
        base = Vector2(0, -self.radius)
        return [self.center + base.rotate(self.rotation + i * 120) for i in range(3)]

    def aabb(self) -> pygame.Rect:
        pts = self.points()
        xs = [p.x for p in pts]
        ys = [p.y for p in pts]
        return pygame.Rect(min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)).inflate(8, 8)


class GravityZone:
    def __init__(self):
        self.active = False
        self.center = Vector2()
        self.radius = 100.0
        self.slow_pct = 0.25

    def configure(self, center: Vector2, radius: float, slow_pct: float):
        self.active = True
        self.center = Vector2(center)
        self.radius = radius
        self.slow_pct = slow_pct

    def deactivate(self):
        self.active = False

    def aabb(self) -> pygame.Rect:
        return pygame.Rect(self.center.x - self.radius, self.center.y - self.radius, self.radius * 2, self.radius * 2)


class CutLine:
    def __init__(self):
        self.active = False
        self.a = Vector2()
        self.b = Vector2()

    def configure(self, a: Vector2, b: Vector2):
        self.active = True
        self.a = Vector2(a)
        self.b = Vector2(b)

    def deactivate(self):
        self.active = False

    def aabb(self) -> pygame.Rect:
        r = pygame.Rect(min(self.a.x, self.b.x), min(self.a.y, self.b.y), abs(self.a.x - self.b.x) + 1, abs(self.a.y - self.b.y) + 1)
        return r.inflate(8, 8)


class GeometrySystem:
    def __init__(self):
        self.arena_bounds = pygame.Rect(80, 80, WIDTH - 160, HEIGHT - 160)
        self.phase = 1
        self.phase_configs = {
            1: PhaseConfig(
                reflectors=[{"center": Vector2(250, 240), "rotation": 0}],
                gravity_zone=None,
                cut_lines=[{"a": Vector2(430, 130), "b": Vector2(530, 260)}],
            ),
            2: PhaseConfig(
                reflectors=[{"center": Vector2(230, 210), "rotation": 25}, {"center": Vector2(600, 360), "rotation": 210}],
                gravity_zone={"center": Vector2(WIDTH / 2, HEIGHT / 2), "radius": 120, "slow_pct": 0.32},
                cut_lines=[{"a": Vector2(120, 350), "b": Vector2(260, 470)}],
                global_rotation_speed=11,
            ),
            3: PhaseConfig(
                reflectors=[{"center": Vector2(190, 180), "rotation": 35}, {"center": Vector2(640, 190), "rotation": 170}],
                gravity_zone={"center": Vector2(WIDTH / 2 - 40, HEIGHT / 2 + 30), "radius": 130, "slow_pct": 0.36},
                cut_lines=[{"a": Vector2(260, 130), "b": Vector2(260, 500)}, {"a": Vector2(620, 130), "b": Vector2(620, 500)}],
                global_rotation_speed=18,
                space_shrink=20,
            ),
        }
        self.reflector_pool = [ReflectiveTriangle() for _ in range(3)]
        self.cutline_pool = [CutLine() for _ in range(2)]
        self.gravity_pool = [GravityZone()]
        self.transitioning = False
        self.transition_t = 0.0
        self.transition_len = 1.0
        self.start_positions: dict[int, tuple[Vector2, float]] = {}
        self.target_positions: dict[int, tuple[Vector2, float]] = {}
        self.micro_adjust_cd = 0.0
        self.global_rotation = 0.0
        self.visual_pulse = 0.0
        self._last_gravity_entries: set[int] = set()
        self._hash: dict[tuple[int, int], list[tuple[str, object]]] = {}
        self.biome_name = "Antechamber"

        self.apply_phase_config(self.phase_configs[1], Vector2(WIDTH // 2, HEIGHT // 2), instant=True)

    def randomize_biome(self, level: int, difficulty: int, last_door: str | None):
        """Varia geometría base por sala para evitar repetición de bioma."""
        biome = random.choice(["Cathedral", "Forge", "Labyrinth", "Sanctum"])
        if last_door == "SHADOW":
            biome = random.choice(["Labyrinth", "Cathedral"])
        elif last_door == "CONFLICT":
            biome = random.choice(["Forge", "Labyrinth"])
        elif last_door == "ASCENT":
            biome = random.choice(["Sanctum", "Cathedral"])
        self.biome_name = biome

        cx, cy = WIDTH / 2, HEIGHT / 2
        jitter = min(90, 35 + level * 3 + difficulty * 2)

        if biome == "Forge":
            self.phase_configs[1] = PhaseConfig(
                reflectors=[{"center": Vector2(cx - 170, cy - 70), "rotation": 16}],
                gravity_zone=None,
                cut_lines=[{"a": Vector2(cx - 260, cy - 180), "b": Vector2(cx + 230, cy + 120)}],
                global_rotation_speed=14,
            )
            self.phase_configs[2].gravity_zone = {"center": Vector2(cx + 35, cy), "radius": 128, "slow_pct": 0.30}
        elif biome == "Labyrinth":
            self.phase_configs[1] = PhaseConfig(
                reflectors=[{"center": Vector2(cx - 230, cy), "rotation": 0}, {"center": Vector2(cx + 230, cy), "rotation": 180}],
                gravity_zone=None,
                cut_lines=[{"a": Vector2(cx - 80, cy - 220), "b": Vector2(cx - 80, cy + 220)}],
            )
            self.phase_configs[2].cut_lines = [
                {"a": Vector2(cx - 260, cy - 120), "b": Vector2(cx + 120, cy - 120)},
                {"a": Vector2(cx - 120, cy + 120), "b": Vector2(cx + 260, cy + 120)},
            ]
        elif biome == "Sanctum":
            self.phase_configs[1] = PhaseConfig(
                reflectors=[{"center": Vector2(cx, cy - 180), "rotation": 0}],
                gravity_zone={"center": Vector2(cx, cy), "radius": 110, "slow_pct": 0.24},
                cut_lines=[],
            )
            self.phase_configs[2].reflectors = [
                {"center": Vector2(cx - 190, cy), "rotation": 28},
                {"center": Vector2(cx + 190, cy), "rotation": 208},
            ]
        else:  # Cathedral
            self.phase_configs[1] = PhaseConfig(
                reflectors=[{"center": Vector2(cx - 160, cy - 110), "rotation": 24}],
                gravity_zone=None,
                cut_lines=[{"a": Vector2(cx + 70, cy - 220), "b": Vector2(cx + 70, cy + 220)}],
            )
            self.phase_configs[2].gravity_zone = {"center": Vector2(cx, cy + 40), "radius": 124, "slow_pct": 0.31}

        # Pequeña variación procedural por sala.
        for cfg in self.phase_configs.values():
            for ref in cfg.reflectors:
                ref["center"] = Vector2(
                    max(self.arena_bounds.left + 80, min(self.arena_bounds.right - 80, ref["center"].x + random.uniform(-jitter, jitter))),
                    max(self.arena_bounds.top + 80, min(self.arena_bounds.bottom - 80, ref["center"].y + random.uniform(-jitter, jitter))),
                )

        self.apply_phase_config(self.phase_configs[1], Vector2(WIDTH // 2, HEIGHT // 2), instant=True)

    @property
    def active_reflectors(self):
        return [r for r in self.reflector_pool if r.active]

    @property
    def active_cutlines(self):
        return [c for c in self.cutline_pool if c.active]

    @property
    def active_gravity(self):
        return self.gravity_pool[0] if self.gravity_pool[0].active else None

    def request_phase_from_boss(self, boss_hp_ratio: float):
        target = 3 if boss_hp_ratio <= 0.33 else 2 if boss_hp_ratio <= 0.66 else 1
        if target > self.phase and not self.transitioning:
            self.start_transition(target)
            return True
        return False

    def start_transition(self, target_phase: int):
        self.transitioning = True
        self.transition_t = 0.0
        self.transition_len = random.uniform(0.8, 1.2)
        cfg = self.phase_configs[target_phase]
        self.target_phase = target_phase
        self.start_positions.clear()
        self.target_positions.clear()

        for i, refl in enumerate(self.reflector_pool):
            if refl.active:
                self.start_positions[i] = (Vector2(refl.center), refl.rotation)
            t = cfg.reflectors[i] if i < len(cfg.reflectors) else None
            if t:
                self.target_positions[i] = (Vector2(t["center"]), float(t["rotation"]))

    def apply_phase_config(self, cfg: PhaseConfig, player_pos: Vector2, instant=False):
        for i, refl in enumerate(self.reflector_pool):
            if i < len(cfg.reflectors):
                data = cfg.reflectors[i]
                center = Vector2(data["center"])
                if center.distance_to(player_pos) < 70:
                    center += Vector2(80, 0)
                refl.configure(center, float(data["rotation"]))
            else:
                refl.deactivate()

        g = self.gravity_pool[0]
        if cfg.gravity_zone:
            gd = cfg.gravity_zone
            g.configure(Vector2(gd["center"]), gd["radius"], gd["slow_pct"])
        else:
            g.deactivate()

        for i, line in enumerate(self.cutline_pool):
            if i < len(cfg.cut_lines):
                cd = cfg.cut_lines[i]
                line.configure(Vector2(cd["a"]), Vector2(cd["b"]))
            else:
                line.deactivate()

        if instant:
            self.phase = list(self.phase_configs.keys())[list(self.phase_configs.values()).index(cfg)]

    def _segment_intersection(self, p1: Vector2, p2: Vector2, q1: Vector2, q2: Vector2) -> bool:
        def orient(a, b, c):
            return (b.x - a.x) * (c.y - a.y) - (b.y - a.y) * (c.x - a.x)

        o1 = orient(p1, p2, q1)
        o2 = orient(p1, p2, q2)
        o3 = orient(q1, q2, p1)
        o4 = orient(q1, q2, p2)
        return (o1 * o2 < 0) and (o3 * o4 < 0)

    def _closest_triangle_normal(self, tri: ReflectiveTriangle, p: Vector2):
        pts = tri.points()
        best_n = Vector2(1, 0)
        best_d = 1e9
        for i in range(3):
            a = pts[i]
            b = pts[(i + 1) % 3]
            edge = b - a
            n = Vector2(-edge.y, edge.x)
            if n.length_squared() == 0:
                continue
            n = n.normalize()
            d = abs((p - a).dot(n))
            if d < best_d:
                best_d = d
                best_n = n
        return best_n

    def _build_spatial_hash(self):
        self._hash.clear()
        cell = 120
        for refl in self.active_reflectors:
            r = refl.aabb()
            for gx in range(int(r.left // cell), int(r.right // cell) + 1):
                for gy in range(int(r.top // cell), int(r.bottom // cell) + 1):
                    self._hash.setdefault((gx, gy), []).append(("reflector", refl))
        if self.active_gravity:
            r = self.active_gravity.aabb()
            for gx in range(int(r.left // cell), int(r.right // cell) + 1):
                for gy in range(int(r.top // cell), int(r.bottom // cell) + 1):
                    self._hash.setdefault((gx, gy), []).append(("gravity", self.active_gravity))
        for cl in self.active_cutlines:
            r = cl.aabb()
            for gx in range(int(r.left // cell), int(r.right // cell) + 1):
                for gy in range(int(r.top // cell), int(r.bottom // cell) + 1):
                    self._hash.setdefault((gx, gy), []).append(("cutline", cl))

    def _query(self, pos: Vector2):
        return self._hash.get((int(pos.x // 120), int(pos.y // 120)), [])

    def update(
        self,
        dt: float,
        player,
        boss,
        projectiles,
        world_state: dict,
        consecutive_player_hits: int,
        player_focus_point: Vector2,
        on_player_cutline_damage,
        audio,
    ):
        self.micro_adjust_cd = max(0.0, self.micro_adjust_cd - dt)
        self.visual_pulse = max(0.0, self.visual_pulse - dt * 1.5)
        distortion = world_state.get("permanent_distortion_level", 0.0)

        if self.transitioning:
            self.transition_t += dt
            t = min(1.0, self.transition_t / self.transition_len)
            for i, refl in enumerate(self.reflector_pool):
                if i in self.target_positions:
                    sp, sr = self.start_positions.get(i, (self.target_positions[i][0], self.target_positions[i][1]))
                    tp, tr = self.target_positions[i]
                    refl.configure(sp.lerp(tp, t), sr + (tr - sr) * t)
                else:
                    refl.deactivate()
            if t >= 1.0:
                self.transitioning = False
                self.phase = self.target_phase
                self.apply_phase_config(self.phase_configs[self.phase], player.pos)

        if consecutive_player_hits >= 2 and self.micro_adjust_cd <= 0 and not self.transitioning:
            self.micro_adjust_cd = 15.0
            if self.active_reflectors and random.random() < 0.7:
                r = random.choice(self.active_reflectors)
                target = r.center.lerp(player_focus_point, 0.25)
                r.center = Vector2(
                    max(self.arena_bounds.left + 30, min(self.arena_bounds.right - 30, target.x)),
                    max(self.arena_bounds.top + 30, min(self.arena_bounds.bottom - 30, target.y)),
                )
            elif self.active_gravity:
                self.active_gravity.center = self.active_gravity.center.lerp(player_focus_point, 0.18)

        cfg = self.phase_configs[self.phase]
        if cfg.global_rotation_speed:
            self.global_rotation += cfg.global_rotation_speed * dt
            for r in self.active_reflectors:
                r.rotation += cfg.global_rotation_speed * dt * 0.12

        if distortion > 0.4:
            for r in self.active_reflectors:
                r.rotation += random.uniform(-0.6, 0.6) * dt
            if self.active_gravity:
                self.active_gravity.radius += (random.uniform(-1.2, 1.2) * dt)
                self.active_gravity.radius = max(70, min(160, self.active_gravity.radius))

        self._build_spatial_hash()
        in_gravity_ids = set()

        # disable geometric collisions during transitions
        if not self.transitioning:
            for proj in list(projectiles):
                nearby = self._query(proj.pos)
                for typ, obj in nearby:
                    if typ == "gravity":
                        g = obj
                        if proj.pos.distance_to(g.center) <= g.radius:
                            in_gravity_ids.add(id(proj))
                            proj.speed *= (1.0 - g.slow_pct * dt * 3.0)
                            toward = g.center - proj.pos
                            if toward.length_squared() > 0:
                                proj.dir = (proj.dir + toward.normalize() * 0.55 * dt).normalize()
                    elif typ == "cutline":
                        cl = obj
                        prev = getattr(proj, "prev_pos", proj.pos)
                        if self._segment_intersection(prev, proj.pos, cl.a, cl.b):
                            proj.dir = proj.dir.rotate(90)
                    elif typ == "reflector":
                        tr = obj
                        if tr.aabb().collidepoint(proj.pos.x, proj.pos.y):
                            n = self._closest_triangle_normal(tr, proj.pos)
                            proj.dir = (proj.dir - 2 * proj.dir.dot(n) * n).normalize()
                            audio.play_sfx("reflect_player" if proj.owner == "player" else "reflect_boss")

            for cl in self.active_cutlines:
                if self._segment_intersection(getattr(player, "prev_pos", player.pos), player.pos, cl.a, cl.b) and player.dash_timer > 0:
                    on_player_cutline_damage(8)

        for pid in in_gravity_ids - self._last_gravity_entries:
            audio.play_sfx("gravity_enter")
        self._last_gravity_entries = in_gravity_ids

        self.clamp_boss_inside(boss)

    def clamp_boss_inside(self, boss):
        if boss is None:
            return
        old = Vector2(boss.pos)
        boss.pos.x = max(self.arena_bounds.left + 10, min(self.arena_bounds.right - 10, boss.pos.x))
        boss.pos.y = max(self.arena_bounds.top + 10, min(self.arena_bounds.bottom - 10, boss.pos.y))
        if old != boss.pos:
            delta = boss.pos - old
            boss.impulse = getattr(boss, "impulse", Vector2()) + delta * -6
            self.visual_pulse = 0.8


    def set_door_theme(self, door_name: str):
        # Modula la arena según la puerta elegida para diversificar jugabilidad.
        if door_name == "CONFLICT":
            self.phase_configs[1].cut_lines = [{"a": Vector2(340, 120), "b": Vector2(620, 300)}]
            self.phase_configs[2].global_rotation_speed = 16
            self.phase_configs[3].global_rotation_speed = 24
        elif door_name == "CONTEMPLATION":
            self.phase_configs[1].cut_lines = []
            self.phase_configs[2].gravity_zone = {"center": Vector2(WIDTH / 2, HEIGHT / 2), "radius": 145, "slow_pct": 0.28}
            self.phase_configs[3].gravity_zone = {"center": Vector2(WIDTH / 2, HEIGHT / 2), "radius": 160, "slow_pct": 0.30}
        elif door_name == "SHADOW":
            self.phase_configs[2].cut_lines = [{"a": Vector2(180, 180), "b": Vector2(760, 460)}]
            self.phase_configs[3].cut_lines = [
                {"a": Vector2(220, 120), "b": Vector2(220, 520)},
                {"a": Vector2(700, 120), "b": Vector2(700, 520)},
            ]
        elif door_name == "ASCENT":
            self.phase_configs[1].reflectors = [{"center": Vector2(260, 250), "rotation": 0}, {"center": Vector2(620, 250), "rotation": 180}]
            self.phase_configs[2].reflectors = [{"center": Vector2(220, 220), "rotation": 25}, {"center": Vector2(680, 330), "rotation": 210}]

        # Aplicación inmediata para que el cambio de puerta sea legible en la sala actual.
        self.apply_phase_config(self.phase_configs[self.phase], Vector2(WIDTH // 2, HEIGHT // 2), instant=True)

    def draw(self, screen):
        pygame.draw.rect(screen, (60, 80, 110), self.arena_bounds, 2)
        if self.visual_pulse > 0:
            pulse_col = (120, 180, 240, int(90 * self.visual_pulse))
            surf = pygame.Surface((self.arena_bounds.width, self.arena_bounds.height), pygame.SRCALPHA)
            surf.fill(pulse_col)
            screen.blit(surf, self.arena_bounds.topleft)

        for r in self.active_reflectors:
            pts = [p.xy for p in r.points()]
            pygame.draw.polygon(screen, (180, 220, 255), pts, 2)

        g = self.active_gravity
        if g:
            gs = pygame.Surface((int(g.radius * 2) + 4, int(g.radius * 2) + 4), pygame.SRCALPHA)
            pygame.draw.circle(gs, (120, 90, 180, 48), (int(g.radius) + 2, int(g.radius) + 2), int(g.radius))
            screen.blit(gs, (int(g.center.x - g.radius - 2), int(g.center.y - g.radius - 2)))
            pygame.draw.circle(screen, (148, 120, 220), (int(g.center.x), int(g.center.y)), int(g.radius), 2)
            pygame.draw.circle(screen, (148, 120, 220), (int(g.center.x), int(g.center.y)), 4)

        for i, cl in enumerate(self.active_cutlines):
            jitter = random.uniform(-1.5, 1.5) if self.phase >= 2 else 0.0
            a = (cl.a.x + jitter, cl.a.y)
            b = (cl.b.x + jitter, cl.b.y)
            color = (255, 130 + i * 20, 120)
            pygame.draw.line(screen, color, a, b, 3)
            pygame.draw.circle(screen, color, (int(a[0]), int(a[1])), 5)
            pygame.draw.circle(screen, color, (int(b[0]), int(b[1])), 5)

        if self.transitioning:
            tw = 280
            tr = pygame.Rect(self.arena_bounds.centerx - tw // 2, self.arena_bounds.top - 22, tw, 10)
            pygame.draw.rect(screen, (40, 44, 56), tr, border_radius=4)
            progress = min(1.0, self.transition_t / max(0.001, self.transition_len))
            pygame.draw.rect(screen, (120, 170, 230), (tr.x, tr.y, int(tw * progress), tr.h), border_radius=4)

    def get_context_for_boss(self):
        return {
            "arena_bounds": self.arena_bounds,
            "gravity": self.active_gravity,
            "reflectors": self.active_reflectors,
            "cutlines": self.active_cutlines,
            "phase": self.phase,
        }
