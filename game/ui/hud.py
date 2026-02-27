import pygame

from game.config import BLUE, GREEN, HEIGHT, ORANGE, RED, WHITE, WIDTH


class HUD:
    def draw(
        self,
        screen,
        font,
        player,
        level_idx: int,
        tension: float,
        profile: str,
        message: str,
        enemies_alive: int,
        difficulty: int,
        powers: list[str],
        secondary_label: str = "Nova",
        secondary_cd: float = 0.0,
    ):
        # Top modern status bar
        bar_h = 76
        panel = pygame.Surface((WIDTH, bar_h), pygame.SRCALPHA)
        panel.fill((10, 14, 24, 185))
        screen.blit(panel, (0, 0))

        hp_x, hp_y, hp_w, hp_h = 28, 22, 360, 20
        pygame.draw.rect(screen, (40, 44, 56), (hp_x, hp_y, hp_w, hp_h), border_radius=6)
        ratio = max(0.0, min(1.0, player.hp / max(1, player.max_hp)))
        col = GREEN if ratio > 0.55 else ORANGE if ratio > 0.25 else RED
        pygame.draw.rect(screen, col, (hp_x, hp_y, int(hp_w * ratio), hp_h), border_radius=6)
        pygame.draw.rect(screen, WHITE, (hp_x, hp_y, hp_w, hp_h), 2, border_radius=6)

        exp_x, exp_y, exp_w, exp_h = 28, 50, 360, 8
        pygame.draw.rect(screen, (36, 40, 52), (exp_x, exp_y, exp_w, exp_h), border_radius=4)
        exp_ratio = max(0.0, min(1.0, player.exp / max(1, player.exp_next)))
        pygame.draw.rect(screen, BLUE, (exp_x, exp_y, int(exp_w * exp_ratio), exp_h), border_radius=4)

        screen.blit(font.render(f"HP {int(player.hp)}/{int(player.max_hp)}", True, WHITE), (hp_x + hp_w + 16, 18))
        screen.blit(font.render(f"◈ L{level_idx}", True, WHITE), (560, 18))
        screen.blit(font.render(f"✹ {enemies_alive}", True, WHITE), (670, 18))
        screen.blit(font.render(f"Ψ {tension:.1f}", True, WHITE), (760, 18))
        screen.blit(font.render(f"Δ {difficulty}", True, WHITE), (870, 18))
        screen.blit(font.render(f"Arq: {profile}", True, BLUE), (950, 18))

        if powers:
            powers_txt = " · ".join(powers[:3])
            screen.blit(font.render(f"Poderes {powers_txt}", True, WHITE), (560, 46))

        sec_state = "READY" if secondary_cd <= 0 else f"{secondary_cd:.1f}s"
        screen.blit(font.render(f"2º {secondary_label}: {sec_state}", True, WHITE), (1220, 46))

        # Bottom center event banner for boss/text cues
        if message:
            banner_w, banner_h = 860, 38
            bx = (WIDTH - banner_w) // 2
            by = HEIGHT - 96
            pygame.draw.rect(screen, (12, 14, 24), (bx, by, banner_w, banner_h), border_radius=8)
            pygame.draw.rect(screen, (102, 124, 200), (bx, by, banner_w, banner_h), 2, border_radius=8)
            text = font.render(message, True, WHITE)
            screen.blit(text, text.get_rect(center=(bx + banner_w // 2, by + banner_h // 2)))
