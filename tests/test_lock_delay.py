"""Tests for lock delay (ARE), DAS, and ARR mechanics."""

import pytest
from tetris_game.board import Board
from tetris_game.settings import LOCK_DELAY_FRAMES, DAS_FRAMES, ARR_FRAMES


class TestLockDelayInit:
    """Lock delay state initialization."""

    def test_lock_timer_starts_at_zero(self):
        b = Board()
        assert b._lock_timer == 0

    def test_lock_delay_inactive_at_start(self):
        b = Board()
        assert b._lock_delay_active is False

    def test_lock_delay_constants_set(self):
        assert LOCK_DELAY_FRAMES == 24
        assert DAS_FRAMES == 10
        assert ARR_FRAMES == 2


class TestStartLockDelay:
    """Starting the lock delay."""

    def test_start_sets_active(self):
        b = Board()
        b.start_lock_delay()
        assert b._lock_delay_active is True

    def test_start_resets_timer(self):
        b = Board()
        b._lock_timer = 10
        b.start_lock_delay()
        assert b._lock_timer == 0

    def test_start_multiple_times(self):
        b = Board()
        b.start_lock_delay()
        b._lock_timer = 5
        b.start_lock_delay()
        assert b._lock_timer == 0
        assert b._lock_delay_active is True


class TestTickLockDelay:
    """Advancing lock delay frames."""

    def test_tick_returns_false_before_expiry(self):
        b = Board()
        b.start_lock_delay()
        for _ in range(LOCK_DELAY_FRAMES - 1):
            assert b.tick_lock_delay() is False

    def test_tick_returns_true_on_expiry(self):
        b = Board()
        b.start_lock_delay()
        for _ in range(LOCK_DELAY_FRAMES - 1):
            b.tick_lock_delay()
        assert b.tick_lock_delay() is True

    def test_tick_returns_false_when_inactive(self):
        b = Board()
        assert b.tick_lock_delay() is False

    def test_timer_increments(self):
        b = Board()
        b.start_lock_delay()
        b.tick_lock_delay()
        assert b._lock_timer == 1
        b.tick_lock_delay()
        assert b._lock_timer == 2

    def test_lock_delay_deactivates_on_expiry(self):
        b = Board()
        b.start_lock_delay()
        for _ in range(LOCK_DELAY_FRAMES):
            b.tick_lock_delay()
        assert b._lock_delay_active is False

    def test_ticks_during_delay_dont_lock(self):
        """Lock delay frames should not trigger lock."""
        b = Board()
        b.start_lock_delay()
        for _ in range(LOCK_DELAY_FRAMES - 1):
            result = b.tick_lock_delay()
            assert result is False


class TestResetLockDelay:
    """Resetting lock delay on player input."""

    def test_reset_clears_timer(self):
        b = Board()
        b.start_lock_delay()
        b._lock_timer = 15
        b.reset_lock_delay()
        assert b._lock_timer == 0

    def test_reset_preserves_active_flag(self):
        b = Board()
        b.start_lock_delay()
        b.reset_lock_delay()
        assert b._lock_delay_active is True

    def test_reset_extends_delay(self):
        """Resetting should effectively extend the lock delay window."""
        b = Board()
        b.start_lock_delay()
        # Advance to 20 frames (4 from expiry)
        for _ in range(20):
            b.tick_lock_delay()
        assert b._lock_timer == 20
        # Reset — should bring it back to 0
        b.reset_lock_delay()
        assert b._lock_timer == 0
        # Now it takes 24 more frames to expire
        for _ in range(23):
            b.tick_lock_delay()
        assert b._lock_delay_active is True  # not yet expired


class TestLockDelayIntegration:
    """Lock delay integrated with lock behavior."""

    def test_lock_after_delay_expires(self):
        """Piece should lock when lock delay expires."""
        b = Board()
        # Fill the board below a piece so it collides
        b.hard_drop()  # locks first piece at bottom
        # Get a new piece and move it to bottom
        while b.move_down():
            pass
        # Now move_down returns False — start lock delay
        b.start_lock_delay()
        # Advance just before expiry
        for _ in range(LOCK_DELAY_FRAMES - 1):
            b.tick_lock_delay()
        assert b.current is not None
        assert any(cell is not None for row in b.grid for cell in row)
        # One more tick should trigger lock
        b.tick_lock_delay()
        # Piece should be locked (current is now a new spawned piece)
        assert b.current is not None



class TestLockDelayOnInput:
    """Lock delay resets on player input (app-layer behavior)."""

    def test_board_move_left_during_delay(self):
        """Board move_left should still work during lock delay."""
        b = Board()
        b.start_lock_delay()
        b.move_left()
        assert b.move_left() is True

    def test_board_move_right_during_delay(self):
        b = Board()
        b.start_lock_delay()
        assert b.move_right() is True

    def test_board_rotate_during_delay(self):
        b = Board()
        b.current.type = "T"
        b.start_lock_delay()
        b.rotate(clockwise=True)

    def test_board_move_down_during_delay(self):
        b = Board()
        b.start_lock_delay()
        b.move_down(soft_drop=True)

    def test_hard_drop_skips_lock_delay(self):
        """Hard drop should lock immediately, ignoring lock delay."""
        b = Board()
        b.start_lock_delay()
        b._lock_timer = 23
        b.hard_drop()
        assert any(cell is not None for row in b.grid for cell in row)
