from __future__ import annotations


class BaseScene:
    def __init__(self, ctx: dict):
        self.ctx = ctx
        self._next = None

    def handle_event(self, event):
        pass

    def update(self, dt: float):
        pass

    def render(self, screen):
        pass

    def next_scene(self):
        return self._next
