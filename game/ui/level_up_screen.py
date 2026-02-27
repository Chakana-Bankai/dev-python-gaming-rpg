import pygame

from game.settings import BLUE, WHITE, WIDTH, HEIGHT


class LevelUpScreen:
    def draw(self, screen, font, small_font, options):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((8, 10, 16, 220))
        screen.blit(overlay, (0, 0))

        title = font.render("LEVEL UP | Choose: 1 / 2 / 3", True, WHITE)
        screen.blit(title, title.get_rect(center=(WIDTH // 2, 150)))

        for i, opt in enumerate(options, start=1):
            rect = pygame.Rect(WIDTH // 2 - 220, 190 + (i - 1) * 72, 440, 52)
            pygame.draw.rect(screen, (34, 39, 52), rect, border_radius=8)
            pygame.draw.rect(screen, BLUE, rect, 2, border_radius=8)
            txt = small_font.render(f"{i}. {opt.label}", True, WHITE)
            screen.blit(txt, (rect.x + 16, rect.y + 16))
