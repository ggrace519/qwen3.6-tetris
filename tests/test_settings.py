"""Tests for tetris_game.settings constants and shapes."""

import pytest
from tetris_game.settings import (
    BOARD_WIDTH,
    BOARD_HEIGHT,
    CELL_SIZE,
    SIDEBAR_WIDTH,
    TOTAL_WIDTH,
    TOTAL_HEIGHT,
    WINDOW_MARGIN,
    BLACK,
    WHITE,
    GRAY,
    DARK_GRAY,
    BG_COLOR,
    COLOR_I,
    COLOR_O,
    COLOR_T,
    COLOR_S,
    COLOR_Z,
    COLOR_J,
    COLOR_L,
    TETROMINO_COLORS,
    SHAPES,
    TETROMINO_TYPES,
    LINE_SCORES,
    BASE_SPEED,
    SPEED_DECREASE,
    MIN_SPEED,
    drop_speed,
)


# --- Dimensions ---


class TestDimensions:
    def test_board_dimensions(self):
        assert BOARD_WIDTH == 10
        assert BOARD_HEIGHT == 20

    def test_cell_size(self):
        assert CELL_SIZE == 30

    def test_total_dimensions(self):
        assert TOTAL_WIDTH == BOARD_WIDTH * CELL_SIZE + SIDEBAR_WIDTH + WINDOW_MARGIN  # 454
        assert TOTAL_HEIGHT == BOARD_HEIGHT * CELL_SIZE + WINDOW_MARGIN  # 604

    def test_sidebar_width(self):
        assert SIDEBAR_WIDTH == 150


# --- Colors ---


class TestColors:
    def test_black(self):
        assert BLACK == (0, 0, 0)

    def test_white(self):
        assert WHITE == (255, 255, 255)

    def test_gray(self):
        assert GRAY == (40, 40, 40)

    def test_dark_gray(self):
        assert DARK_GRAY == (30, 30, 30)

    def test_bg_color(self):
        assert BG_COLOR == (20, 20, 20)

    def test_all_tetromino_colors_rgb_tuples(self):
        for name, color in TETROMINO_COLORS.items():
            assert isinstance(color, tuple)
            assert len(color) == 3
            assert all(0 <= c <= 255 for c in color)

    def test_all_seven_types_have_colors(self):
        assert len(TETROMINO_COLORS) == 7
        for t in TETROMINO_TYPES:
            assert t in TETROMINO_COLORS

    def test_specific_colors(self):
        assert TETROMINO_COLORS["I"] == COLOR_I
        assert TETROMINO_COLORS["O"] == COLOR_O
        assert TETROMINO_COLORS["T"] == COLOR_T
        assert TETROMINO_COLORS["S"] == COLOR_S
        assert TETROMINO_COLORS["Z"] == COLOR_Z
        assert TETROMINO_COLORS["J"] == COLOR_J
        assert TETROMINO_COLORS["L"] == COLOR_L


# --- Shapes ---


def _norm(cells):
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return tuple(sorted((r - min_r, c - min_c) for r, c in cells))


def _cw(cells):
    return _norm([(c, -r) for r, c in cells])


class TestShapes:
    def test_all_shapes_have_four_rotations(self):
        for name, states in SHAPES.items():
            assert len(states) == 4, f"{name} has {len(states)} rotation states"

    def test_all_rotations_are_valid_clockwise(self):
        for name, states in SHAPES.items():
            expected = _norm(states[0])
            for i, actual in enumerate(states):
                if i:
                    expected = _cw(expected)
                assert _norm(actual) == expected, (
                    f"{name} rot {i}: expected {expected}, got {_norm(actual)}"
                )

    def test_no_duplicate_shapes_except_symmetric(self):
        """I, S, Z repeat after 180° (period 2). O is period 1. T, J, L must have 4 unique."""
        for name, states in SHAPES.items():
            unique = len(set(_norm(s) for s in states))
            if name in ("O",):
                assert unique == 1
            elif name in ("I", "S", "Z"):
                assert unique == 2
            else:
                assert unique == 4, f"{name} has {unique} unique states"

    def test_each_shape_has_four_cells(self):
        for name, states in SHAPES.items():
            for i, cells in enumerate(states):
                assert len(cells) == 4, f"{name} rot {i} has {len(cells)} cells"

    def test_j_and_l_are_mirror_images_at_rot0(self):
        """At rotation 0, J and L are horizontal mirror images."""
        j_cells = SHAPES["J"][0]
        l_cells = SHAPES["L"][0]
        # Both should have 4 cells in an L-shape
        assert len(j_cells) == len(l_cells) == 4


# --- Scoring ---


class TestScoring:
    def test_line_scores(self):
        assert LINE_SCORES == {1: 100, 2: 300, 3: 500, 4: 800}

    def test_single_line_score(self):
        assert LINE_SCORES[1] == 100

    def test_double_line_score(self):
        assert LINE_SCORES[2] == 300

    def test_triple_line_score(self):
        assert LINE_SCORES[3] == 500

    def test_tetris_score(self):
        assert LINE_SCORES[4] == 800

    def test_default_score_for_zero_lines(self):
        assert LINE_SCORES.get(0, 800) == 800


# --- Speed ---


class TestDropSpeed:
    def test_level_1_speed(self):
        assert drop_speed(1) == 1.0

    def test_level_2_speed(self):
        assert drop_speed(2) == 0.92

    def test_level_10_speed(self):
        expected = max(0.05, 1.0 - 9 * 0.08)
        assert drop_speed(10) == expected

    def test_high_level_minimum(self):
        # At level 13: 1.0 - 12*0.08 = 0.04 -> clamped to 0.05
        assert drop_speed(13) == 0.05
        assert drop_speed(20) == 0.05

    def test_level_11_speed(self):
        expected = max(0.05, 1.0 - 10 * 0.08)
        assert drop_speed(11) == expected

    def test_speed_decreases_with_level(self):
        for level in range(1, 13):
            assert drop_speed(level + 1) < drop_speed(level)


# --- Types ---


class TestTetrominoTypes:
    def test_all_seven_types(self):
        assert TETROMINO_TYPES == ["I", "O", "T", "S", "Z", "J", "L"]

    def test_type_count(self):
        assert len(TETROMINO_TYPES) == 7

    def test_all_types_in_shapes(self):
        for t in TETROMINO_TYPES:
            assert t in SHAPES
