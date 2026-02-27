import pygame

from game.settings import RED, WHITE, WIDTH, HEIGHT


class EndScreen:
    def draw_game_over(self, screen, font, small_font):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((6, 8, 12, 200))
        screen.blit(overlay, (0, 0))
        screen.blit(font.render("GAME OVER", True, RED), (WIDTH // 2 - 80, HEIGHT // 2 - 20))
        txt = small_font.render("R restart | ESC quit", True, WHITE)
        screen.blit(txt, txt.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 24)))

    def draw_final(self, screen, font, small_font, title: str, body: str):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((6, 8, 12, 220))
        screen.blit(overlay, (0, 0))
        t = font.render(title, True, WHITE)
        b = small_font.render(body, True, WHITE)
        r = small_font.render("R restart | ESC quit", True, WHITE)
        screen.blit(t, t.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 32)))
        screen.blit(b, b.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 2)))
        screen.blit(r, r.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 38)))
