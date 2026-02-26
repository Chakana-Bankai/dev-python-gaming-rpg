from pathlib import Path

WIDTH = 960
HEIGHT = 540
FPS = 60
MAX_LEVELS = 8

BG = (16, 18, 24)
GRID = (28, 32, 44)
WHITE = (232, 236, 244)
GREEN = (80, 200, 120)
RED = (220, 78, 96)
BLUE = (95, 130, 220)
YELLOW = (240, 196, 83)
PURPLE = (170, 110, 220)
CYAN = (90, 205, 220)

DATA_DIR = Path(__file__).resolve().parent / "data"
WORLD_MEMORY_PATH = DATA_DIR / "world_memory.json"
