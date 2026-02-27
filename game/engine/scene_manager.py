from __future__ import annotations


class SceneManager:
    def __init__(self, initial_scene):
        self.current_scene = initial_scene

    def handle_event(self, event):
        self.current_scene.handle_event(event)

    def update(self, dt: float):
        self.current_scene.update(dt)
        nxt = self.current_scene.next_scene()
        if nxt is not None:
            self.current_scene = nxt

    def render(self, screen):
        self.current_scene.render(screen)
