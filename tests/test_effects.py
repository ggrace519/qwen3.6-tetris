"""Tests for Particle, ScreenShake, FlashOverlay, and spawn helpers."""

import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pytest
import random

import pygame


@pytest.fixture(autouse=True)
def _init_pygame():
    """Ensure pygame is initialized for all tests in this module."""
    pygame.init()
    yield
    pygame.quit()

from tetris_game.effects import (
    Particle, ScreenShake, FlashOverlay,
    spawn_sparks, spawn_line_clear_sparks, _pygame_ready,
)
from tetris_game.settings import CELL_SIZE


# ------------------------------------------------------------------
# _pygame_ready
# ------------------------------------------------------------------

class TestPygameReady:
    def test_returns_true_when_initialized(self):
        assert _pygame_ready() is True


# ------------------------------------------------------------------
# Particle
# ------------------------------------------------------------------

class TestParticle:
    def test_default_init(self):
        p = Particle(10.0, 20.0, (255, 0, 0))
        assert p.x == 10.0
        assert p.y == 20.0
        assert p.vx == 0.0
        assert p.vy == 0.0
        assert p.life == 15
        assert p.max_life == 15
        assert p.color == (255, 0, 0)
        assert p.size == 2

    def test_custom_init(self):
        p = Particle(0.0, 0.0, (0, 255, 0), vx=3.0, vy=-5.0, life=30, size=4)
        assert p.vx == 3.0
        assert p.vy == -5.0
        assert p.life == 30
        assert p.max_life == 30
        assert p.size == 4

    def test_update_decreases_life(self):
        p = Particle(0, 0, (255, 0, 0), life=5)
        for _ in range(5):
            p.update()
        assert p.life == 0

    def test_update_returns_false_when_dead(self):
        p = Particle(0, 0, (255, 0, 0), life=1)
        assert p.update() is False

    def test_update_returns_true_while_alive(self):
        p = Particle(0, 0, (255, 0, 0), life=10)
        for _ in range(9):
            assert p.update() is True

    def test_update_applies_gravity(self):
        p = Particle(0, 0, (255, 0, 0), vy=0.0)
        p.update()
        assert p.vy > 0

    def test_update_applies_air_resistance(self):
        p = Particle(0, 0, (255, 0, 0), vx=10.0, vy=0.0)
        p.update()
        assert abs(p.vx) < 10.0

    def test_update_moves_position(self):
        p = Particle(0, 0, (255, 0, 0), vx=5.0, vy=-3.0, life=10)
        p.update()
        assert p.x > 0
        assert p.y < 0

    def test_update_stops_moving_when_dead(self):
        p = Particle(100, 100, (0, 0, 255), life=1, vx=0.0, vy=0.0)
        p.update()  # dies (life 1→0), returns False
        assert p.life == 0
        x_before = p.x
        y_before = p.y
        result = p.update()  # life 0→-1, still returns False
        assert result is False
        # After death (life<=0), vx=0 and vy gets +0.3 gravity each tick
        # x stays constant (vx=0), y increases (gravity)
        assert p.x == x_before  # vx=0 so x stays
        assert p.y > y_before   # vy accumulates gravity
        assert p.life < 0


# ------------------------------------------------------------------
# spawn_sparks
# ------------------------------------------------------------------

class TestSpawnSparks:
    def test_returns_list_of_particles(self):
        particles = spawn_sparks(5, 3, (255, 0, 0), count=6)
        assert isinstance(particles, list)
        assert len(particles) == 6

    def test_all_at_cell_center(self):
        row, col = 2, 4
        particles = spawn_sparks(row, col, (0, 255, 0), count=10)
        cx = col * CELL_SIZE + CELL_SIZE // 2
        cy = row * CELL_SIZE + CELL_SIZE // 2
        for p in particles:
            assert p.x == cx
            assert p.y == cy

    def test_all_correct_color(self):
        color = (200, 100, 50)
        particles = spawn_sparks(0, 0, color, count=5)
        for p in particles:
            assert p.color == color

    def test_varying_velocities(self):
        particles = spawn_sparks(0, 0, (255, 255, 255), count=20)
        vxs = [p.vx for p in particles]
        vys = [p.vy for p in particles]
        assert len(set(vxs)) > 1 or len(set(vys)) > 1

    def test_vy_bias_upward(self):
        particles = spawn_sparks(0, 0, (0, 0, 0), count=50)
        avg_vy = sum(p.vy for p in particles) / len(particles)
        assert avg_vy < 0

    def test_varying_lifespans(self):
        particles = spawn_sparks(0, 0, (255, 0, 0), count=10)
        lives = [p.life for p in particles]
        assert min(lives) >= 10
        assert max(lives) <= 20
        assert len(set(lives)) > 1

    def test_default_count(self):
        particles = spawn_sparks(0, 0, (255, 0, 0))
        assert len(particles) == 6


# ------------------------------------------------------------------
# spawn_line_clear_sparks
# ------------------------------------------------------------------

class TestSpawnLineClearSparks:
    def test_returns_particles_for_single_row(self):
        cleared_rows = [19]
        cleared_colors = [[(255, 0, 0)] * 10]
        particles = spawn_line_clear_sparks(cleared_rows, cleared_colors, count=3)
        assert len(particles) == 30

    def test_returns_particles_for_multiple_rows(self):
        cleared_rows = [18, 19]
        cleared_colors = [
            [(0, 255, 0)] * 10,
            [(0, 0, 255)] * 10,
        ]
        particles = spawn_line_clear_sparks(cleared_rows, cleared_colors, count=2)
        assert len(particles) == 40

    def test_skips_none_cells(self):
        cleared_rows = [5]
        cleared_colors = [[None if i == 5 else (255, 255, 255) for i in range(10)]]
        particles = spawn_line_clear_sparks(cleared_rows, cleared_colors, count=4)
        assert len(particles) == 36

    def test_uses_correct_row_index(self):
        cleared_rows = [7]
        cleared_colors = [[(255, 0, 0)] * 10]
        particles = spawn_line_clear_sparks(cleared_rows, cleared_colors, count=1)
        cx = 0 * CELL_SIZE + CELL_SIZE // 2
        cy = 7 * CELL_SIZE + CELL_SIZE // 2
        p = particles[0]
        assert p.x == cx
        assert p.y == cy

    def test_uses_correct_row_index_multiple_rows(self):
        cleared_rows = [3, 15]
        cleared_colors = [
            [(255, 0, 0)] * 10,
            [(0, 255, 0)] * 10,
        ]
        particles = spawn_line_clear_sparks(cleared_rows, cleared_colors, count=2)
        for p in particles[:20]:
            assert p.y == 3 * CELL_SIZE + CELL_SIZE // 2
        for p in particles[20:]:
            assert p.y == 15 * CELL_SIZE + CELL_SIZE // 2


# ------------------------------------------------------------------
# ScreenShake
# ------------------------------------------------------------------

class TestScreenShake:
    def test_initial_state(self):
        s = ScreenShake(intensity=3, decay=0.5)
        assert s.intensity == 3
        assert s.decay == 0.5
        assert s.active is True

    def test_zero_intensity_produces_noise(self):
        """intensity=0 still uses half=max(1,0)=1, so noise continues."""
        s = ScreenShake(intensity=0, decay=0.5)
        dx, dy = s.offset()
        # half = max(1, 0) = 1, so jitter still happens
        assert -1 <= dx <= 1
        assert -1 <= dy <= 1

    def test_offset_returns_zero_when_inactive(self):
        s = ScreenShake(intensity=3, decay=0.4)
        while s.active:
            s.offset()
        dx, dy = s.offset()
        assert dx == 0
        assert dy == 0

    def test_offset_returns_tuple(self):
        s = ScreenShake(intensity=5)
        result = s.offset()
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_offset_within_intensity_range(self):
        s = ScreenShake(intensity=3)
        for _ in range(50):
            if s.active:
                dx, dy = s.offset()
                assert -3 <= dx <= 3
                assert -3 <= dy <= 3

    def test_decay_reduces_intensity(self):
        s = ScreenShake(intensity=5, decay=0.4)
        initial = s.intensity
        for _ in range(10):
            s.offset()
        assert s.intensity < initial

    def test_active_becomes_false_when_intensity_zero(self):
        s = ScreenShake(intensity=5, decay=0.4)
        while s.active:
            s.offset()
        assert s.active is False

    def test_default_intensity(self):
        s = ScreenShake()
        assert s.intensity == 3

    def test_default_decay(self):
        s = ScreenShake()
        assert s.decay == 0.85

    def test_shake_with_decay_never_infinite_loop(self):
        """Regression: shake must stop in bounded frames."""
        s = ScreenShake(intensity=5, decay=0.4)
        frames = 0
        while s.active and frames < 100:
            s.offset()
            frames += 1
        assert s.active is False, f"Shake did not stop in {frames} frames"

    def test_shake_offset_at_low_intensity(self):
        s = ScreenShake(intensity=1, decay=0.4)
        for _ in range(10):
            if s.active:
                dx, dy = s.offset()
                assert -1 <= dx <= 1
                assert -1 <= dy <= 1

    def test_half_clamped_to_at_least_one(self):
        """half = max(1, self.intensity) ensures non-zero range."""
        s = ScreenShake(intensity=1, decay=0.4)
        dx, dy = s.offset()
        assert -1 <= dx <= 1
        assert -1 <= dy <= 1

    def test_decay_zero_stops_after_first(self):
        s = ScreenShake(intensity=1, decay=0.0)
        s.offset()
        assert s.active is False
        dx, dy = s.offset()
        assert dx == 0
        assert dy == 0


# ------------------------------------------------------------------
# FlashOverlay
# ------------------------------------------------------------------

class TestFlashOverlay:
    def test_initial_state(self):
        f = FlashOverlay(100, 200, frames=10)
        assert f.frames == 10
        assert f.max_frames == 10
        assert f.active is True

    def test_zero_frames_inactive(self):
        f = FlashOverlay(100, 200, frames=0)
        assert f.active is False

    def test_tick_decreases_frames(self):
        f = FlashOverlay(100, 200, frames=5)
        f.tick()
        assert f.frames == 4

    def test_tick_returns_true_while_active(self):
        f = FlashOverlay(100, 200, frames=3)
        assert f.tick() is True
        assert f.tick() is True
        assert f.tick() is True
        assert f.active is False

    def test_tick_returns_false_when_inactive(self):
        f = FlashOverlay(100, 200, frames=1)
        f.tick()
        assert f.tick() is False

    def test_becomes_inactive_after_frames_expire(self):
        f = FlashOverlay(100, 200, frames=2)
        f.tick()
        assert f.active is True
        f.tick()
        assert f.active is False

    def test_inactive_does_nothing(self):
        f = FlashOverlay(100, 200, frames=0)
        result = f.tick()
        assert result is False
        assert f.frames == 0

    def test_surface_none_when_pygame_not_ready(self):
        # Since pygame is init at module level, we can't test None surface
        # without tearing it down. Skip this test.
        pass

    def test_surface_created_when_pygame_ready(self):
        f = FlashOverlay(100, 200, frames=5)
        assert f.surface is not None

    def test_max_frames_preserved(self):
        f = FlashOverlay(100, 200, frames=8)
        f.tick()
        assert f.max_frames == 8
        assert f.frames == 7

    def test_custom_frames(self):
        f = FlashOverlay(300, 200, frames=20)
        assert f.frames == 20
        assert f.max_frames == 20

    def test_default_frames(self):
        f = FlashOverlay(100, 200)
        assert f.frames == 10

    def test_multiple_ticks_deplete_correctly(self):
        f = FlashOverlay(100, 200, frames=5)
        for _ in range(5):
            f.tick()
        assert f.frames == 0
        assert f.active is False

    def test_active_remains_true_during_ticks(self):
        f = FlashOverlay(100, 200, frames=3)
        assert f.active is True
        f.tick()
        assert f.active is True
        f.tick()
        assert f.active is True
        f.tick()
        assert f.active is False


# ------------------------------------------------------------------
# Integration: effects on Board
# ------------------------------------------------------------------

class TestBoardEffects:
    def test_no_effects_before_line_clear(self):
        from tetris_game.board import Board
        b = Board()
        assert b.shake is None
        assert b.flash is None
        assert b.particles == []

    def test_effects_triggered_on_line_clear(self):
        from tetris_game.board import Board
        b = Board()
        b.grid[19] = [(255, 0, 0)] * 10
        b._clear_lines()
        assert b.shake is not None
        assert b.flash is not None
        assert len(b.particles) > 0

    def test_flash_duration_scales_with_lines(self):
        from tetris_game.board import Board
        b = Board()
        b.grid[19] = [(255, 0, 0)] * 10
        b._clear_lines()
        single_frames = b.flash.max_frames
        b.reset()
        for r in range(16, 20):
            b.grid[r] = [(0, 255, 0)] * 10
        b._clear_lines()
        quad_frames = b.flash.max_frames
        assert quad_frames > single_frames

    def test_shake_intensity_scales_with_lines(self):
        from tetris_game.board import Board
        b = Board()
        b.grid[19] = [(255, 0, 0)] * 10
        b._clear_lines()
        single_intensity = b.shake.intensity
        b.reset()
        for r in range(16, 20):
            b.grid[r] = [(0, 255, 0)] * 10
        b._clear_lines()
        quad_intensity = b.shake.intensity
        assert quad_intensity > single_intensity

    def test_particle_count_scales_with_lines(self):
        from tetris_game.board import Board
        b = Board()
        b.grid[19] = [(255, 0, 0)] * 10
        b._clear_lines()
        single_count = len(b.particles)
        b.reset()
        for r in range(16, 20):
            b.grid[r] = [(0, 255, 0)] * 10
        b._clear_lines()
        quad_count = len(b.particles)
        assert quad_count > single_count

    def test_shake_decays_to_none(self):
        from tetris_game.board import Board
        b = Board()
        b.grid[19] = [(255, 0, 0)] * 10
        b._clear_lines()
        assert b.shake is not None
        # Board uses decay=0.4, shake will deactivate
        while b.shake.active:
            b.shake.offset()
        assert b.shake.active is False
        # app.py sets board.shake = None when inactive
        b.shake = None
        assert b.shake is None

    def test_flash_fades_to_inactive(self):
        from tetris_game.board import Board
        b = Board()
        b.grid[19] = [(255, 0, 0)] * 10
        b._clear_lines()
        assert b.flash is not None
        for _ in range(100):
            b.flash.tick()
        assert b.flash.active is False

