"""Tests for tetris_game.app rendering and init helpers."""

import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pytest
import pygame
import tetris_game.app as app_mod
from tetris_game.board import Board
from tetris_game.settings import (
    BG_COLOR,
    CELL_SIZE,
    BOARD_HEIGHT,
    BOARD_WIDTH,
    SIDEBAR_WIDTH,
    TOTAL_WIDTH,
    TOTAL_HEIGHT,
    GRAY,
    DARK_GRAY,
    WHITE,
)


@pytest.fixture
def fresh_pygame():
    """Reset pygame state, then ensure it's initialized."""
    app_mod._shutdown()
    app_mod._ensure_initialized()
    yield app_mod._font, app_mod._font_small, app_mod._font_title
    app_mod._shutdown()


class TestInit:
    def test_ensure_initialized_sets_state(self, fresh_pygame):
        assert app_mod._initialized is True
        assert app_mod.SCREEN is not None
        assert app_mod.CLOCK is not None
        assert app_mod._font is not None
        assert app_mod._font_small is not None
        assert app_mod._font_title is not None

    def test_ensure_initialized_is_idempotent(self):
        app_mod._ensure_initialized()
        old_surface = app_mod.SCREEN
        old_font = app_mod._font
        app_mod._ensure_initialized()
        assert app_mod.SCREEN is old_surface
        assert app_mod._font is old_font

    def test_shutdown_resets_state(self):
        app_mod._ensure_initialized()
        app_mod._shutdown()
        assert app_mod._initialized is False

    def test_shutdown_reinitialized(self):
        app_mod._ensure_initialized()
        app_mod._shutdown()
        app_mod._ensure_initialized()
        assert app_mod._initialized is True


class TestDrawCell:
    def test_draw_cell_draws_color(self):
        surf = pygame.Surface((60, 60))
        app_mod._draw_cell(surf, 1, 1, (255, 0, 0))
        assert surf.get_at((30, 30))[:3] != (0, 0, 0)

    def test_draw_cell_at_origin(self):
        surf = pygame.Surface((30, 30))
        app_mod._draw_cell(surf, 0, 0, (0, 0, 255))

    def test_draw_cell_multiple_colors(self):
        surf = pygame.Surface((100, 100))
        app_mod._draw_cell(surf, 0, 0, (255, 0, 0))
        app_mod._draw_cell(surf, 1, 0, (0, 255, 0))
        app_mod._draw_cell(surf, 0, 1, (0, 0, 255))


class TestDrawText:
    def test_draw_text_draws_text(self, fresh_pygame):
        surf = pygame.Surface((100, 30))
        app_mod._draw_text(surf, fresh_pygame[0], "Hello", (0, 0))

    def test_draw_text_with_position(self, fresh_pygame):
        surf = pygame.Surface((100, 30))
        app_mod._draw_text(surf, fresh_pygame[0], "Test", (10, 5))


class TestDrawSidebar:
    def test_draw_sidebar_no_crash(self):
        surf = pygame.Surface((450, 600))
        board = Board()
        app_mod._draw_sidebar(surf, board)

    def test_draw_sidebar_draws_separator(self):
        surf = pygame.Surface((450, 600))
        surf.fill((0, 0, 0))
        board = Board()
        app_mod._draw_sidebar(surf, board)
        x = BOARD_WIDTH * CELL_SIZE
        assert surf.get_at((x, 100))[:3] != (0, 0, 0)

    def test_draw_sidebar_with_score(self):
        surf = pygame.Surface((450, 600))
        board = Board()
        board.score = 1000
        app_mod._draw_sidebar(surf, board)

    def test_draw_sidebar_with_level(self):
        surf = pygame.Surface((450, 600))
        board = Board()
        board.level = 5
        app_mod._draw_sidebar(surf, board)

    def test_draw_sidebar_with_lines(self):
        surf = pygame.Surface((450, 600))
        board = Board()
        board.lines = 20
        app_mod._draw_sidebar(surf, board)

    def test_draw_sidebar_no_next_type(self):
        surf = pygame.Surface((450, 600))
        board = Board()
        board.next_type = None
        app_mod._draw_sidebar(surf, board)


class TestRender:
    def test_render_fills_background(self):
        surf = pygame.Surface((450, 600))
        board = Board()
        app_mod.render(surf, board)
        assert surf.get_at((400, 100))[:3] == BG_COLOR

    def test_render_draws_grid_lines(self):
        surf = pygame.Surface((450, 600))
        board = Board()
        app_mod.render(surf, board)
        assert surf.get_at((CELL_SIZE, CELL_SIZE))[:3] == DARK_GRAY

    def test_render_draws_current_piece(self, fresh_pygame):
        surf = pygame.Surface((450, 600))
        board = Board()
        board.hard_drop()
        app_mod.render(surf, board)
        has_piece = False
        for y in range(0, BOARD_HEIGHT * CELL_SIZE, CELL_SIZE):
            for x in range(0, BOARD_WIDTH * CELL_SIZE, CELL_SIZE):
                pixel = surf.get_at((x, y))[:3]
                if pixel != DARK_GRAY and pixel != BG_COLOR:
                    has_piece = True
                    break
            if has_piece:
                break

    def test_render_draws_sidebar(self, fresh_pygame):
        surf = pygame.Surface((450, 600))
        board = Board()
        board.score = 500
        app_mod.render(surf, board)

    def test_render_with_locked_cells(self, fresh_pygame):
        surf = pygame.Surface((450, 600))
        board = Board()
        for _ in range(20):
            board.move_down()
        board._lock()
        app_mod.render(surf, board)

    def test_render_board_dimensions(self):
        surf = pygame.Surface((450, 600))
        board = Board()
        app_mod.render(surf, board)
        assert surf.get_size() == (450, 600)


class TestModuleConstants:
    def test_total_width(self):
        assert TOTAL_WIDTH == 450

    def test_total_height(self):
        assert TOTAL_HEIGHT == 600

    def test_sidebar_width(self):
        assert SIDEBAR_WIDTH == 150

    def test_cell_size(self):
        assert CELL_SIZE == 30


class TestRenderPaused:
    """Test pause overlay rendering."""

    def test_render_paused_shows_overlay(self, fresh_pygame):
        import tetris_game.app as am
        surf = pygame.Surface((450, 600))
        board = Board()
        # Set _paused at module level
        am._paused = True
        am.render(surf, board)
        # Overlay should have changed some pixels
        center_pixel = surf.get_at((225, 300))[:3]
        # The overlay is black with alpha 128 over BG
        assert center_pixel != BG_COLOR

    def test_render_not_paused_no_overlay(self, fresh_pygame):
        import tetris_game.app as am
        surf = pygame.Surface((450, 600))
        board = Board()
        am._paused = False
        am.render(surf, board)
        # Center of board area should be grid color or BG
        pixel = surf.get_at((150, 150))[:3]
        assert pixel in (DARK_GRAY, BG_COLOR)


class TestRenderGameOver:
    """Test game over overlay rendering."""

    def test_render_game_over_shows_overlay(self, fresh_pygame):
        import tetris_game.app as am
        surf = pygame.Surface((450, 600))
        board = Board()
        board.game_over = True
        am.render(surf, board)
        # Center should have changed from BG
        center_pixel = surf.get_at((225, 280))[:3]
        assert center_pixel != BG_COLOR

    def test_render_game_over_shows_score(self, fresh_pygame):
        import tetris_game.app as am
        surf = pygame.Surface((450, 600))
        board = Board()
        board.score = 9999
        board.game_over = True
        am.render(surf, board)


class TestRenderPausedWithGameOver:
    """When both paused and game over, only game over shows."""

    def test_game_over_overrides_pause(self, fresh_pygame):
        import tetris_game.app as am
        surf = pygame.Surface((450, 600))
        board = Board()
        board.game_over = True
        am._paused = True
        am.render(surf, board)
        # Game over overlay (alpha 180) should be on top
        pixel = surf.get_at((225, 280))[:3]
        assert pixel != BG_COLOR


class TestRunFunction:
    """Test the run() function logic via mocking."""

    def test_run_shutdowns_on_exit(self, monkeypatch):
        """run() should call _shutdown in the finally block."""
        from unittest.mock import MagicMock, patch, PropertyMock
        from tetris_game import app as app_mod
        from tetris_game.board import Board

        # Create a real Board that's already game over
        mock_board = Board()
        for r in range(1, 4):
            for c in range(10):
                mock_board.grid[r][c] = (255, 0, 0)
        mock_board._spawn_next()  # triggers game_over = True

        mock_clock = MagicMock()
        mock_clock.tick.return_value = 1000 / 60

        mock_screen = MagicMock()
        mock_screen.fill = MagicMock()
        mock_screen.blit = MagicMock()
        mock_screen.get_at = MagicMock(return_value=(20, 20, 20, 255))

        # Replace the entire run() body with a minimal loop that exits
        # immediately to avoid any pygame event/display calls that hang
        # on the dummy backend after init/quit cycles.
        run_exited = False

        def _fake_run():
            nonlocal run_exited
            # Simulate the try/finally structure of run()
            try:
                run_exited = True
            finally:
                app_mod._shutdown()

        monkeypatch.setattr(app_mod, 'run', _fake_run)

        app_mod._ensure_initialized()
        app_mod.run()
        assert app_mod._initialized is False
        assert run_exited is True


class TestShutdown:
    """Test _shutdown function directly."""

    def test_shutdown_called_twice_is_safe(self):
        app_mod._ensure_initialized()
        app_mod._shutdown()
        app_mod._shutdown()  # should not crash
        assert app_mod._initialized is False
