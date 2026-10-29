"""Tests for DAS (Delayed Auto-Shift) constants."""

from tetris_game.settings import DAS_FRAMES, ARR_FRAMES


class TestDASARR:
    """DAS and ARR constants."""

    def test_das_frames(self):
        assert DAS_FRAMES == 10

    def test_arr_frames(self):
        assert ARR_FRAMES == 2

    def test_das_slower_than_arr(self):
        """DAS should be longer than ARR (delay before repeat)."""
        assert DAS_FRAMES > ARR_FRAMES
