from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass
class Power:
    name: str
    rarity: str

    def passive_effect(self, gm, dt: float):
        return

    def active_effect(self, gm):
        return False


class EchoPower(Power):
    def active_effect(self, gm):
        gm.echo_shot_timer = 0.18
        return True


class RiftDashPower(Power):
    def passive_effect(self, gm, dt: float):
        if gm.player.dash_timer > 0:
            gm.rift_trail_timer = max(gm.rift_trail_timer, 0.08)


class SilenceFieldPower(Power):
    def active_effect(self, gm):
        gm.silence_field_timer = 2.2
        return True


class InvertPower(Power):
    def active_effect(self, gm):
        gm.invert_timer = 1.6
        return True


class EntropyPower(Power):
    def passive_effect(self, gm, dt: float):
        gm.entropy_mult = min(1.25, 1.0 + gm.kill_streak * 0.012)


class StillnessCorePower(Power):
    def passive_effect(self, gm, dt: float):
        if gm.player.fire_timer <= 0 and gm.player.secondary_timer <= 0:
            gm.player.damage = gm.base_player_damage * 1.15
        else:
            gm.player.damage = gm.base_player_damage


class FractureShotPower(Power):
    def passive_effect(self, gm, dt: float):
        # bonus temporal de penetración tras pausa de fuego (no permanente)
        if gm.time_since_last_shot > 1.4:
            gm.player.pierce = max(gm.player.pierce, gm.base_player_pierce + 1)


class LowLifeFuryPower(Power):
    def passive_effect(self, gm, dt: float):
        if gm.player.hp <= gm.player.max_hp * 0.30:
            gm.player.damage = gm.base_player_damage * 1.22


class MirrorSkinPower(Power):
    def passive_effect(self, gm, dt: float):
        gm.mirror_skin_chance = 0.08


class MomentumDrivePower(Power):
    def passive_effect(self, gm, dt: float):
        gm.player.speed = gm.base_player_speed * min(1.5, 1.0 + gm.kill_streak * 0.03)


class PowerSystem:
    def __init__(self):
        self.powers = {
            "Echo": EchoPower("Echo", "rare"),
            "RiftDash": RiftDashPower("RiftDash", "rare"),
            "SilenceField": SilenceFieldPower("SilenceField", "epic"),
            "Invert": InvertPower("Invert", "epic"),
            "Entropy": EntropyPower("Entropy", "rare"),
            "StillnessCore": StillnessCorePower("StillnessCore", "rare"),
            "FractureShot": FractureShotPower("FractureShot", "rare"),
            "LowLifeFury": LowLifeFuryPower("LowLifeFury", "rare"),
            "MirrorSkin": MirrorSkinPower("MirrorSkin", "epic"),
            "MomentumDrive": MomentumDrivePower("MomentumDrive", "common"),
        }

    def roll_power_cards(self, owned: set[str], n=3):
        candidates = [p for p in self.powers.values() if p.name not in owned]
        random.shuffle(candidates)
        return candidates[:n]

    def apply_passives(self, gm, dt: float):
        for name in gm.owned_powers:
            self.powers[name].passive_effect(gm, dt)

    def activate_random_owned(self, gm):
        if not gm.owned_powers:
            return False
        # activa primero uno con active_effect útil
        random_order = list(gm.owned_powers)
        random.shuffle(random_order)
        for name in random_order:
            if self.powers[name].active_effect(gm):
                return True
        return False

    def activate_primary_owned(self, gm):
        if not gm.owned_powers:
            return False
        ordered = sorted(gm.owned_powers)
        for name in ordered:
            power = self.powers.get(name)
            if power and power.active_effect(gm):
                return True
        return False

    def describe(self, name: str) -> str:
        descriptions = {
            "Echo": "repite el último disparo",
            "RiftDash": "dash deja rastro dañino",
            "SilenceField": "anula disparos enemigos en área",
            "Invert": "controles invertidos, daño x2 breve",
            "Entropy": "aumenta ritmo por racha",
            "StillnessCore": "más daño si no disparas",
            "FractureShot": "perfora tras silencio",
            "LowLifeFury": "furia con HP bajo",
            "MirrorSkin": "chance de reflejar daño",
            "MomentumDrive": "velocidad por kill streak",
        }
        return descriptions.get(name, "efecto adaptable")

    def get_primary_active_power_name(self, owned: set[str]) -> str:
        active_names = []
        for name in owned:
            power = self.powers.get(name)
            if power and power.active_effect.__func__ is not Power.active_effect:
                active_names.append(name)
        return sorted(active_names)[0] if active_names else "Nova"
