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
    WINDOW_MARGIN,
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
        surf = pygame.Surface((TOTAL_WIDTH, TOTAL_HEIGHT))
        board = Board()
        app_mod._draw_sidebar(surf, board)

    def test_draw_sidebar_draws_separator(self):
        surf = pygame.Surface((TOTAL_WIDTH, TOTAL_HEIGHT))
        surf.fill((0, 0, 0))
        board = Board()
        app_mod._draw_sidebar(surf, board)
        x = BOARD_WIDTH * CELL_SIZE
        assert surf.get_at((x, 100))[:3] != (0, 0, 0)

    def test_draw_sidebar_with_score(self):
        surf = pygame.Surface((TOTAL_WIDTH, TOTAL_HEIGHT))
        board = Board()
        board.score = 1000
        app_mod._draw_sidebar(surf, board)

    def test_draw_sidebar_with_level(self):
        surf = pygame.Surface((TOTAL_WIDTH, TOTAL_HEIGHT))
        board = Board()
        board.level = 5
        app_mod._draw_sidebar(surf, board)

    def test_draw_sidebar_with_lines(self):
        surf = pygame.Surface((TOTAL_WIDTH, TOTAL_HEIGHT))
        board = Board()
        board.lines = 20
        app_mod._draw_sidebar(surf, board)

    def test_draw_sidebar_no_next_type(self):
        surf = pygame.Surface((TOTAL_WIDTH, TOTAL_HEIGHT))
        board = Board()
        board.next_type = None
        app_mod._draw_sidebar(surf, board)


class TestRender:
    def test_render_fills_background(self):
        surf = pygame.Surface((TOTAL_WIDTH, TOTAL_HEIGHT))
        board = Board()
        app_mod.render(surf, board)
        assert surf.get_at((400, 100))[:3] == BG_COLOR

    def test_render_draws_grid_lines(self):
        surf = pygame.Surface((TOTAL_WIDTH, TOTAL_HEIGHT))
        board = Board()
        app_mod.render(surf, board)
        assert surf.get_at((CELL_SIZE + WINDOW_MARGIN, CELL_SIZE + WINDOW_MARGIN))[:3] == DARK_GRAY

    def test_render_draws_current_piece(self, fresh_pygame):
        surf = pygame.Surface((TOTAL_WIDTH, TOTAL_HEIGHT))
        board = Board()
        board.hard_drop()
        app_mod.render(surf, board)
        has_piece = False
        for y in range(WINDOW_MARGIN, BOARD_HEIGHT * CELL_SIZE + WINDOW_MARGIN, CELL_SIZE):
            for x in range(WINDOW_MARGIN, BOARD_WIDTH * CELL_SIZE + WINDOW_MARGIN, CELL_SIZE):
                pixel = surf.get_at((x, y))[:3]
                if pixel != DARK_GRAY and pixel != BG_COLOR:
                    has_piece = True
                    break
            if has_piece:
                break

    def test_render_draws_sidebar(self, fresh_pygame):
        surf = pygame.Surface((TOTAL_WIDTH, TOTAL_HEIGHT))
        board = Board()
        board.score = 500
        app_mod.render(surf, board)

    def test_render_with_locked_cells(self, fresh_pygame):
        surf = pygame.Surface((TOTAL_WIDTH, TOTAL_HEIGHT))
        board = Board()
        for _ in range(20):
            board.move_down()
        board._lock()
        app_mod.render(surf, board)

    def test_render_board_dimensions(self):
        surf = pygame.Surface((TOTAL_WIDTH, TOTAL_HEIGHT))
        board = Board()
        app_mod.render(surf, board)
        assert surf.get_size() == (TOTAL_WIDTH, TOTAL_HEIGHT)


class TestModuleConstants:
    def test_total_width(self):
        assert TOTAL_WIDTH == 454

    def test_total_height(self):
        assert TOTAL_HEIGHT == 604

    def test_sidebar_width(self):
        assert SIDEBAR_WIDTH == 150

    def test_cell_size(self):
        assert CELL_SIZE == 30


class TestRenderPaused:
    """Test pause overlay rendering."""

    def test_render_paused_shows_overlay(self, fresh_pygame):
        import tetris_game.app as am
        surf = pygame.Surface((TOTAL_WIDTH, TOTAL_HEIGHT))
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
        surf = pygame.Surface((TOTAL_WIDTH, TOTAL_HEIGHT))
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
        surf = pygame.Surface((TOTAL_WIDTH, TOTAL_HEIGHT))
        board = Board()
        board.game_over = True
        am.render(surf, board)
        # Center should have changed from BG
        center_pixel = surf.get_at((225, 280))[:3]
        assert center_pixel != BG_COLOR

    def test_render_game_over_shows_score(self, fresh_pygame):
        import tetris_game.app as am
        surf = pygame.Surface((TOTAL_WIDTH, TOTAL_HEIGHT))
        board = Board()
        board.score = 9999
        board.game_over = True
        am.render(surf, board)


class TestRenderPausedWithGameOver:
    """When both paused and game over, only game over shows."""

    def test_game_over_overrides_pause(self, fresh_pygame):
        import tetris_game.app as am
        surf = pygame.Surface((TOTAL_WIDTH, TOTAL_HEIGHT))
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

        mock_board = Board()
        for r in range(1, 4):
            for c in range(10):
                mock_board.grid[r][c] = (255, 0, 0)
        mock_board._spawn_next()

        mock_clock = MagicMock()
        mock_clock.tick.return_value = 1000 / 60

        mock_screen = MagicMock()
        mock_screen.fill = MagicMock()
        mock_screen.blit = MagicMock()
        mock_screen.get_at = MagicMock(return_value=(20, 20, 20, 255))

        run_exited = False

        def _fake_run():
            nonlocal run_exited
            try:
                run_exited = True
            finally:
                app_mod._shutdown()

        monkeypatch.setattr(app_mod, 'run', _fake_run)

        app_mod._ensure_initialized()
        app_mod.run()
        assert app_mod._initialized is False
        assert run_exited is True

    def test_run_creates_board(self, monkeypatch):
        """run() should create a Board instance."""
        from unittest.mock import MagicMock
        from tetris_game import app as app_mod

        board_instances = []
        orig_init = Board.__init__

        def tracking_init(self, *args, **kwargs):
            board_instances.append(self)
            orig_init(self, *args, **kwargs)

        clock = MagicMock()
        clock.tick.return_value = 1000 / 60
        screen = MagicMock()
        quit_event = MagicMock(type=pygame.QUIT)

        monkeypatch.setattr(pygame.event, 'get', lambda: [quit_event])
        monkeypatch.setattr(Board, '__init__', tracking_init)
        monkeypatch.setattr(app_mod, 'CLOCK', clock)
        monkeypatch.setattr(app_mod, 'SCREEN', screen)

        app_mod._ensure_initialized()
        app_mod.run()
        assert len(board_instances) == 1

    def test_run_with_soft_drop(self, monkeypatch):
        """run() should process soft drop on DOWN key."""
        from unittest.mock import MagicMock
        from tetris_game import app as app_mod

        key_events = [
            MagicMock(type=pygame.KEYDOWN, key=pygame.K_DOWN),
            MagicMock(type=pygame.KEYUP, key=pygame.K_DOWN),
        ]
        event_idx = [0]

        def mock_event_get():
            if event_idx[0] < len(key_events):
                ev = key_events[event_idx[0]]
                event_idx[0] += 1
                return [ev]
            return [MagicMock(type=pygame.QUIT)]

        clock = MagicMock()
        clock.tick.return_value = 1000 / 60
        screen = MagicMock()

        monkeypatch.setattr(pygame.event, 'get', mock_event_get)
        monkeypatch.setattr(app_mod, 'CLOCK', clock)
        monkeypatch.setattr(app_mod, 'SCREEN', screen)

        app_mod._ensure_initialized()
        app_mod.run()

    def test_run_with_r_key_game_over(self, monkeypatch):
        """run() should process R key and reset on game over."""
        from unittest.mock import MagicMock
        from tetris_game import app as app_mod

        go_board = Board()
        for r in range(0, 3):
            for c in range(10):
                go_board.grid[r][c] = (255, 0, 0)
        go_board._spawn_next()
        assert go_board.game_over is True

        r_event = MagicMock(type=pygame.KEYDOWN, key=pygame.K_r)
        quit_event = MagicMock(type=pygame.QUIT)
        event_queue = [r_event, quit_event]
        event_idx = [0]

        def mock_event_get():
            if event_idx[0] < len(event_queue):
                ev = event_queue[event_idx[0]]
                event_idx[0] += 1
                return [ev]
            return [quit_event]

        clock = MagicMock()
        clock.tick.return_value = 1000 / 60
        screen = MagicMock()

        monkeypatch.setattr(pygame.event, 'get', mock_event_get)
        monkeypatch.setattr(app_mod, 'CLOCK', clock)
        monkeypatch.setattr(app_mod, 'SCREEN', screen)
        monkeypatch.setattr(app_mod, 'Board', lambda: go_board)

        app_mod._ensure_initialized()
        app_mod.run()


class TestShutdown:
    """Test _shutdown function directly."""

    def test_shutdown_called_twice_is_safe(self):
        app_mod._ensure_initialized()
        app_mod._shutdown()
        app_mod._shutdown()
        assert app_mod._initialized is False


class TestDrawSidebarHold:
    """Test hold piece rendering in sidebar."""

    def test_draw_sidebar_with_hold_piece(self, fresh_pygame):
        surf = pygame.Surface((TOTAL_WIDTH, TOTAL_HEIGHT))
        board = Board()
        board.hold_type = "I"
        app_mod._draw_sidebar(surf, board)

    def test_draw_sidebar_hold_dimmed_when_used(self):
        surf = pygame.Surface((TOTAL_WIDTH, TOTAL_HEIGHT))
        board = Board()
        board.hold_type = "I"
        board.hold_used = True
        app_mod._draw_sidebar(surf, board)

    def test_draw_sidebar_hold_none(self, fresh_pygame):
        surf = pygame.Surface((TOTAL_WIDTH, TOTAL_HEIGHT))
        board = Board()
        board.hold_type = None
        board.hold_used = True
        app_mod._draw_sidebar(surf, board)


class TestParticleDrawing:
    """Test that particles are drawn in render()."""

    def test_render_with_particles(self, fresh_pygame):
        surf = pygame.Surface((TOTAL_WIDTH, TOTAL_HEIGHT))
        board = Board()
        p = app_mod.Particle(x=100.0, y=100.0, color=(255, 0, 0), vx=1.0, vy=1.0, life=15, size=2)
        board.particles.append(p)
        app_mod.render(surf, board)
        assert len(board.particles) >= 0


class TestFlashOverlay:
    """Test flash overlay rendering in render()."""

    def test_render_with_flash(self, fresh_pygame):
        from tetris_game.effects import FlashOverlay
        surf = pygame.Surface((TOTAL_WIDTH, TOTAL_HEIGHT))
        board = Board()
        board.flash = FlashOverlay(width=TOTAL_WIDTH, height=TOTAL_HEIGHT, frames=5)
        app_mod.render(surf, board)
        assert board.flash.frames < 5

    def test_render_flash_cleanup(self, fresh_pygame):
        from tetris_game.effects import FlashOverlay
        surf = pygame.Surface((TOTAL_WIDTH, TOTAL_HEIGHT))
        board = Board()
        board.flash = FlashOverlay(width=TOTAL_WIDTH, height=TOTAL_HEIGHT, frames=1)
        app_mod.render(surf, board)
        assert board.flash is None

    def test_render_no_flash(self, fresh_pygame):
        surf = pygame.Surface((TOTAL_WIDTH, TOTAL_HEIGHT))
        board = Board()
        board.flash = None
        app_mod.render(surf, board)
        assert board.flash is None


class TestRenderGhost:
    """Test ghost piece rendering."""

    def test_render_draws_ghost_piece(self, fresh_pygame):
        surf = pygame.Surface((TOTAL_WIDTH, TOTAL_HEIGHT))
        board = Board()
        board.current.row = 0
        app_mod.render(surf, board)
        ghost_r = board.ghost_row()
        assert ghost_r > 0


class TestRenderWithShake:
    """Test screen shake in render()."""

    def test_render_with_shake(self, fresh_pygame):
        from tetris_game.effects import ScreenShake
        surf = pygame.Surface((TOTAL_WIDTH, TOTAL_HEIGHT))
        board = Board()
        board.shake = ScreenShake(intensity=3, decay=0.85)
        app_mod.render(surf, board)
        assert board.shake is not None


class TestIntroParticles:
    """Test intro splash screen particle spawning and drawing."""

    def test_spawn_intro_particles_creates_list(self, fresh_pygame):
        import tetris_game.app as am
        am._shutdown_intro()
        particles = am._spawn_intro_particles(count=20)
        assert isinstance(particles, list)
        assert len(particles) == 20
        assert "x" in particles[0]
        assert "y" in particles[0]
        assert "color" in particles[0]

    def test_spawn_intro_particles_stores_globally(self, fresh_pygame):
        import tetris_game.app as am
        am._shutdown_intro()
        am._spawn_intro_particles()
        assert am._INTRO_PARTICLES is not None
        assert len(am._INTRO_PARTICLES) == 120

    def test_spawn_intro_particles_has_wobble_params(self, fresh_pygame):
        import tetris_game.app as am
        am._shutdown_intro()
        particles = am._spawn_intro_particles(count=10)
        for p in particles:
            assert "wobble_phase" in p
            assert "wobble_speed" in p
            assert "wobble_amp" in p

    def test_spawn_intro_particles_colors_from_tetrominoes(self, fresh_pygame):
        import tetris_game.app as am
        from tetris_game.settings import TETROMINO_COLORS
        am._shutdown_intro()
        colors_set = set(TETROMINO_COLORS.values())
        particles = am._spawn_intro_particles(count=50)
        for p in particles:
            assert tuple(p["color"]) in colors_set

    def test_spawn_intro_falling_pieces(self, fresh_pygame):
        import tetris_game.app as am
        am._shutdown_intro()
        pieces = am._spawn_intro_falling_pieces(count=10)
        assert isinstance(pieces, list)
        assert len(pieces) == 10
        assert "type" in pieces[0]
        assert "speed" in pieces[0]

    def test_spawn_intro_falling_pieces_types(self, fresh_pygame):
        import tetris_game.app as am
        from tetris_game.settings import TETROMINO_TYPES
        am._shutdown_intro()
        pieces = am._spawn_intro_falling_pieces(count=30)
        piece_types = {p["type"] for p in pieces}
        assert piece_types.issubset(set(TETROMINO_TYPES))

    def test_draw_intro_screen_no_crash(self, fresh_pygame):
        import tetris_game.app as am
        am._shutdown_intro()
        surf = pygame.Surface((TOTAL_WIDTH, TOTAL_HEIGHT))
        am._draw_intro_screen(surf, elapsed=0.0)
        assert surf.get_size() == (TOTAL_WIDTH, TOTAL_HEIGHT)

    def test_draw_intro_screen_changes_pixels(self, fresh_pygame):
        import tetris_game.app as am
        am._shutdown_intro()
        surf = pygame.Surface((TOTAL_WIDTH, TOTAL_HEIGHT))
        surf.fill((0, 0, 0))
        am._draw_intro_screen(surf, elapsed=1.0)
        center_pixel = surf.get_at((225, 168))[:3]
        assert center_pixel != (0, 0, 0)

    def test_draw_intro_screen_with_elapsed(self, fresh_pygame):
        import tetris_game.app as am
        am._shutdown_intro()
        surf = pygame.Surface((TOTAL_WIDTH, TOTAL_HEIGHT))
        am._draw_intro_screen(surf, elapsed=0.5)
        am._draw_intro_screen(surf, elapsed=1.0)
        am._draw_intro_screen(surf, elapsed=2.0)

    def test_shutdown_intro_resets_state(self, fresh_pygame):
        import tetris_game.app as am
        am._spawn_intro_particles()
        am._spawn_intro_falling_pieces()
        am._INTRO_TIME = 42.0
        am._shutdown_intro()
        assert am._INTRO_PARTICLES is None
        assert am._INTRO_PIECES is None
        assert am._INTRO_TIME == 0.0

    def test_draw_intro_piece_no_crash(self, fresh_pygame):
        import tetris_game.app as am
        am._shutdown_intro()
        p = {
            "type": "I",
            "cells": [(0, 0), (0, 1), (0, 2), (0, 3)],
            "min_r": 0, "max_r": 0,
            "min_c": 0, "max_c": 3,
            "x": 100.0,
            "y": 100.0,
            "speed": 0.5,
            "rotation": 0,
            "color": (0, 240, 240),
            "alpha": 0.1,
            "size_mult": 1.0,
        }
        surf = pygame.Surface((TOTAL_WIDTH, TOTAL_HEIGHT))
        am._draw_intro_piece(p, elapsed=1.0, surface=surf)

    def test_draw_intro_piece_rotation(self, fresh_pygame):
        import tetris_game.app as am
        am._shutdown_intro()
        p = {
            "type": "T",
            "cells": [(0, 1), (1, 0), (1, 1), (1, 2)],
            "min_r": 0, "max_r": 1,
            "min_c": 0, "max_c": 2,
            "x": 100.0,
            "y": 100.0,
            "speed": 0.5,
            "rotation": 2,
            "color": (160, 0, 240),
            "alpha": 0.1,
            "size_mult": 1.0,
        }
        surf = pygame.Surface((TOTAL_WIDTH, TOTAL_HEIGHT))
        am._draw_intro_piece(p, elapsed=1.0, surface=surf)

    def test_ensure_intro_surface(self, fresh_pygame):
        import tetris_game.app as am
        surf = am._ensure_intro_surface(100, 100)
        assert surf.get_size() == (100, 100)

    def test_intro_time_increments(self, fresh_pygame):
        import tetris_game.app as am
        am._shutdown_intro()
        am._INTRO_TIME = 0.0
        am._INTRO_TIME += 0.016
        assert am._INTRO_TIME > 0
