"""Piece class representing the active falling tetromino."""

import random
from .settings import SHAPES, TETROMINO_COLORS


TETROMINO_TYPES = list(SHAPES.keys())


class Piece:
    """Represents the currently falling tetromino.

    The piece knows its type, rotation state, board position (top-left anchor),
    and can produce the list of occupied (row, col) cells at its current state.
    """

    def __init__(self, piece_type: str | None = None):
        if piece_type is None:
            piece_type = random.choice(TETROMINO_TYPES)
        self.type = piece_type
        self.rotation = 0
        # Anchor position: top-left of the bounding box on the board grid
        self.row = 0
        self.col = 3  # Start near center for a 10-wide board

    @property
    def color(self):
        return TETROMINO_COLORS[self.type]

    def cells(self):
        """Return the list of (row, col) cells occupied by this piece."""
        return SHAPES[self.type][self.rotation]

    def rotated_cells(self, clockwise: bool = True):
        """Return the cells the piece would occupy after one rotation step.

        Uses the pre-computed rotation states from SHAPES rather than
        geometrically computing rotation, so wall kicks can reference
        the exact offset lists.
        """
        next_rot = (self.rotation + 1) % 4 if clockwise else (self.rotation - 1) % 4
        return SHAPES[self.type][next_rot], next_rot

    def move(self, dr: int, dc: int):
        """Shift the piece's anchor by (dr, dc)."""
        self.row += dr
        self.col += dc

    def rotate(self, clockwise: bool = True):
        """Advance or reverse the rotation state."""
        if self.type == "O":
            return  # O never changes
        self.rotation = (self.rotation + 1) % 4 if clockwise else (self.rotation - 1) % 4

    def get_absolute_cells(self):
        """Return absolute board coordinates of every occupied cell.

        Each cell in SHAPES is stored as an offset from the piece's anchor.
        """
        offsets = self.cells()
        return [(self.row + r, self.col + c) for r, c in offsets]
