from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RunState:
    room_index: int = 1
    rooms_cleared: int = 0
    symbolic_state: str = "Caos"
    active_archetype: str = "Iniciado"
    special_event: str | None = None
    seed: int | None = None
    finished: bool = False
    victory: bool = False


@dataclass
class StateManager:
    run: RunState = field(default_factory=RunState)

    def reset_run(self, archetype: str, seed: int):
        self.run = RunState(active_archetype=archetype, seed=seed)
