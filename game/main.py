import pygame

from game.config import HEIGHT, WIDTH
from game.core.game_manager import GameManager


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Symbolic Roguelike")
    GameManager(screen).run()
    pygame.quit()


if __name__ == "__main__":
    main()
