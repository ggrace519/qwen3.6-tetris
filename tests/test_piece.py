"""Tests for Piece class."""

import pytest
import random
from tetris_game.piece import Piece, TETROMINO_TYPES
from tetris_game.settings import SHAPES, TETROMINO_COLORS


class TestPieceInit:
    def test_default_piece_random_type(self):
        random.seed(42)
        p = Piece()
        assert p.type in TETROMINO_TYPES

    def test_explicit_type_I(self):
        p = Piece("I")
        assert p.type == "I"

    def test_explicit_all_types(self):
        for t in TETROMINO_TYPES:
            p = Piece(t)
            assert p.type == t

    def test_default_rotation_zero(self):
        p = Piece("T")
        assert p.rotation == 0

    def test_default_row_zero(self):
        p = Piece("Z")
        assert p.row == 0

    def test_default_col_three(self):
        p = Piece("S")
        assert p.col == 3


class TestPieceColor:
    def test_I_color(self):
        assert Piece("I").color == TETROMINO_COLORS["I"]

    def test_O_color(self):
        assert Piece("O").color == TETROMINO_COLORS["O"]

    def test_all_types_have_colors(self):
        for t in TETROMINO_TYPES:
            assert Piece(t).color == TETROMINO_COLORS[t]


class TestCells:
    def test_cells_return_correct_shape(self):
        p = Piece("I")
        assert p.cells() == SHAPES["I"][0]

    def test_O_cells(self):
        p = Piece("O")
        assert p.cells() == SHAPES["O"][0]

    def test_T_cells(self):
        p = Piece("T")
        assert p.cells() == SHAPES["T"][0]

    def test_S_cells(self):
        p = Piece("S")
        assert p.cells() == SHAPES["S"][0]

    def test_Z_cells(self):
        p = Piece("Z")
        assert p.cells() == SHAPES["Z"][0]

    def test_J_cells(self):
        p = Piece("J")
        assert p.cells() == SHAPES["J"][0]

    def test_L_cells(self):
        p = Piece("L")
        assert p.cells() == SHAPES["L"][0]

    def test_all_cells_are_tuples(self):
        p = Piece("T")
        for r, c in p.cells():
            assert isinstance(r, int)
            assert isinstance(c, int)

    def test_cell_count_is_four(self):
        p = Piece("I")
        assert len(p.cells()) == 4


class TestRotatedCells:
    def test_clockwise_returns_next_rotation(self):
        p = Piece("T")
        cells, rot = p.rotated_cells(clockwise=True)
        assert rot == 1
        assert cells == SHAPES["T"][1]

    def test_counterclockwise_returns_previous_rotation(self):
        p = Piece("T")
        p.rotation = 1
        cells, rot = p.rotated_cells(clockwise=False)
        assert rot == 0
        assert cells == SHAPES["T"][0]

    def test_O_rotates_but_returns_same_shape(self):
        p = Piece("O")
        cells, rot = p.rotated_cells(clockwise=True)
        assert rot == 1
        assert cells == SHAPES["O"][1]

    def test_wrap_around_3_to_0_clockwise(self):
        p = Piece("T")
        p.rotation = 3
        cells, rot = p.rotated_cells(clockwise=True)
        assert rot == 0

    def test_wrap_around_0_to_3_counterclockwise(self):
        p = Piece("T")
        cells, rot = p.rotated_cells(clockwise=False)
        assert rot == 3


class TestMove:
    def test_move_left(self):
        p = Piece("I")
        p.move(0, -1)
        assert p.col == 2

    def test_move_right(self):
        p = Piece("I")
        p.move(0, 1)
        assert p.col == 4

    def test_move_down(self):
        p = Piece("I")
        p.move(1, 0)
        assert p.row == 1

    def test_move_up(self):
        p = Piece("I")
        p.move(-1, 0)
        assert p.row == -1

    def test_move_diagonal(self):
        p = Piece("I")
        p.move(1, 1)
        assert p.row == 1
        assert p.col == 4

    def test_multiple_moves(self):
        p = Piece("T")
        p.move(0, -1)
        p.move(0, -1)
        assert p.col == 1
        p.move(2, 0)
        assert p.row == 2


class TestRotate:
    def test_T_clockwise(self):
        p = Piece("T")
        p.rotate(clockwise=True)
        assert p.rotation == 1

    def test_T_counterclockwise(self):
        p = Piece("T")
        p.rotate(clockwise=False)
        assert p.rotation == 3

    def test_O_unchanged(self):
        p = Piece("O")
        p.rotate(clockwise=True)
        assert p.rotation == 0
        p.rotate(clockwise=False)
        assert p.rotation == 0

    def test_cycle_4_rotations_returns_to_zero(self):
        p = Piece("J")
        for _ in range(4):
            p.rotate(clockwise=True)
        assert p.rotation == 0

    def test_cycle_4_counterclockwise_returns_to_zero(self):
        p = Piece("L")
        for _ in range(4):
            p.rotate(clockwise=False)
        assert p.rotation == 0

    def test_all_types_rotate(self):
        for t in ["I", "T", "S", "Z", "J", "L"]:
            p = Piece(t)
            p.rotate(clockwise=True)
            assert p.rotation == 1


class TestGetAbsoluteCells:
    def test_absolute_cells_at_origin(self):
        p = Piece("I")
        p.row = 0
        p.col = 0
        abs_cells = p.get_absolute_cells()
        expected = [(0, 0), (0, 1), (0, 2), (0, 3)]
        assert abs_cells == expected

    def test_absolute_cells_offset(self):
        p = Piece("T")
        p.row = 5
        p.col = 7
        abs_cells = p.get_absolute_cells()
        # T[0] = [(0,1),(1,0),(1,1),(1,2)]
        expected = [(5, 8), (6, 7), (6, 8), (6, 9)]
        assert abs_cells == expected

    def test_absolute_cells_negative_row(self):
        p = Piece("S")
        p.row = -1
        p.col = 0
        abs_cells = p.get_absolute_cells()
        assert abs_cells[0] == (-1, 1)

    def test_absolute_cells_after_move(self):
        p = Piece("L")
        p.move(3, 5)  # col = 3+5 = 8
        p.rotate(clockwise=True)
        abs_cells = p.get_absolute_cells()
        # L[1] = [(0,0),(1,0),(2,0),(2,1)]
        # anchor = (3, 8)
        expected = [(3, 8), (4, 8), (5, 8), (5, 9)]
        assert abs_cells == expected

    def test_absolute_cell_count(self):
        p = Piece("Z")
        assert len(p.get_absolute_cells()) == 4
