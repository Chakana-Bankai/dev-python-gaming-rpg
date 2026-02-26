import pygame

from game.config import BLUE, GREEN, ORANGE, RED, WHITE


class HUD:
    def draw(self, screen, font, player, level_idx: int, tension: float, profile: str, message: str, enemies_alive: int):
        x, y, w, h = 16, 16, 220, 20
        pygame.draw.rect(screen, (40, 44, 56), (x, y, w, h), border_radius=4)
        ratio = max(0.0, player.hp / max(1, player.max_hp))
        col = GREEN if ratio > 0.35 else ORANGE if ratio > 0.15 else RED
        pygame.draw.rect(screen, col, (x, y, int(w * ratio), h), border_radius=4)
        pygame.draw.rect(screen, WHITE, (x, y, w, h), 2, border_radius=4)

        screen.blit(font.render(f"Level {level_idx}/8", True, WHITE), (16, 44))
        screen.blit(font.render(f"Enemies {enemies_alive}", True, WHITE), (16, 64))
        screen.blit(font.render(f"Tension {tension:.1f}", True, WHITE), (16, 84))
        screen.blit(font.render(f"Profile {profile}", True, BLUE), (16, 104))

        ex, ey, ew, eh = 16, 128, 220, 10
        pygame.draw.rect(screen, (40, 44, 56), (ex, ey, ew, eh), border_radius=3)
        exp_ratio = player.exp / max(1, player.exp_next)
        pygame.draw.rect(screen, BLUE, (ex, ey, int(ew * exp_ratio), eh), border_radius=3)

        if message:
            screen.blit(font.render(message, True, WHITE), (260, 16))
