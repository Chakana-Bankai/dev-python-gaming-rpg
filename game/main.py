from __future__ import annotations

import json

import pygame

from game.config import DATA_DIR, FPS, HEIGHT, WIDTH
from game.engine.save_system import SaveSystem
from game.engine.scene_manager import SceneManager
from game.engine.state_manager import StateManager
from game.scenes.intro_scene import IntroScene
from game.systems.audio_system import AudioSystem
from game.systems.camera_system import CameraSystem
from game.systems.difficulty_system import DifficultySystem
from game.systems.particle_system import ParticleSystem
from game.systems.procedural_system import ProceduralSystem
from game.systems.progression_system import ProgressionSystem


def load_json(name: str):
    return json.loads((DATA_DIR / name).read_text(encoding="utf-8"))


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Roguelike 2D Iniciático Evolutivo")
    clock = pygame.time.Clock()

    save = SaveSystem(DATA_DIR / "progression.json")
    narrative_data = load_json("narrative.json")
    _config = load_json("config.json")

    audio = AudioSystem()
    audio.play_music("menu")

    procedural = ProceduralSystem()
    seed = procedural.start_run(save.data.get("last_seed"))

    state = StateManager()
    state.reset_run(archetype=save.data.get("archetype_unlocked", "Iniciado"), seed=seed)

    ctx = {
        "screen": screen,
        "font": pygame.font.SysFont("consolas", 26),
        "small": pygame.font.SysFont("consolas", 16),
        "audio": audio,
        "save": save,
        "state": state,
        "difficulty": DifficultySystem(),
        "progression": ProgressionSystem(save.data),
        "procedural": procedural,
        "particles": ParticleSystem(),
        "camera": CameraSystem(),
        "narrative_data": narrative_data,
    }

    sm = SceneManager(IntroScene(ctx))

    running = True
    while running:
        dt = min(0.033, clock.tick(FPS) / 1000.0)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            else:
                sm.handle_event(event)

        sm.update(dt)
        sm.render(screen)
        pygame.display.flip()

    save.flush()
    pygame.quit()


if __name__ == "__main__":
    main()
