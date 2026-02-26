from dataclasses import dataclass


@dataclass
class LevelMeta:
    index: int
    is_boss: bool
    is_final_boss: bool
    is_shadow_event: bool


class LevelSystem:
    def next_level(self, index: int) -> LevelMeta:
        nxt = index + 1
        return LevelMeta(
            index=nxt,
            is_boss=nxt in (3, 6, 8),
            is_final_boss=nxt == 8,
            is_shadow_event=nxt not in (3, 6, 8) and nxt % 2 == 0,
        )
