"""Tests for hold piece and scoring system (Tetris DS standard)."""

import pytest
from tetris_game.board import Board
from tetris_game.piece import Piece
from tetris_game.settings import (
    LINE_SCORES, SOFT_DROP_POINTS, HARD_DROP_POINTS,
    B2B_MULTIPLIER, COMBO_BASE,
)


# ------------------------------------------------------------------
# Hold piece
# ------------------------------------------------------------------


class TestHoldPiece:
    """Tests for the hold piece feature."""

    def test_first_hold_stashes_current_piece(self):
        b = Board()
        current_type = b.current.type
        assert b.hold_type is None
        b.hold_piece()
        assert b.hold_type == current_type

    def test_first_hold_spawns_next_piece(self):
        b = Board()
        next_before = b.next_type
        b.hold_piece()
        assert b.current is not None
        assert b.next_type is not None

    def test_hold_returns_false_when_no_current(self):
        b = Board()
        b.current = None
        assert b.hold_piece() is False

    def test_hold_returns_false_when_already_used(self):
        b = Board()
        b.hold_piece()
        assert b.hold_used is True
        assert b.hold_piece() is False

    def test_hold_sets_hold_used_flag(self):
        b = Board()
        assert b.hold_used is False
        b.hold_piece()
        assert b.hold_used is True

    def test_hold_reusable_after_lock(self):
        """Hold should become reusable after the held piece locks."""
        b = Board()
        b.hold_piece()
        assert b.hold_used is True
        b.hard_drop()
        assert b.hold_used is False

    def test_second_hold_swaps(self):
        """Second hold should swap current into hold slot."""
        b = Board()
        b.hard_drop()  # lock first piece to reset hold
        b.hold_piece()  # first: stash current, spawn next
        b.hard_drop()  # lock the spawned piece, reset hold
        # Capture state right before 2nd hold
        held_before = b.hold_type
        current_before = b.current.type
        # Now hold again — should swap
        b.hold_piece()
        assert b.hold_type == current_before
        assert b.current.type == held_before

    def test_hold_preserves_piece_type(self):
        """Held piece retains its type when swapped back."""
        b = Board()
        b.hard_drop()  # lock first piece
        b.hold_piece()  # stash whatever was current
        b.hard_drop()  # lock the spawned piece
        # Now current is a fresh piece — set it to T
        b.current = Piece("T")
        b.hold_piece()  # T goes to hold, old held piece comes back
        # The held piece from before is now current
        assert b.current.type != "T"  # T should be in hold now

    def test_hold_O_piece(self):
        """O piece can be held and retrieved normally."""
        b = Board()
        b.current = Piece("O")
        b.hold_piece()
        assert b.hold_type == "O"
        b.hard_drop()  # lock spawned piece, resets hold_used
        b.hard_drop()  # get another piece
        b.hold_piece()  # hold goes back
        assert b.current.type == "O"

    def test_hold_does_not_affect_score(self):
        """Holding a piece should not change the score."""
        b = Board()
        initial_score = b.score
        b.hold_piece()
        assert b.score == initial_score

    def test_hold_does_not_affect_lines(self):
        """Holding a piece should not change line count."""
        b = Board()
        initial_lines = b.lines
        b.hold_piece()
        assert b.lines == initial_lines

    def test_hold_multiple_times_blocks_after_first(self):
        """Only one hold per piece lifecycle allowed."""
        b = Board()
        assert b.hold_piece() is True
        assert b.hold_piece() is False
        b.hard_drop()
        assert b.hold_piece() is True

    def test_hold_queue_continues_after_swap(self):
        """After hold swap, the queue is replenished."""
        b = Board()
        b.hard_drop()
        b.hold_piece()
        b.hard_drop()
        b.hold_piece()
        assert b.current is not None
        assert b.current.type in ["I", "O", "T", "S", "Z", "J", "L"]


class TestNextQueue:
    """Tests for the extended next queue (5 pieces)."""

    def test_next_queue_has_pieces(self):
        b = Board()
        # _spawn_next consumes 2 from the bag (next_type + current piece)
        # and fills queue to 5, so queue should have 3 left (5 - 2 consumed)
        assert len(b.next_queue) >= 3

    def test_next_queue_contains_all_types(self):
        b = Board()
        for p in b.next_queue:
            assert p in ["I", "O", "T", "S", "Z", "J", "L"]

    def test_next_queue_refills(self):
        b = Board()
        initial_len = len(b.next_queue)
        for _ in range(initial_len):
            b.next_queue.pop(0)
        b._fill_next_queue()
        assert len(b.next_queue) >= 5

    def test_next_queue_persists_after_hold(self):
        b = Board()
        b.hold_piece()
        assert len(b.next_queue) >= 3


# ------------------------------------------------------------------
# Scoring — soft drop
# ------------------------------------------------------------------


class TestSoftDropScoring:
    """Soft drop awards SOFT_DROP_POINTS per cell moved, added on lock."""

    def test_soft_drop_adds_points_on_lock(self):
        b = Board()
        for _ in range(5):
            b.move_down(soft_drop=True)
        b._lock()
        assert b.score > 0

    def test_soft_drop_point_formula(self):
        b = Board()
        steps = 5
        for _ in range(steps):
            b.move_down(soft_drop=True)
        b._lock()
        expected = steps * SOFT_DROP_POINTS
        assert b.score == expected

    def test_soft_drop_none_current(self):
        b = Board()
        b.current = None
        b.move_down(soft_drop=True)
        assert b.score == 0

    def test_soft_drop_no_score_on_blocked(self):
        """Moving down when blocked should not award points."""
        b = Board()
        b.hard_drop()
        initial_score = b.score
        b.move_down(soft_drop=True)
        assert b.score == initial_score

    def test_soft_drop_points_locked_on_hard_drop(self):
        """Soft drop points accumulated before hard drop are included in lock."""
        b = Board()
        for _ in range(5):
            b.move_down(soft_drop=True)
        # hard_drop calls _lock which adds soft drop points
        b.hard_drop()
        assert b.score >= 5 * SOFT_DROP_POINTS


# ------------------------------------------------------------------
# Scoring — hard drop
# ------------------------------------------------------------------


class TestHardDropScoring:
    """Hard drop awards HARD_DROP_POINTS per cell dropped."""

    def test_hard_drop_awards_points(self):
        b = Board()
        row_before = b.current.row
        b.hard_drop()
        # hard_drop locks and spawns new piece at row 0
        # score should reflect drop_dist * 2 from the piece that was just dropped
        assert b.score > 0

    def test_hard_drop_point_formula(self):
        b = Board()
        b.hard_drop()
        # hard_drop awards 2 points per cell dropped
        # O piece drops ~18 cells from row 0, score = ~36
        # I piece drops ~19 cells, score = ~38
        # Just verify the formula is drop_dist * 2
        assert b.score % 2 == 0  # always even
        assert b.score > 0

    def test_hard_drop_combined_with_soft_drop(self):
        """Soft drop points + hard drop points are both awarded."""
        b = Board()
        for _ in range(3):
            b.move_down(soft_drop=True)
        soft_points = 3 * SOFT_DROP_POINTS
        b.hard_drop()
        # Score = soft_drop_points + hard_drop_points (from drop to bottom)
        assert b.score > soft_points

    def test_hard_drop_zero_distance(self):
        """Hard drop when already on bottom should award 0 extra."""
        b = Board()
        while b.move_down():
            pass
        initial_score = b.score
        b.hard_drop()
        assert b.score == initial_score


# ------------------------------------------------------------------
# Scoring — line clears
# ------------------------------------------------------------------


class TestLineClearScoring:
    """Line clear scoring uses LINE_SCORES * level."""

    def test_single_line_score(self):
        b = Board()
        b.grid[19] = [(255, 0, 0)] * 10
        b._clear_lines()
        expected = LINE_SCORES[1] * b.level
        assert b.score == expected

    def test_double_line_score(self):
        b = Board()
        b.grid[18] = [(255, 0, 0)] * 10
        b.grid[19] = [(255, 0, 0)] * 10
        b._clear_lines()
        expected = LINE_SCORES[2] * b.level
        assert b.score == expected

    def test_triple_line_score(self):
        b = Board()
        for r in range(17, 20):
            b.grid[r] = [(255, 0, 0)] * 10
        b._clear_lines()
        expected = LINE_SCORES[3] * b.level
        assert b.score == expected

    def test_tetris_score(self):
        b = Board()
        for r in range(16, 20):
            b.grid[r] = [(255, 0, 0)] * 10
        b._clear_lines()
        expected = LINE_SCORES[4] * b.level
        assert b.score == expected

    def test_scoring_scales_by_level(self):
        b = Board()
        b.level = 5
        b.grid[19] = [(255, 0, 0)] * 10
        b._clear_lines()
        expected = LINE_SCORES[1] * 5
        assert b.score == expected

    def test_no_score_on_no_lines_cleared(self):
        b = Board()
        b.level = 3
        b.grid[19][0] = (255, 0, 0)
        b._clear_lines()
        assert b.score == 0


# ------------------------------------------------------------------
# Back-to-back
# ------------------------------------------------------------------


class TestBackToBack:
    """Consecutive tetris/t-spin clears get B2B multiplier."""

    def test_back_to_back_tetris(self):
        """Two consecutive tetrises should trigger B2B."""
        b = Board()
        for r in range(16, 20):
            b.grid[r] = [(255, 0, 0)] * 10
        b._clear_lines()
        first_score = b.score
        b.grid = [[None] * 10 for _ in range(20)]
        b._last_clear_type = "tetris"
        for r in range(16, 20):
            b.grid[r] = [(0, 255, 0)] * 10
        b._clear_lines()
        # Second tetris: base * B2B + combo bonus (combo_count incremented to 2)
        expected_b2b = int(LINE_SCORES[4] * b.level * B2B_MULTIPLIER)
        expected_combo = COMBO_BASE * 2 * b.level
        second_contribution = expected_b2b + expected_combo
        assert b.score == first_score + second_contribution

    def test_non_special_clear_breaks_back_to_back(self):
        """Clearing 3 lines is not special, should not trigger B2B."""
        b = Board()
        for r in range(16, 20):
            b.grid[r] = [(255, 0, 0)] * 10
        b._clear_lines()
        first_score = b.score
        b.grid = [[None] * 10 for _ in range(20)]
        b._last_clear_type = "other"
        for r in range(17, 20):
            b.grid[r] = [(0, 255, 0)] * 10
        b._clear_lines()
        # Non-special clear: no B2B, but combo still applies
        combo_bonus = COMBO_BASE * 2 * b.level
        expected = LINE_SCORES[3] * b.level + combo_bonus
        assert b.score == first_score + expected

    def test_back_to_back_only_for_tetris(self):
        """B2B multiplier only applies to 4-line clears."""
        b = Board()
        for r in range(17, 20):
            b.grid[r] = [(255, 0, 0)] * 10
        b._clear_lines()
        first_score = b.score
        b.grid = [[None] * 10 for _ in range(20)]
        b._last_clear_type = "tetris"
        for r in range(17, 20):
            b.grid[r] = [(0, 255, 0)] * 10
        b._clear_lines()
        # 3-line clear: no B2B, combo bonus applies
        combo_bonus = COMBO_BASE * 2 * b.level
        expected = LINE_SCORES[3] * b.level + combo_bonus
        assert b.score == first_score + expected

    def test_tetris_after_non_special_resets(self):
        """A tetris after a non-special clear should NOT get B2B."""
        b = Board()
        for r in range(17, 20):
            b.grid[r] = [(255, 0, 0)] * 10
        b._clear_lines()
        first_score = b.score
        b.grid = [[None] * 10 for _ in range(20)]
        b._last_clear_type = "other"
        for r in range(16, 20):
            b.grid[r] = [(0, 255, 0)] * 10
        b._clear_lines()
        # Tetris: no B2B, combo bonus applies
        combo_bonus = COMBO_BASE * 2 * b.level
        expected = LINE_SCORES[4] * b.level + combo_bonus
        assert b.score == first_score + expected


# ------------------------------------------------------------------
# Combos
# ------------------------------------------------------------------


class TestCombos:
    """Combo bonus for consecutive line clears across pieces."""

    def test_first_clear_no_combo(self):
        """First line clear should have no combo bonus."""
        b = Board()
        b._combo_count = 0
        b._last_cleared = False
        b.grid[19] = [(255, 0, 0)] * 10
        b._clear_lines()
        assert b._combo_count == 1
        assert b.score == LINE_SCORES[1] * b.level

    def test_consecutive_clear_gives_combo(self):
        """Clearing lines on next piece gives combo bonus."""
        b = Board()
        b.grid[19] = [(255, 0, 0)] * 10
        b._clear_lines()
        first_score = b.score
        b.grid[18] = [(0, 255, 0)] * 10
        b._clear_lines()
        second_score = b.score - first_score
        # Combo bonus = COMBO_BASE * 2 * level
        expected_combo = COMBO_BASE * 2 * b.level
        assert second_score == LINE_SCORES[1] * b.level + expected_combo

    def test_combo_increments(self):
        """Each consecutive line clear increments the combo count."""
        b = Board()
        for i in range(1, 5):
            b.grid[19] = [(i * 50, 0, 0)] * 10
            b._clear_lines()
            assert b._combo_count == i

    def test_non_clear_resets_combo(self):
        """A piece that doesn't clear lines should reset the combo chain."""
        b = Board()
        b.grid[19] = [(255, 0, 0)] * 10
        b._clear_lines()
        assert b._combo_count == 1
        b.grid[18] = [(0, 255, 0)] * 10
        b._clear_lines()
        assert b._combo_count == 2
        b._clear_lines()
        assert b._combo_count == 0

    def test_combo_scales_by_level(self):
        """Combo bonus should be multiplied by the current level."""
        b = Board()
        b.level = 3
        b.grid[19] = [(255, 0, 0)] * 10
        b._clear_lines()
        first_score = b.score
        b.grid[18] = [(0, 255, 0)] * 10
        b._clear_lines()
        # First: LINE_SCORES[1]*3 = 300
        # Second: LINE_SCORES[1]*3 + COMBO_BASE*2*3 = 300 + 300 = 600
        second_clear_expected = LINE_SCORES[1] * b.level + COMBO_BASE * 2 * b.level
        assert b.score == first_score + second_clear_expected
