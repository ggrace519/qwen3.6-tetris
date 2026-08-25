"""Game constants, colors, dimensions, scoring values, and shape definitions."""

# Board dimensions
BOARD_WIDTH = 10
BOARD_HEIGHT = 20
CELL_SIZE = 30

# Sidebar (next piece preview, score, level)
SIDEBAR_WIDTH = 150
TOTAL_WIDTH = BOARD_WIDTH * CELL_SIZE + SIDEBAR_WIDTH
TOTAL_HEIGHT = BOARD_HEIGHT * CELL_SIZE

# Colors (R, G, B)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (40, 40, 40)
DARK_GRAY = (30, 30, 30)
BG_COLOR = (20, 20, 20)

# Tetromino colors
COLOR_I = (0, 240, 240)
COLOR_O = (240, 240, 0)
COLOR_T = (160, 0, 240)
COLOR_S = (0, 240, 0)
COLOR_Z = (240, 0, 0)
COLOR_J = (0, 0, 240)
COLOR_L = (240, 160, 0)

TETROMINO_COLORS = {
    "I": COLOR_I,
    "O": COLOR_O,
    "T": COLOR_T,
    "S": COLOR_S,
    "Z": COLOR_Z,
    "J": COLOR_J,
    "L": COLOR_L,
}

# Shape definitions: each rotation state is a list of (row, col) offsets.
# Each state is a normalized 90-degree clockwise rotation of the previous.
SHAPES = {
    "I": [
        [(0, 0), (0, 1), (0, 2), (0, 3)],
        [(0, 0), (1, 0), (2, 0), (3, 0)],
        [(0, 0), (0, 1), (0, 2), (0, 3)],
        [(0, 0), (1, 0), (2, 0), (3, 0)],
    ],
    "O": [
        [(0, 0), (0, 1), (1, 0), (1, 1)],
        [(0, 0), (0, 1), (1, 0), (1, 1)],
        [(0, 0), (0, 1), (1, 0), (1, 1)],
        [(0, 0), (0, 1), (1, 0), (1, 1)],
    ],
    "T": [
        [(0, 1), (1, 0), (1, 1), (1, 2)],
        [(0, 0), (1, 0), (1, 1), (2, 0)],
        [(0, 0), (0, 1), (0, 2), (1, 1)],
        [(0, 1), (1, 0), (1, 1), (2, 1)],
    ],
    "S": [
        [(0, 1), (0, 2), (1, 0), (1, 1)],
        [(0, 0), (1, 0), (1, 1), (2, 1)],
        [(0, 1), (0, 2), (1, 0), (1, 1)],
        [(0, 0), (1, 0), (1, 1), (2, 1)],
    ],
    "Z": [
        [(0, 0), (0, 1), (1, 1), (1, 2)],
        [(0, 1), (1, 0), (1, 1), (2, 0)],
        [(0, 0), (0, 1), (1, 1), (1, 2)],
        [(0, 1), (1, 0), (1, 1), (2, 0)],
    ],
    "J": [
        [(0, 0), (1, 0), (1, 1), (1, 2)],
        [(0, 0), (0, 1), (1, 0), (2, 0)],
        [(0, 0), (0, 1), (0, 2), (1, 2)],
        [(0, 1), (1, 1), (2, 0), (2, 1)],
    ],
    "L": [
        [(0, 2), (1, 0), (1, 1), (1, 2)],
        [(0, 0), (1, 0), (2, 0), (2, 1)],
        [(0, 0), (0, 1), (0, 2), (1, 0)],
        [(0, 0), (0, 1), (1, 1), (2, 1)],
    ],
}

TETROMINO_TYPES = ["I", "O", "T", "S", "Z", "J", "L"]

# Scoring (Tetris DS standard): base points for each line clear count.
# These values already encode the level-1 scoring; the Board multiplies
# by self.level at clear time.  Soft/hard drop points are scored separately.
LINE_SCORES = {1: 100, 2: 300, 3: 500, 4: 800}

# Drop scoring (Tetris DS standard)
SOFT_DROP_POINTS = 1        # 1 point per cell for soft-dropping
HARD_DROP_POINTS = 2        # 2 points per cell for hard-dropping

# Combo / back-to-back
B2B_MULTIPLIER = 1.5        # 1.5x for consecutive special clears (tetris or t-spin)
COMBO_BASE = 50             # 50 points per combo count, scaled by level

# Drop speed: seconds per automatic drop at each level
# Level 1 = 1.0s, decreasing by 0.08s per level, minimum 0.05s
BASE_SPEED = 1.0
SPEED_DECREASE = 0.08
MIN_SPEED = 0.05


def drop_speed(level: int) -> float:
    """Return drop interval in seconds for the given level."""
    return max(MIN_SPEED, BASE_SPEED - (level - 1) * SPEED_DECREASE)
