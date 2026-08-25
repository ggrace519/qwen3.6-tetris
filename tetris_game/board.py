"""Board logic: collision, bag randomization, movement, line clearing, scoring, game-over."""

import random
from .piece import Piece
from .settings import (
    BOARD_WIDTH, BOARD_HEIGHT, LINE_SCORES, drop_speed, TETROMINO_TYPES,
    SOFT_DROP_POINTS, HARD_DROP_POINTS,
    B2B_MULTIPLIER, COMBO_BASE,
)


class Board:
    """Manages the game grid and all game-state rules.

    The board is an internal grid of ``None`` (empty) or a color tuple
    (cell occupied by a locked piece).  All public methods update this
    grid and the associated score / level / line count.
    """

    def __init__(self):
        self.grid: list[list[None | tuple]] = [[None] * BOARD_WIDTH for _ in range(BOARD_HEIGHT)]
        self.bag: list[str] = []
        self.current: Piece | None = None
        self.next_type: str | None = None
        self.score = 0
        self.lines = 0
        self.level = 1
        self.game_over = False
        # Scoring state (Tetris DS standard)
        self._soft_drop_points = 0   # accumulated soft-drop points this piece
        self._last_clear_type = "other"  # "tetris" | "t-spin" | "other"
        self._combo_count = 0         # consecutive line clears
        self._last_cleared = False    # did this piece just clear lines?
        self._spawn_next()

    # ------------------------------------------------------------------
    # 7-bag randomizer
    # ------------------------------------------------------------------

    def _fill_bag(self):
        self.bag = ["I", "O", "T", "S", "Z", "J", "L"]
        random.shuffle(self.bag)

    def _next_type(self) -> str:
        if not self.bag:
            self._fill_bag()
        return self.bag.pop()

    # ------------------------------------------------------------------
    # Spawning
    # ------------------------------------------------------------------

    def _spawn_next(self):
        """Place the next piece from the bag, and draw a new next piece."""
        if self.next_type is None:
            self.next_type = self._next_type()
        piece = Piece(self.next_type)
        self.next_type = self._next_type()
        self.current = piece

        # Game-over: the newly spawned piece already collides
        if self._collides(piece.row, piece.col, piece.cells()):
            self.game_over = True

    # ------------------------------------------------------------------
    # Collision
    # ------------------------------------------------------------------

    def _collides(self, row: int, col: int, cells) -> bool:
        """Return True if placing the piece at (row, col) would overlap."""
        for dr, dc in cells:
            r, c = row + dr, col + dc
            if r < 0 or r >= BOARD_HEIGHT or c < 0 or c >= BOARD_WIDTH:
                return True
            if self.grid[r][c] is not None:
                return True
        return False

    # ------------------------------------------------------------------
    # Movement
    # ------------------------------------------------------------------

    def move_left(self) -> bool:
        if self.current is None:
            return False
        if not self._collides(self.current.row, self.current.col - 1, self.current.cells()):
            self.current.move(0, -1)
            return True
        return False

    def move_right(self) -> bool:
        if self.current is None:
            return False
        if not self._collides(self.current.row, self.current.col + 1, self.current.cells()):
            self.current.move(0, 1)
            return True
        return False

    def move_down(self, soft_drop: bool = False) -> bool:
        """Move the current piece down one cell.

        If *soft_drop* is True (player-held down key), award
        :data:`SOFT_DROP_POINTS` per cell toward the score.
        """
        if self.current is None:
            return False
        if not self._collides(self.current.row + 1, self.current.col, self.current.cells()):
            self.current.move(1, 0)
            if soft_drop:
                self._soft_drop_points += SOFT_DROP_POINTS
            return True
        return False

    def rotate(self, clockwise: bool = True) -> bool:
        if self.current is None:
            return False
        if self.current.type == "O":
            return False
        _, next_rot = self.current.rotated_cells(clockwise)
        old_rot = self.current.rotation
        self.current.rotation = next_rot
        if self._collides(self.current.row, self.current.col, self.current.cells()):
            # Wall kick attempts: try shifting left/right by 1 or 2 cells
            kicked = False
            for dc in [1, -1, 2, -2]:
                if not self._collides(self.current.row, self.current.col + dc, self.current.cells()):
                    self.current.col += dc
                    kicked = True
                    break
            if not kicked:
                # Revert
                self.current.rotation = old_rot
                return False
        return True

    def hard_drop(self):
        if self.current is None:
            return 0
        drop_dist = 0
        while not self._collides(self.current.row + 1, self.current.col, self.current.cells()):
            self.current.row += 1
            drop_dist += 1
        self.score += drop_dist * HARD_DROP_POINTS
        self._lock()
        return drop_dist

    def ghost_row(self) -> int:
        """Return the row where the piece would land if hard-dropped (for ghost rendering)."""
        if self.current is None:
            return 0
        ghost_row = self.current.row
        while not self._collides(ghost_row + 1, self.current.col, self.current.cells()):
            ghost_row += 1
        return ghost_row

    # ------------------------------------------------------------------
    # Locking, line clearing, scoring
    # ------------------------------------------------------------------

    def _lock(self):
        """Lock the current piece into the grid, clear lines, spawn next."""
        if self.current is None:
            return
        # Add accumulated soft-drop points
        self.score += self._soft_drop_points
        self._soft_drop_points = 0
        for r, c in self.current.get_absolute_cells():
            assert 0 <= r < BOARD_HEIGHT and 0 <= c < BOARD_WIDTH, \
                f"Piece cell ({r},{c}) out of bounds — collision detection failed"
            self.grid[r][c] = self.current.color
        self._clear_lines()
        self._spawn_next()

    def _clear_lines(self):
        """Remove full lines, update score, level, combo, and back-to-back."""
        cleared_rows: list[int] = []
        for r in range(BOARD_HEIGHT):
            if all(cell is not None for cell in self.grid[r]):
                cleared_rows.append(r)

        num_lines = len(cleared_rows)
        if num_lines == 0:
            self._last_cleared = False
            return

        # Remove cleared rows from top to bottom
        for r in sorted(cleared_rows, reverse=True):
            del self.grid[r]
        # Add empty rows at top
        for _ in cleared_rows:
            self.grid.insert(0, [None] * BOARD_WIDTH)

        # Scoring: base line clear points × level
        base_score = LINE_SCORES.get(num_lines, 800) * self.level

        # Track clear type for back-to-back
        is_special = num_lines == 4  # "tetris" — could extend to T-spins later
        if is_special and self._last_clear_type in ("tetris", "t-spin"):
            # Back-to-back: 1.5× multiplier
            base_score = int(base_score * B2B_MULTIPLIER)
        self._last_clear_type = "tetris" if is_special else "other"

        # Combo bonus: consecutive line clears across pieces
        if self._last_cleared:
            self._combo_count += 1
            combo_bonus = COMBO_BASE * self._combo_count * self.level
            base_score += combo_bonus
        else:
            self._combo_count = 1  # start combo chain
        self._last_cleared = True

        self.lines += num_lines
        self.score += base_score

        # Level up every 10 lines
        self.level = self.lines // 10 + 1

    def drop_speed(self) -> float:
        return drop_speed(self.level)

    # ------------------------------------------------------------------
    # Reset
    # ------------------------------------------------------------------

    def reset(self):
        self.__init__()