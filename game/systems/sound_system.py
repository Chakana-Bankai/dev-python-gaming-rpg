import math
from array import array

import pygame


class SoundSystem:
    """Genera SFX sintéticos (sin assets externos) para disparos, daño y bosses."""

    def __init__(self):
        self.enabled = False
        self._cache = {}
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=512)
            self.enabled = True
        except pygame.error:
            self.enabled = False

    def _tone(self, freq: float, duration: float, volume: float = 0.3):
        key = (round(freq), round(duration, 3), round(volume, 2))
        if key in self._cache:
            return self._cache[key]

        sample_rate = 44100
        n_samples = int(sample_rate * duration)
        buf = array("h")
        amp = int(32767 * max(0.0, min(1.0, volume)))
        for i in range(n_samples):
            t = i / sample_rate
            envelope = max(0.0, 1 - (i / max(1, n_samples)))
            v = int(amp * envelope * math.sin(2 * math.pi * freq * t))
            buf.append(v)

        snd = pygame.mixer.Sound(buffer=buf)
        self._cache[key] = snd
        return snd

    def _play(self, freq: float, duration: float, volume: float):
        if not self.enabled:
            return
        self._tone(freq, duration, volume).play()

    def shoot(self):
        self._play(680, 0.06, 0.22)

    def secondary(self):
        self._play(420, 0.13, 0.28)

    def hit_enemy(self):
        self._play(820, 0.04, 0.20)

    def hit_player(self):
        self._play(180, 0.10, 0.30)

    def boss_spawn(self):
        self._play(95, 0.30, 0.35)
