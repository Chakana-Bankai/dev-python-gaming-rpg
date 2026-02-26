import pygame

from game.config import GREEN, RED, WHITE, WIDTH, HEIGHT


class Menus:
    def draw_menu(self, screen, font, small_font):
        t = font.render("SYMBOLIC ROGUELIKE", True, WHITE)
        s = small_font.render("ENTER start | ESC quit", True, GREEN)
        screen.blit(t, t.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 20)))
        screen.blit(s, s.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 20)))

    def draw_end(self, screen, font, small_font, title: str, body: str):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190))
        screen.blit(overlay, (0, 0))
        screen.blit(font.render(title, True, RED if title == "GAME OVER" else WHITE), (WIDTH // 2 - 90, HEIGHT // 2 - 20))
        screen.blit(small_font.render(body, True, WHITE), (WIDTH // 2 - 220, HEIGHT // 2 + 10))
        screen.blit(small_font.render("R restart | ESC quit", True, WHITE), (WIDTH // 2 - 110, HEIGHT // 2 + 40))
