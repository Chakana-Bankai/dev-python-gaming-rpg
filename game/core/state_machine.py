from enum import Enum, auto


class GameState(Enum):
    MENU = auto()
    RUNNING = auto()
    LEVEL_UP = auto()
    BOSS = auto()
    PAUSED = auto()
    FINAL = auto()
    GAME_OVER = auto()


class StateMachine:
    def __init__(self):
        self.current = GameState.MENU

    def set(self, state: GameState):
        self.current = state

    def is_state(self, state: GameState) -> bool:
        return self.current == state
