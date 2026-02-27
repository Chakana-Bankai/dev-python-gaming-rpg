import random
from dataclasses import dataclass

from game.settings import ShotTrait


@dataclass
class UpgradeOption:
    label: str
    apply_fn: callable


class UpgradeSystem:
    def __init__(self, max_upgrades: int = 4):
        self.max_upgrades = max_upgrades

    def roll_options(self, player) -> list[UpgradeOption]:
        p = player
        pool = [
            UpgradeOption("+20 Max HP", lambda: setattr(p, "max_hp", p.max_hp + 20)),
            UpgradeOption("+4 Damage", lambda: setattr(p, "base_damage", p.base_damage + 4)),
            UpgradeOption("-10% fire cooldown", lambda: setattr(p, "fire_cd", max(0.07, p.fire_cd * 0.9))),
            UpgradeOption("+12% speed", lambda: setattr(p, "speed", p.speed * 1.12)),
            UpgradeOption("Dash cooldown down", lambda: setattr(p, "dash_cd", max(0.45, p.dash_cd * 0.9))),
            UpgradeOption("Trait: Triple", lambda: p.traits.add(ShotTrait.TRIPLE)),
            UpgradeOption("Trait: Pierce", lambda: p.traits.add(ShotTrait.PIERCE)),
            UpgradeOption("Trait: Bounce", lambda: p.traits.add(ShotTrait.BOUNCE)),
            UpgradeOption("Trait: Crit", lambda: p.traits.add(ShotTrait.CRIT)),
            UpgradeOption(
                "Trait: Lifesteal",
                lambda: (p.traits.add(ShotTrait.LIFESTEAL), setattr(p, "lifesteal_ratio", p.lifesteal_ratio + 0.05)),
            ),
        ]
        random.shuffle(pool)
        return pool[:3]

    def apply_upgrade(self, player, option: UpgradeOption):
        if len(player.upgrades_taken) >= self.max_upgrades:
            player.heal(20)
            return False, "Upgrade cap reached: insight turns into healing."
        option.apply_fn()
        player.upgrades_taken.append(option.label)
        player.hp = min(player.hp, player.max_hp)
        return True, ""
