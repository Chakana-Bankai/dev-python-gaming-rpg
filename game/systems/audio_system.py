"""Procedural 8-bit audio system (no assets).
Genera ondas cuadradas y ruido con pygame.mixer + numpy.
"""

from __future__ import annotations

import numpy as np
import pygame


class AudioSystem:
    def __init__(self):
        self.enabled = False
        self.sample_rate = 22050
        self.music_channel = None
        self.sfx_channel = None
        self._cache = {}
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=self.sample_rate, size=-16, channels=1, buffer=512)
            self.music_channel = pygame.mixer.Channel(0)
            self.sfx_channel = pygame.mixer.Channel(1)
            self.enabled = True
            self._build_bank()
        except pygame.error:
            self.enabled = False

    def _square(self, freq: float, dur: float, volume: float = 0.3):
        key = ("sq", round(freq, 2), round(dur, 3), round(volume, 2))
        if key in self._cache:
            return self._cache[key]
        t = np.linspace(0, dur, int(self.sample_rate * dur), endpoint=False)
        wave = np.sign(np.sin(2 * np.pi * freq * t))
        env = np.linspace(1.0, 0.0, wave.size)
        audio = (wave * env * volume * 32767).astype(np.int16)
        snd = pygame.mixer.Sound(buffer=audio)
        self._cache[key] = snd
        return snd

    def _noise(self, dur: float, volume: float = 0.2):
        key = ("nz", round(dur, 3), round(volume, 2))
        if key in self._cache:
            return self._cache[key]
        n = int(self.sample_rate * dur)
        wave = np.random.uniform(-1.0, 1.0, n)
        env = np.linspace(1.0, 0.0, n)
        audio = (wave * env * volume * 32767).astype(np.int16)
        snd = pygame.mixer.Sound(buffer=audio)
        self._cache[key] = snd
        return snd

    def _build_bank(self):
        # SFX bank
        self.sfx = {
            "shoot": self._square(760, 0.05, 0.22),
            "dash": self._square(300, 0.08, 0.25),
            "damage": self._square(170, 0.11, 0.32),
            "boss_spawn": self._square(95, 0.30, 0.36),
        }
        # Final sounds
        self.final_sounds = {
            "RUPTURA": self._square(420, 0.24, 0.3),
            "DISOLUCION": self._square(260, 0.30, 0.28),
            "INTEGRACION": self._square(520, 0.28, 0.28),
        }

        # Procedural loops
        self.menu_loop = self._build_menu_loop()
        self.gameplay_loop = self._build_gameplay_loop()

    def _build_menu_loop(self):
        # 220Hz pulse each 1.2s
        total = int(self.sample_rate * 4.8)
        audio = np.zeros(total, dtype=np.float32)
        pulse = np.sign(np.sin(2 * np.pi * 220 * np.linspace(0, 0.12, int(self.sample_rate * 0.12), endpoint=False)))
        pulse *= np.linspace(1.0, 0.0, pulse.size)
        for s in [0.0, 1.2, 2.4, 3.6]:
            i = int(s * self.sample_rate)
            j = min(total, i + pulse.size)
            audio[i:j] += pulse[: j - i] * 0.18
        pcm = np.clip(audio * 32767, -32767, 32767).astype(np.int16)
        return pygame.mixer.Sound(buffer=pcm)

    def _build_gameplay_loop(self):
        # 140 BPM tick + noise accent each 4 beats
        bpm = 140
        beat = 60.0 / bpm
        total = int(self.sample_rate * (beat * 16))
        audio = np.zeros(total, dtype=np.float32)
        tick = np.sign(np.sin(2 * np.pi * 330 * np.linspace(0, 0.04, int(self.sample_rate * 0.04), endpoint=False)))
        tick *= np.linspace(1.0, 0.0, tick.size)
        accent = np.random.uniform(-1.0, 1.0, int(self.sample_rate * 0.07)) * np.linspace(1.0, 0.0, int(self.sample_rate * 0.07))
        for b in range(16):
            i = int((b * beat) * self.sample_rate)
            j = min(total, i + tick.size)
            audio[i:j] += tick[: j - i] * 0.12
            if b % 4 == 0:
                j2 = min(total, i + accent.size)
                audio[i:j2] += accent[: j2 - i] * 0.07
        pcm = np.clip(audio * 32767, -32767, 32767).astype(np.int16)
        return pygame.mixer.Sound(buffer=pcm)

    def play_sfx(self, name: str):
        if not self.enabled:
            return
        s = self.sfx.get(name)
        if s:
            self.sfx_channel.play(s)

    def play_music(self, name: str):
        if not self.enabled:
            return
        if name == "menu":
            self.music_channel.play(self.menu_loop, loops=-1)
        elif name == "gameplay":
            self.music_channel.play(self.gameplay_loop, loops=-1)

    def stop_music(self):
        if self.enabled:
            self.music_channel.stop()

    def play_final(self, archetype: str):
        if not self.enabled:
            return
        # map archetype -> requested final sonics
        key = {
            "Duelist": "RUPTURA",
            "Colossus": "DISOLUCION",
            "Oracle": "INTEGRACION",
            "Overlord": "RUPTURA",
        }.get(archetype, "INTEGRACION")
        self.sfx_channel.play(self.final_sounds[key])
