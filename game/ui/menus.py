import pygame

from game.config import GREEN, RED, WHITE, WIDTH, HEIGHT


class Menus:
    def draw_menu(self, screen, font, small_font):
        t = font.render("SYMBOLIC ROGUELIKE", True, WHITE)
        s = small_font.render("ENTER start | P pause/options | ESC quit", True, GREEN)
        c = small_font.render("WASD move | LMB shoot | RMB skill | SHIFT dash", True, WHITE)
        screen.blit(t, t.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 32)))
        screen.blit(s, s.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 4)))
        screen.blit(c, c.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 30)))

    def draw_pause(self, screen, font, small_font):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        t = font.render("PAUSED", True, WHITE)
        s1 = small_font.render("P: resume", True, WHITE)
        s2 = small_font.render("R: restart run", True, WHITE)
        s3 = small_font.render("ESC: quit", True, WHITE)
        screen.blit(t, t.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 24)))
        screen.blit(s1, s1.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 6)))
        screen.blit(s2, s2.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 28)))
        screen.blit(s3, s3.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 50)))

    def draw_end(self, screen, font, small_font, title: str, body: str):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190))
        screen.blit(overlay, (0, 0))
        screen.blit(font.render(title, True, RED if title == "GAME OVER" else WHITE), (WIDTH // 2 - 90, HEIGHT // 2 - 20))
        screen.blit(small_font.render(body, True, WHITE), (WIDTH // 2 - 220, HEIGHT // 2 + 10))
        screen.blit(small_font.render("R restart | ESC quit", True, WHITE), (WIDTH // 2 - 110, HEIGHT // 2 + 40))
