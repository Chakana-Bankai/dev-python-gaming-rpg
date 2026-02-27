import pygame

from game.config import HEIGHT, WIDTH
from game.core.game_manager import GameManager
from game.systems.audio_system import AudioSystem


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Symbolic Roguelike")

    audio = AudioSystem()  # inicialización global de audio procedural
    GameManager(screen, audio=audio).run()

    pygame.quit()


if __name__ == "__main__":
    main()
