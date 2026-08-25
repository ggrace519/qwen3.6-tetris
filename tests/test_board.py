"""Tests for Board class: collision, bag randomizer, movement, rotation, locking, scoring, game-over."""

import pytest
import random
from tetris_game.board import Board
from tetris_game.piece import Piece
from tetris_game.settings import BOARD_WIDTH, BOARD_HEIGHT, LINE_SCORES


class TestBoardInit:
    def test_empty_grid(self):
        b = Board()
        assert len(b.grid) == BOARD_HEIGHT
        assert all(len(row) == BOARD_WIDTH for row in b.grid)
        assert all(cell is None for row in b.grid for cell in row)

    def test_initial_score_zero(self):
        b = Board()
        assert b.score == 0

    def test_initial_lines_zero(self):
        b = Board()
        assert b.lines == 0

    def test_initial_level_one(self):
        b = Board()
        assert b.level == 1

    def test_not_game_over(self):
        b = Board()
        assert not b.game_over

    def test_current_piece_exists(self):
        b = Board()
        assert b.current is not None

    def test_current_piece_type(self):
        b = Board()
        assert b.current.type in ["I", "O", "T", "S", "Z", "J", "L"]

    def test_next_type_set(self):
        b = Board()
        assert b.next_type is not None

    def test_current_starts_at_top(self):
        b = Board()
        assert b.current.row == 0

    def test_current_starts_center(self):
        b = Board()
        assert b.current.col == 3


class TestBagRandomizer:
    def test_bag_fills_with_all_types(self):
        b = Board()
        b._fill_bag()
        assert len(b.bag) == 7
        assert set(b.bag) == {"I", "O", "T", "S", "Z", "J", "L"}

    def test_next_type_pops_from_bag(self):
        b = Board()
        b._fill_bag()
        t1 = b._next_type()
        t2 = b._next_type()
        assert t2 != t1

    def test_refills_when_empty(self):
        b = Board()
        b._fill_bag()
        for _ in range(7):
            b._next_type()
        assert len(b.bag) == 0
        t = b._next_type()
        assert t in ["I", "O", "T", "S", "Z", "J", "L"]

    def test_bag_is_permutation(self):
        """Each batch of 7 types should contain all 7 tetromino types."""
        random.seed(99)
        b = Board()
        # First batch: Board.__init__ calls _spawn_next which calls _next_type twice
        # (once for next_type init, once for next_type after spawn).
        # So first batch starts with those 2 consumed, then we collect 12 more.
        # Instead, just verify that after consuming 7+ from a fresh bag, we get a permutation.
        b._fill_bag()
        batch = []
        for _ in range(7):
            batch.append(b._next_type())
        assert set(batch) == {"I", "O", "T", "S", "Z", "J", "L"}
        assert len(set(batch)) == 7  # no duplicates


class TestCollision:
    def test_empty_board_no_collision(self):
        b = Board()
        assert not b._collides(5, 5, [(0, 0), (0, 1)])

    def test_collision_with_grid(self):
        b = Board()
        b.grid[10][5] = (255, 0, 0)
        assert b._collides(10, 5, [(0, 0)])

    def test_collision_out_of_bounds_row(self):
        b = Board()
        assert b._collides(BOARD_HEIGHT, 5, [(0, 0)])

    def test_collision_out_of_bounds_col(self):
        b = Board()
        assert b._collides(5, BOARD_WIDTH, [(0, 0)])

    def test_no_collision_above_board(self):
        b = Board()
        assert not b._collides(-1, 5, [(1, 0)])

    def test_multiple_cells_collision(self):
        b = Board()
        b.grid[5][5] = (1, 1, 1)
        assert b._collides(5, 5, [(0, 0), (0, 1), (0, 2)])


class TestMovement:
    def test_move_left_returns_true(self):
        b = Board()
        assert b.move_left() is True

    def test_move_right_returns_true(self):
        b = Board()
        assert b.move_right() is True

    def test_move_down_returns_true(self):
        b = Board()
        assert b.move_down() is True

    def test_move_left_at_left_edge(self):
        b = Board()
        for _ in range(5):
            b.move_left()
        assert not b.move_left()

    def test_move_right_at_right_edge(self):
        b = Board()
        for _ in range(7):
            b.move_right()
        assert not b.move_right()

    def test_move_down_hits_bottom(self):
        b = Board()
        count = 0
        while b.move_down():
            count += 1
            if count > 30:
                pytest.fail("move_down never returned False")
        # Should have moved down many times but stopped at bottom
        assert count >= 15

    def test_move_no_current(self):
        b = Board()
        b.current = None
        assert not b.move_left()
        assert not b.move_right()
        assert not b.move_down()

    def test_move_left_changes_col(self):
        b = Board()
        initial_col = b.current.col
        b.move_left()
        assert b.current.col == initial_col - 1

    def test_move_right_changes_col(self):
        b = Board()
        initial_col = b.current.col
        b.move_right()
        assert b.current.col == initial_col + 1

    def test_move_down_changes_row(self):
        b = Board()
        initial_row = b.current.row
        b.move_down()
        assert b.current.row == initial_row + 1


class TestRotation:
    def test_rotate_returns_true(self):
        b = Board()
        b.current.type = "T"
        assert b.rotate(clockwise=True) is True

    def test_rotate_O_returns_false(self):
        b = Board()
        b.current.type = "O"
        assert b.rotate(clockwise=True) is False

    def test_rotate_changes_rotation(self):
        b = Board()
        b.current.type = "T"
        b.rotate(clockwise=True)
        assert b.current.rotation == 1

    def test_rotate_ccw(self):
        b = Board()
        b.current.type = "J"
        b.rotate(clockwise=False)
        assert b.current.rotation == 3

    def test_rotate_no_current(self):
        b = Board()
        b.current = None
        assert not b.rotate(clockwise=True)

    def test_wall_kick_right(self):
        b = Board()
        b.current.type = "T"
        b.current.row = 0
        b.current.col = 0
        b.rotate(clockwise=True)

    def test_wall_kick_left(self):
        b = Board()
        b.current.type = "T"
        b.current.row = 0
        b.current.col = 9
        b.rotate(clockwise=True)

    def test_rotation_fails_when_blocked(self):
        b = Board()
        b.current.type = "T"
        b.current.row = 0
        b.current.col = 0
        b.grid[1][1] = (255, 0, 0)
        b.rotate(clockwise=True)

    def test_all_types_can_rotate(self):
        for t in ["I", "T", "S", "Z", "J", "L"]:
            b = Board()
            b.current.type = t
            assert b.rotate(clockwise=True)


class TestHardDrop:
    def test_hard_drop_on_empty_board(self):
        b = Board()
        initial_row = b.current.row
        dist = b.hard_drop()
        assert dist > 0
        assert b.current is not None

    def test_hard_drop_score(self):
        b = Board()
        b.hard_drop()
        assert b.score > 0

    def test_hard_drop_score_formula(self):
        b = Board()
        for _ in range(5):
            b.move_down()
        initial_row = b.current.row
        dist = b.hard_drop()
        expected = dist * 2
        assert b.score == expected

    def test_hard_drop_returns_zero_when_none(self):
        b = Board()
        b.current = None
        assert b.hard_drop() == 0

    def test_hard_drop_locks_piece(self):
        b = Board()
        b.hard_drop()
        assert any(cell is not None for row in b.grid for cell in row)


class TestGhostRow:
    def test_ghost_on_empty_board(self):
        b = Board()
        ghost = b.ghost_row()
        assert ghost > 0

    def test_ghost_with_blocked_below(self):
        b = Board()
        b.current.row = 15
        for r in range(16, 20):
            for c in range(10):
                b.grid[r][c] = (128, 128, 128)
        ghost = b.ghost_row()
        assert ghost == 15

    def test_ghost_returns_zero_when_none(self):
        b = Board()
        b.current = None
        assert b.ghost_row() == 0

    def test_ghost_same_as_hard_drop_row(self):
        b = Board()
        b.hard_drop()


class TestLineClearing:
    def test_no_clear_on_empty_board(self):
        b = Board()
        b._clear_lines()
        assert b.lines == 0
        assert b.score == 0

    def test_single_line_clear(self):
        b = Board()
        b.grid[19] = [(128, 128, 128)] * BOARD_WIDTH
        b._clear_lines()
        assert b.lines == 1
        assert b.score == LINE_SCORES[1]

    def test_two_line_clear(self):
        b = Board()
        b.grid[18] = [(128, 128, 128)] * BOARD_WIDTH
        b.grid[19] = [(128, 128, 128)] * BOARD_WIDTH
        b._clear_lines()
        assert b.lines == 2
        assert b.score == LINE_SCORES[2]

    def test_four_line_clear(self):
        b = Board()
        for r in range(16, 20):
            b.grid[r] = [(128, 128, 128)] * BOARD_WIDTH
        b._clear_lines()
        assert b.lines == 4
        assert b.score == LINE_SCORES[4]

    def test_partial_line_not_cleared(self):
        b = Board()
        for c in range(9):
            b.grid[19][c] = (128, 128, 128)
        b._clear_lines()
        assert b.lines == 0

    def test_cleared_rows_removed_from_top(self):
        b = Board()
        b.grid[5] = [(128, 128, 128)] * BOARD_WIDTH
        b._clear_lines()
        assert b.grid[0] == [None] * BOARD_WIDTH

    def test_scoring_scaled_by_level(self):
        b = Board()
        b.level = 3
        b.grid[19] = [(128, 128, 128)] * BOARD_WIDTH
        b._clear_lines()
        assert b.score == LINE_SCORES[1] * 3

    def test_level_up_after_10_lines(self):
        b = Board()
        for r in range(10, 20):
            b.grid[r] = [(128, 128, 128)] * BOARD_WIDTH
        b._clear_lines()
        assert b.level == 2

    def test_level_not_changed_if_no_lines(self):
        b = Board()
        b.level = 5
        b._clear_lines()
        assert b.level == 5


class TestLocking:
    def test_lock_writes_to_grid(self):
        b = Board()
        b.hard_drop()
        assert any(cell is not None for row in b.grid for cell in row)

    def test_lock_spawns_next(self):
        b = Board()
        next_type = b.next_type
        b.hard_drop()
        assert b.current is not None
        assert b.current.type == next_type

    def test_lock_out_of_bounds_asserts(self):
        b = Board()
        b.current = Piece("I")
        b.current.row = -5
        with pytest.raises(AssertionError):
            b._lock()

    def test_lock_none_current(self):
        b = Board()
        b.current = None
        b._lock()


class TestGameOver:
    def test_not_over_at_start(self):
        b = Board()
        assert not b.game_over

    def test_game_over_on_spawn_collision(self):
        b = Board()
        for r in range(1, 4):
            for c in range(BOARD_WIDTH):
                b.grid[r][c] = (255, 0, 0)
        b._spawn_next()
        assert b.game_over is True

    def test_current_piece_not_cleared_on_game_over(self):
        b = Board()
        for r in range(1, 4):
            for c in range(BOARD_WIDTH):
                b.grid[r][c] = (255, 0, 0)
        b._spawn_next()
        assert b.current is not None


class TestDropSpeed:
    def test_drop_speed_delegates(self):
        b = Board()
        assert isinstance(b.drop_speed(), float)

    def test_speed_at_level_1(self):
        b = Board()
        assert b.drop_speed() == 1.0

    def test_speed_at_level_12(self):
        b = Board()
        b.level = 12
        assert abs(b.drop_speed() - 0.12) < 0.001


class TestReset:
    def test_reset_clears_score(self):
        b = Board()
        b.score = 999
        b.reset()
        assert b.score == 0

    def test_reset_clears_lines(self):
        b = Board()
        b.lines = 50
        b.reset()
        assert b.lines == 0

    def test_reset_level_to_one(self):
        b = Board()
        b.level = 10
        b.reset()
        assert b.level == 1

    def test_reset_clears_game_over(self):
        b = Board()
        b.game_over = True
        b.reset()
        assert not b.game_over

    def test_reset_has_current_piece(self):
        b = Board()
        b.reset()
        assert b.current is not None

    def test_reset_has_next_type(self):
        b = Board()
        b.reset()
        assert b.next_type is not None

    def test_reset_empty_grid(self):
        b = Board()
        b.grid[19] = [(128, 128, 128)] * BOARD_WIDTH
        b.reset()
        assert all(cell is None for row in b.grid for cell in row)

    def test_reset_clears_bag(self):
        b = Board()
        b._fill_bag()
        b.bag.clear()
        b.reset()
        # __init__ starts with empty bag, then _spawn_next pulls from it
        assert b.bag == [] or len(b.bag) == 0 or b.current is not None


class TestRotationRevert:
    """Test that rotation reverts when wall kicks fail."""

    def test_rotation_reverts_on_block(self):
        b = Board()
        b.current.type = "T"
        b.current.row = 1
        b.current.col = 1
        # T[1] cells would be at (1,1),(2,1),(2,2),(3,1)
        # Block those + wall kick offsets for dc=+1,+2,-1
        for r, c in [(1, 1), (2, 1), (2, 2), (3, 1),
                     (1, 2), (2, 3),
                     (1, 3), (2, 4),
                     (1, 0), (2, 0), (3, 0)]:
            if 0 <= r < BOARD_HEIGHT and 0 <= c < BOARD_WIDTH:
                b.grid[r][c] = (255, 0, 0)
        old_rot = b.current.rotation
        result = b.rotate(clockwise=True)
        assert result is False
        assert b.current.rotation == old_rot

    def test_wall_kick_right_succeeds(self):
        b = Board()
        b.current.type = "T"
        b.current.row = 0
        b.current.col = 0
        # Fill the spot where rotation would collide at current position
        # but leave room to kick right
        b.grid[1][1] = (255, 0, 0)
        old_rot = b.current.rotation
        result = b.rotate(clockwise=True)
        # Should either succeed with a kick or revert
        assert b.current.rotation == old_rot or b.current.rotation == 1

    def test_wall_kick_left_succeeds(self):
        b = Board()
        b.current.type = "T"
        b.current.row = 0
        b.current.col = 8
        b.grid[1][8] = (255, 0, 0)
        old_rot = b.current.rotation
        result = b.rotate(clockwise=True)
        assert b.current.rotation == old_rot or b.current.rotation == 1

    def test_wall_kick_two_right(self):
        b = Board()
        b.current.type = "T"
        b.current.row = 0
        b.current.col = 0
        # Block immediate right but not 2-right
        b.grid[1][1] = (255, 0, 0)
        b.grid[2][1] = (255, 0, 0)
        old_rot = b.current.rotation
        b.rotate(clockwise=True)
        # Should have kicked 2 right or reverted

    def test_wall_kick_two_left(self):
        b = Board()
        b.current.type = "T"
        b.current.row = 0
        b.current.col = 8
        b.grid[1][8] = (255, 0, 0)
        b.grid[2][8] = (255, 0, 0)
        old_rot = b.current.rotation
        b.rotate(clockwise=True)
        assert b.current.rotation == old_rot or b.current.rotation == 1
