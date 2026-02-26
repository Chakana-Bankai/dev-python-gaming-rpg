import pygame
from pygame.math import Vector2

from game.entities.boss import BossOne, BossTwo, ReflectBoss
from game.entities.super_boss import SuperBoss
from game.settings import GameState


class CombatSystem:
    def handle(self, gm, dt: float):
        # player bullets -> enemies
        hits = pygame.sprite.groupcollide(gm.enemies, gm.player_bullets, False, False)
        for enemy, bullets in hits.items():
            for b in bullets:
                if isinstance(enemy, SuperBoss) and not enemy.can_take_damage(gm.player.fire_timer.value):
                    b.kill()
                    continue

                dead = enemy.take_damage(b.damage)
                enemy.apply_knock(b.dir, 120)

                if b.pierce > 0:
                    b.pierce -= 1
                else:
                    b.kill()

                if gm.player.lifesteal_ratio > 0:
                    gm.player.heal(b.damage * gm.player.lifesteal_ratio * 0.22)

                if dead:
                    gained = 50 if isinstance(enemy, (BossOne, BossTwo, ReflectBoss, SuperBoss)) else 10 + gm.difficulty
                    if gm.player.gain_exp(gained):
                        gm.level_up_options = gm.upgrade_system.roll_options(gm.player)
                        gm.state = GameState.LEVEL_UP

        # enemy bullets -> player
        for b in pygame.sprite.spritecollide(gm.player, gm.enemy_bullets, False):
            if gm.player.take_damage(b.damage):
                gm.to_game_over()
            b.kill()

        # enemy body -> player
        for e in pygame.sprite.spritecollide(gm.player, gm.enemies, False):
            if gm.player.take_damage(e.damage * dt * 4.0):
                gm.to_game_over()
            push = gm.player.pos - e.pos
            e.apply_knock(-push if push.length_squared() > 0 else Vector2(1, 0), 45)
