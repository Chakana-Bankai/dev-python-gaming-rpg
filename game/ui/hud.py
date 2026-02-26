import pygame

from game.settings import BLUE, GREEN, ORANGE, PURPLE, RED, WHITE, WIDTH


class HUD:
    def draw(self, screen, small_font, player, level_index: int, max_upgrades: int, message: str, msg_timer: float):
        x, y, w, h = 18, 16, 230, 20
        pygame.draw.rect(screen, (40, 44, 56), (x, y, w, h), border_radius=5)
        ratio = max(0.0, player.hp / max(1, player.max_hp))
        color = GREEN if ratio > 0.35 else ORANGE if ratio > 0.15 else RED
        pygame.draw.rect(screen, color, (x, y, int(w * ratio), h), border_radius=5)
        pygame.draw.rect(screen, WHITE, (x, y, w, h), 2, border_radius=5)

        screen.blit(small_font.render(f"HP {int(player.hp)}/{int(player.max_hp)}", True, WHITE), (x + 8, y + 2))
        screen.blit(small_font.render(f"Level {level_index}/8", True, WHITE), (18, 42))
        screen.blit(small_font.render(f"Player Lv {player.level}", True, WHITE), (18, 62))
        screen.blit(small_font.render(f"Upgrades {len(player.upgrades_taken)}/{max_upgrades}", True, WHITE), (18, 82))

        ex, ey, ew, eh = 18, 105, 230, 10
        pygame.draw.rect(screen, (40, 44, 56), (ex, ey, ew, eh), border_radius=4)
        exp_ratio = player.exp / max(1, player.exp_next)
        pygame.draw.rect(screen, BLUE, (ex, ey, int(ew * exp_ratio), eh), border_radius=4)

        if msg_timer > 0 and message:
            txt = small_font.render(message, True, PURPLE)
            screen.blit(txt, txt.get_rect(center=(WIDTH // 2, 20)))
