from enum import Enum, auto

WIDTH = 960
HEIGHT = 540
FPS = 60
MAX_LEVELS = 8

# Colors
BG = (14, 16, 22)
GRID = (24, 28, 38)
WHITE = (230, 233, 240)
RED = (220, 78, 96)
GREEN = (72, 196, 114)
BLUE = (92, 130, 230)
YELLOW = (240, 196, 83)
PURPLE = (160, 110, 220)
CYAN = (80, 210, 220)
ORANGE = (237, 153, 74)
DARK_OVERLAY = (0, 0, 0, 150)


class GameState(Enum):
    MENU = auto()
    PLAYING = auto()
    LEVEL_UP = auto()
    BOSS = auto()
    GAME_OVER = auto()
    SECRET_FINAL = auto()


class DoorType(Enum):
    CONFLICT = "Conflict"
    CONTEMPLATION = "Contemplation"
    SHADOW = "Shadow"
    ASCENT = "Ascent"


class ShotTrait(Enum):
    TRIPLE = "Triple Shot"
    PIERCE = "Piercing"
    BOUNCE = "Ricochet"
    CRIT = "Critical"
    LIFESTEAL = "Lifesteal"
