"""Dynamic layered tactical audio system (procedural, no assets)."""

from __future__ import annotations

import random

import numpy as np
import pygame


class AudioSystem:
    def __init__(self):
        self.enabled = False
        self.sample_rate = 22050
        self.music_channel = None
        self.tension_channel = None
        self.overlay_channel = None
        self.sfx_channel = None
        self._cache = {}
        self._tension_active = False
        self.muted = False
        self.mix_gain = 1.0
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=self.sample_rate, size=-16, channels=1, buffer=512)
            self.music_channel = pygame.mixer.Channel(0)
            self.tension_channel = pygame.mixer.Channel(1)
            self.overlay_channel = pygame.mixer.Channel(2)
            self.sfx_channel = pygame.mixer.Channel(3)
            self.enabled = True
            self._build_bank()
        except pygame.error:
            self.enabled = False

    def _tone(self, freq: float, dur: float, volume: float = 0.3, drift: float = 0.0):
        key = ("tone", round(freq, 2), round(dur, 3), round(volume, 2), round(drift, 3))
        if key in self._cache:
            return self._cache[key]
        t = np.linspace(0, dur, int(self.sample_rate * dur), endpoint=False)
        f = freq + np.sin(t * 2.5) * drift
        wave = np.sin(2 * np.pi * f * t)
        env = np.linspace(1.0, 0.0, wave.size)
        audio = (wave * env * volume * 32767).astype(np.int16)
        snd = pygame.mixer.Sound(buffer=audio)
        self._cache[key] = snd
        return snd

    def _metal(self, freq: float, dur: float, volume: float = 0.3):
        key = ("metal", round(freq), round(dur, 3), round(volume, 2))
        if key in self._cache:
            return self._cache[key]
        t = np.linspace(0, dur, int(self.sample_rate * dur), endpoint=False)
        base = np.sin(2 * np.pi * freq * t)
        overt = np.sin(2 * np.pi * freq * 2.4 * t) * 0.45
        click = np.sign(np.sin(2 * np.pi * freq * 3.8 * t)) * 0.2
        env = np.exp(-t * 18)
        audio = ((base + overt + click) * env * volume * 32767).astype(np.int16)
        snd = pygame.mixer.Sound(buffer=audio)
        self._cache[key] = snd
        return snd

    def _build_bank(self):
        self.sfx = {
            "shoot": self._tone(700, 0.045, 0.18),
            "dash": self._tone(290, 0.07, 0.23),
            "damage": self._tone(165, 0.10, 0.28),
            "boss_spawn": self._tone(95, 0.30, 0.30, drift=8),
            "geom_phase_shift": self._tone(82, 0.24, 0.35, drift=12),
            "reflect_player": self._metal(980, 0.07, 0.2),
            "reflect_boss": self._metal(760, 0.09, 0.24),
            "gravity_enter": self._tone(130, 0.09, 0.16, drift=4),
            "level_up": self._tone(640, 0.16, 0.26, drift=18),
        }

        self.final_sounds = {
            "RUPTURA": self._tone(390, 0.24, 0.28, drift=8),
            "DISOLUCION": self._tone(250, 0.30, 0.26, drift=12),
            "INTEGRACION": self._tone(520, 0.28, 0.24, drift=5),
        }

        self.menu_loop = self._build_ambient_loop(tempo=0.0, color=0)
        self.ambient_variants = [
            self._build_ambient_loop(tempo=1.0, color=0),
            self._build_ambient_loop(tempo=1.0, color=1),
            self._build_ambient_loop(tempo=1.0, color=2),
        ]
        self.tension_loop = self._build_tension_loop()
        self.final_overlay = self._build_final_overlay()

    def _build_ambient_loop(self, tempo=1.0, color=0):
        total = int(self.sample_rate * 6.0)
        t = np.linspace(0, 6.0, total, endpoint=False)
        roots = [84, 96, 76][color % 3]
        pad = np.sin(2 * np.pi * roots * t) * 0.18 + np.sin(2 * np.pi * (roots * 1.5) * t) * 0.08
        texture = np.sin(2 * np.pi * (42 + np.sin(t * (0.35 + color * 0.08)) * (3 + color)) * t) * 0.12
        pulse = np.zeros_like(t)
        if tempo > 0:
            for sec in [1.0, 2.6, 4.2, 5.6]:
                idx = int(sec * self.sample_rate)
                ln = int(0.15 * self.sample_rate)
                pulse[idx : idx + ln] += np.hanning(ln) * 0.08
        audio = np.clip((pad + texture + pulse) * 0.55, -1, 1)
        return pygame.mixer.Sound(buffer=(audio * 32767).astype(np.int16))

    def _build_tension_loop(self):
        total = int(self.sample_rate * 4.0)
        t = np.linspace(0, 4.0, total, endpoint=False)
        drone = np.sin(2 * np.pi * 70 * t) * 0.16 + np.sin(2 * np.pi * 92 * t) * 0.14
        pulses = np.zeros_like(t)
        for sec in [0.0, 1.0, 2.0, 3.0]:
            idx = int(sec * self.sample_rate)
            ln = int(0.2 * self.sample_rate)
            pulses[idx : idx + ln] += np.hanning(ln) * 0.18
        audio = np.clip((drone + pulses) * 0.6, -1, 1)
        return pygame.mixer.Sound(buffer=(audio * 32767).astype(np.int16))

    def _build_final_overlay(self):
        total = int(self.sample_rate * 3.5)
        t = np.linspace(0, 3.5, total, endpoint=False)
        tone = np.sin(2 * np.pi * (150 + np.sin(t * 2.2) * 9) * t) * 0.2
        low = np.sin(2 * np.pi * 55 * t) * 0.1
        audio = np.clip((tone + low) * np.linspace(0.2, 0.9, total), -1, 1)
        return pygame.mixer.Sound(buffer=(audio * 32767).astype(np.int16))

    def play_sfx(self, name: str):
        if self.enabled and not self.muted and name in self.sfx:
            self.sfx_channel.play(self.sfx[name])

    def play_music(self, name: str):
        if not self.enabled:
            return
        self.stop_music()
        if name == "menu":
            self.music_channel.play(self.menu_loop, loops=-1)
            self.music_channel.set_volume(0.22 * self.mix_gain)
        elif name == "gameplay":
            self.music_channel.play(random.choice(self.ambient_variants), loops=-1)
            self.music_channel.set_volume(0.2 * self.mix_gain)
            self.tension_channel.play(self.tension_loop, loops=-1)
            self.tension_channel.set_volume(0.0)

    def update_dynamic(self, tension_level: float, boss_hp_ratio: float | None = None):
        if not self.enabled or not self.tension_channel:
            return
        target = 0.16 if tension_level > 0.6 else 0.0
        current = self.tension_channel.get_volume()
        self.tension_channel.set_volume((current + (target - current) * 0.05) * self.mix_gain)

        if boss_hp_ratio is not None and boss_hp_ratio <= 0.1:
            self.music_channel.set_volume(0.12 * self.mix_gain)
            self.overlay_channel.play(self.final_overlay, loops=-1)
            self.overlay_channel.set_volume(0.14 * self.mix_gain)
        else:
            self.overlay_channel.stop()

    def set_muted(self, muted: bool):
        self.muted = muted
        if not self.enabled:
            return
        if muted:
            self.stop_music()

    def set_mix_gain(self, gain: float):
        self.mix_gain = max(0.0, min(1.0, gain))

    def stop_music(self):
        if self.enabled:
            self.music_channel.stop()
            self.tension_channel.stop()
            self.overlay_channel.stop()

    def play_final(self, archetype: str):
        if not self.enabled:
            return
        key = {
            "Duelist": "RUPTURA",
            "Colossus": "DISOLUCION",
            "Oracle": "INTEGRACION",
            "Overlord": "RUPTURA",
        }.get(archetype, "INTEGRACION")
        self.sfx_channel.play(self.final_sounds[key])
