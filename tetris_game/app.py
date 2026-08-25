"""Pygame window, input handling, rendering, pause logic, and main game loop."""

import math
import random
import pygame
import sys

from .board import Board
from .settings import (
    BLACK,
    WHITE,
    GRAY,
    DARK_GRAY,
    BG_COLOR,
    CELL_SIZE,
    BOARD_HEIGHT,
    BOARD_WIDTH,
    SIDEBAR_WIDTH,
    TOTAL_WIDTH,
    TOTAL_HEIGHT,
    WINDOW_MARGIN,
    SHAPES,
    TETROMINO_COLORS,
    TETROMINO_TYPES,
)
from .effects import Particle


# Module-level game objects — created on first call to run()
SCREEN = None
CLOCK = None
_font = None
_font_small = None
_font_title = None
_initialized = False


def _ensure_initialized():
    global SCREEN, CLOCK, _font, _font_small, _font_title, _initialized
    if _initialized:
        return
    pygame.init()
    pygame.display.set_caption("Python Tetris")
    SCREEN = pygame.display.set_mode((TOTAL_WIDTH, TOTAL_HEIGHT))
    CLOCK = pygame.time.Clock()
    _font = pygame.freetype.Font(None, size=28)
    _font_small = pygame.freetype.Font(None, size=20)
    _font_title = pygame.freetype.Font(None, size=36)
    _initialized = True


def _shutdown():
    global _initialized
    pygame.quit()
    _initialized = False


def _draw_cell(surface, row, col, color):
    """Draw a single cell with a slight bevel effect."""
    x = col * CELL_SIZE
    y = row * CELL_SIZE
    rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
    pygame.draw.rect(surface, color, rect)
    # Highlight edge
    pygame.draw.rect(
        surface,
        tuple(min(255, c + 40) for c in color),
        rect,
        1,
    )
    # Shadow edge
    pygame.draw.rect(
        surface,
        tuple(max(0, c - 40) for c in color),
        rect,
        2,
    )


def _draw_text(surface, font, text, pos, color=WHITE):
    """Draw text at a position on the surface."""
    font.render_to(surface, pos, text, fgcolor=color)


def _draw_sidebar(surface, board, margin=0):
    """Draw the sidebar: title, hold piece, next piece, score, level, lines."""
    sidebar_x = BOARD_WIDTH * CELL_SIZE + margin
    m = margin

    # Separator line
    pygame.draw.line(surface, GRAY, (sidebar_x, m), (sidebar_x, TOTAL_HEIGHT - m), 2)

    y_offset = 20 + m

    # Title
    _draw_text(surface, _font_title, "TETRIS",
               (sidebar_x + SIDEBAR_WIDTH // 2 - 40, y_offset))
    y_offset += 45

    # Hold piece label
    _draw_text(surface, _font_small, "HOLD",
               (sidebar_x + 10, y_offset))
    y_offset += 30

    # Draw hold piece
    if board.hold_type:
        cells = SHAPES[board.hold_type][0]
        piece_color = TETROMINO_COLORS[board.hold_type]
        # Dim the piece if hold already used this turn
        if board.hold_used:
            piece_color = tuple(max(0, c - 120) for c in piece_color)
        min_r = min(r for r, _ in cells)
        max_r = max(r for r, _ in cells)
        min_c = min(c for _, c in cells)
        max_c = max(c for _, c in cells)
        piece_h = (max_r - min_r + 1) * CELL_SIZE
        piece_w = (max_c - min_c + 1) * CELL_SIZE
        start_x = (sidebar_x + SIDEBAR_WIDTH - piece_w) // 2
        start_y = y_offset + (60 - piece_h) // 2

        for dr, dc in cells:
            x = start_x + (dc - min_c) * CELL_SIZE
            y = start_y + (dr - min_r) * CELL_SIZE
            rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(surface, piece_color, rect)
            pygame.draw.rect(
                surface,
                tuple(min(255, c + 40) for c in piece_color),
                rect,
                1,
            )

    y_offset += 95

    # Next piece label
    _draw_text(surface, _font_small, "NEXT",
               (sidebar_x + 10, y_offset))
    y_offset += 30

    # Draw next piece
    if board.next_type:
        cells = SHAPES[board.next_type][0]
        piece_color = TETROMINO_COLORS[board.next_type]
        min_r = min(r for r, _ in cells)
        max_r = max(r for r, _ in cells)
        min_c = min(c for _, c in cells)
        max_c = max(c for _, c in cells)
        piece_h = (max_r - min_r + 1) * CELL_SIZE
        piece_w = (max_c - min_c + 1) * CELL_SIZE
        start_x = (sidebar_x + SIDEBAR_WIDTH - piece_w) // 2
        start_y = y_offset + (60 - piece_h) // 2

        for dr, dc in cells:
            x = start_x + (dc - min_c) * CELL_SIZE
            y = start_y + (dr - min_r) * CELL_SIZE
            rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(surface, piece_color, rect)
            pygame.draw.rect(
                surface,
                tuple(min(255, c + 40) for c in piece_color),
                rect,
                1,
            )

    y_offset += 95

    # Score
    _draw_text(surface, _font_small, "SCORE",
               (sidebar_x + 10, y_offset))
    y_offset += 25
    _draw_text(surface, _font, str(board.score),
               (sidebar_x + 10, y_offset))
    y_offset += 40

    # Level
    _draw_text(surface, _font_small, "LEVEL",
               (sidebar_x + 10, y_offset))
    y_offset += 25
    _draw_text(surface, _font, str(board.level),
               (sidebar_x + 10, y_offset))
    y_offset += 40

    # Lines
    _draw_text(surface, _font_small, "LINES",
               (sidebar_x + 10, y_offset))
    y_offset += 25
    _draw_text(surface, _font, str(board.lines),
               (sidebar_x + 10, y_offset))


_paused = False

# ------------------------------------------------------------------
# Intro splash screen
# ------------------------------------------------------------------

_INTRO_PARTICLES = None
_INTRO_PIECES = None
_INTRO_TIME = 0.0


def _ensure_intro_surface(width: int, height: int):
    """Create a back-buffer for intro rendering."""
    buf = pygame.Surface((width, height))
    buf.fill(BG_COLOR)
    return buf


def _spawn_intro_particles(count: int = 120):
    """Create colorful floating particles for the intro background."""
    global _INTRO_PARTICLES
    particles = []
    for _ in range(count):
        particles.append({
            "x": random.uniform(0, TOTAL_WIDTH),
            "y": random.uniform(0, TOTAL_HEIGHT),
            "vx": random.uniform(-0.3, 0.3),
            "vy": random.uniform(-0.5, -0.1),
            "size": random.uniform(1.5, 4.0),
            "color": random.choice(list(TETROMINO_COLORS.values())),
            "alpha": random.uniform(0.15, 0.5),
            "wobble_phase": random.uniform(0, 2 * math.pi),
            "wobble_speed": random.uniform(0.02, 0.06),
            "wobble_amp": random.uniform(0.3, 1.0),
        })
    _INTRO_PARTICLES = particles
    return particles


def _spawn_intro_falling_pieces(count: int = 15):
    """Create falling tetromino silhouettes for the intro background."""
    global _INTRO_PIECES
    pieces = []
    for _ in range(count):
        ptype = random.choice(TETROMINO_TYPES)
        cells = SHAPES[ptype][0]
        min_r = min(r for r, _ in cells)
        max_r = max(r for r, _ in cells)
        min_c = min(c for _, c in cells)
        max_c = max(c for _, c in cells)
        pieces.append({
            "type": ptype,
            "cells": cells,
            "min_r": min_r, "max_r": max_r,
            "min_c": min_c, "max_c": max_c,
            "x": random.uniform(0, TOTAL_WIDTH - 80),
            "y": random.uniform(-200, -20),
            "speed": random.uniform(0.3, 1.0),
            "rotation": random.randint(0, 3),
            "color": TETROMINO_COLORS[ptype],
            "alpha": random.uniform(0.06, 0.15),
            "size_mult": random.uniform(0.7, 1.3),
        })
    _INTRO_PIECES = pieces
    return pieces


def _draw_intro_piece(p, elapsed, surface):
    """Draw a single falling intro piece with rotation and bobbing."""
    cell_sz = CELL_SIZE * p["size_mult"]
    bob_y = math.sin(elapsed * 1.5 + p["x"] * 0.01) * 8.0
    rot_cells = SHAPES[p["type"]][int(p["rotation"]) % 4]
    for dr, dc in rot_cells:
        px = int(p["x"] + (dc - p["min_c"]) * cell_sz)
        py = int(p["y"] + (dr - p["min_r"]) * cell_sz + bob_y)
        rect = pygame.Rect(px, py, int(cell_sz), int(cell_sz))
        alpha_surf = pygame.Surface((int(cell_sz), int(cell_sz)), pygame.SRCALPHA)
        alpha_surf.fill((*p["color"], int(255 * p["alpha"])))
        surface.blit(alpha_surf, rect.topleft)


def _draw_intro_screen(surface: pygame.Surface, elapsed: float):
    """Draw the full intro splash screen. Mutates surface in place."""
    surface.fill(BG_COLOR)

    # ── Background particles ──
    if _INTRO_PARTICLES is None:
        _spawn_intro_particles()
    for p in _INTRO_PARTICLES:
        p["x"] += p["vx"] + math.sin(elapsed * p["wobble_speed"] + p["wobble_phase"]) * p["wobble_amp"]
        p["y"] += p["vy"]
        if p["y"] < -10:
            p["y"] = TOTAL_HEIGHT + 10
        if p["x"] < -10:
            p["x"] = TOTAL_WIDTH + 10
        elif p["x"] > TOTAL_WIDTH + 10:
            p["x"] = -10
        s = max(1, round(p["size"] * p["alpha"]))
        alpha_val = int(255 * p["alpha"])
        color = (*p["color"], alpha_val)
        pygame.draw.rect(surface, color, (int(p["x"]), int(p["y"]), s, s))

    # ── Falling tetromino silhouettes ──
    if _INTRO_PIECES is None:
        _spawn_intro_falling_pieces()
    for p in _INTRO_PIECES:
        p["y"] += p["speed"]
        p["rotation"] = (p["rotation"] + 0.02) % 4
        if p["y"] > TOTAL_HEIGHT + 50:
            p["y"] = -50
            p["x"] = random.uniform(0, TOTAL_WIDTH - 80)
        _draw_intro_piece(p, elapsed, surface)

    # ── Title "TETRIS" with glow ──
    title_y = int(TOTAL_HEIGHT * 0.22)
    title_x = TOTAL_WIDTH // 2 - 50

    for glow in range(5, 0, -1):
        glow_surf = pygame.Surface((160, 50), pygame.SRCALPHA)
        _draw_text(glow_surf, _font_title, "TETRIS", (0, 0))
        glow_surf.set_alpha(int(40 / glow))
        surface.blit(glow_surf, (title_x, title_y))

    hue_t = math.sin(elapsed * 1.2) * 0.5 + 0.5
    r = int(200 + 55 * hue_t)
    g = int(80 + 80 * (1.0 - hue_t))
    b = int(240 - 100 * hue_t)
    _draw_text(surface, _font_title, "TETRIS", (title_x, title_y), color=(r, g, b))

    # ── Start button ──
    btn_w = 160
    btn_h = 36
    btn_x = TOTAL_WIDTH // 2 - btn_w // 2
    btn_y = title_y + 100
    pulse = math.sin(elapsed * 3.0) * 0.5 + 0.5
    btn_color = tuple(int(c * 0.7 + 60 * pulse) for c in TETROMINO_COLORS["I"])
    btn_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
    pygame.draw.rect(surface, btn_color, btn_rect, border_radius=6)
    pygame.draw.rect(surface, WHITE, btn_rect, 2, border_radius=6)
    btn_surf = pygame.Surface((160, 30), pygame.SRCALPHA)
    _draw_text(btn_surf, _font, "START", (0, 0), color=BG_COLOR)
    surface.blit(btn_surf, (btn_x + 20, btn_y + 3))

    # ── Decorative line ──
    line_y = title_y + 150
    line_w = int(160 + 40 * math.sin(elapsed * 2.0))
    line_color_alpha = int(180 + 75 * math.sin(elapsed * 1.5))
    pygame.draw.line(surface, (255, 255, 255, line_color_alpha),
                       (TOTAL_WIDTH // 2 - line_w // 2, line_y),
                       (TOTAL_WIDTH // 2 + line_w // 2, line_y), 2)

    # ── Controls section ──
    controls_y = int(TOTAL_HEIGHT * 0.46)
    _draw_text(surface, _font_small, "CONTROLS", (TOTAL_WIDTH // 2 - 30, controls_y),
               color=GRAY)
    controls_y += 25

    controls = [
        ("← →", "Move"),
        ("↑ / X", "Rotate CW"),
        ("Z", "Rotate CCW"),
        ("Space", "Hard Drop"),
        ("C / Shift", "Hold"),
        ("↓", "Soft Drop"),
        ("P", "Pause"),
        ("Esc", "Quit"),
    ]
    for key, desc in controls:
        key_surf = pygame.Surface((80, 20), pygame.SRCALPHA)
        _draw_text(key_surf, _font_small, key, (0, 0), color=WHITE)
        val_surf = pygame.Surface((100, 20), pygame.SRCALPHA)
        _draw_text(val_surf, _font_small, desc, (0, 0), color=GRAY)
        surface.blit(key_surf, (TOTAL_WIDTH // 2 - 100, controls_y))
        surface.blit(val_surf, (TOTAL_WIDTH // 2 + 20, controls_y))
        controls_y += 20

    # ── Animated tetromino showcase ──
    showcase_y = int(TOTAL_HEIGHT * 0.78)
    for i, (ptype, color) in enumerate(zip(TETROMINO_TYPES, TETROMINO_COLORS.values())):
        rot = int(elapsed * 0.8 + i * 0.7) % 4
        cells = SHAPES[ptype][rot]
        min_r = min(r for r, _ in cells)
        max_r = max(r for r, _ in cells)
        min_c = min(c for _, c in cells)
        max_c = max(c for _, c in cells)
        piece_w = (max_c - min_c + 1) * 12
        spacing = TOTAL_WIDTH // (len(TETROMINO_TYPES) + 1)
        px = spacing * (i + 1) - piece_w // 2
        py = showcase_y + int(math.sin(elapsed * 2.0 + i) * 5)
        for dr, dc in cells:
            cx = px + (dc - min_c) * 12
            cy = py + (dr - min_r) * 12
            rect = pygame.Rect(cx, cy, 12, 12)
            pygame.draw.rect(surface, color, rect)
            pygame.draw.rect(surface,
                              tuple(min(255, c + 40) for c in color),
                              rect, 1)

    # ── Corner accents ──
    accent_t = int(elapsed * 200) % 256
    corner_size = 8
    for cx, cy in [(0, 0), (TOTAL_WIDTH - corner_size, 0),
                    (0, TOTAL_HEIGHT - corner_size),
                    (TOTAL_WIDTH - corner_size, TOTAL_HEIGHT - corner_size)]:
        accent_surf = pygame.Surface((corner_size, corner_size), pygame.SRCALPHA)
        accent_color = (*TETROMINO_COLORS[TETROMINO_TYPES[accent_t % 7]], 120)
        pygame.draw.rect(accent_surf, accent_color, accent_surf.get_rect())
        surface.blit(accent_surf, (cx, cy))


def _shutdown_intro():
    """Reset intro state when transitioning to gameplay."""
    global _INTRO_PARTICLES, _INTRO_PIECES, _INTRO_TIME
    _INTRO_PARTICLES = None
    _INTRO_PIECES = None
    _INTRO_TIME = 0.0


def render(surface: pygame.Surface, board: Board):
    """Clear screen and draw the entire game state (with effects)."""
    surface.fill(BG_COLOR)
    m = WINDOW_MARGIN

    # Grid background
    for r in range(BOARD_HEIGHT):
        for c in range(BOARD_WIDTH):
            x = c * CELL_SIZE + m
            y = r * CELL_SIZE + m
            rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(surface, DARK_GRAY, rect, 1)
            if board.grid[r][c] is not None:
                _draw_cell(surface, r, c, board.grid[r][c])

    # Ghost piece (where the active piece will land)
    current = board.current
    if current and not board.game_over:
        ghost_r = board.ghost_row()
        for dr, dc in current.cells():
            gr = ghost_r + dr
            gc = current.col + dc
            if 0 <= gr < BOARD_HEIGHT and 0 <= gc < BOARD_WIDTH:
                x = gc * CELL_SIZE + m
                y = gr * CELL_SIZE + m
                rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
                pygame.draw.rect(surface, (60, 60, 60), rect)
                pygame.draw.rect(surface, (128, 128, 128), rect, 1)

        # Current piece
        for dr, dc in current.cells():
            r = current.row + dr
            c = current.col + dc
            if 0 <= r < BOARD_HEIGHT and 0 <= c < BOARD_WIDTH:
                _draw_cell(surface, r, c, current.color)

    # Sidebar
    _draw_sidebar(surface, board, m)

    # Update and draw particles
    board.particles = [p for p in board.particles if p.update()]
    for p in board.particles:
        p.draw(surface)

    # Draw flash overlay
    if board.flash:
        board.flash.tick()
        board.flash.draw(surface)
        if not board.flash.active:
            board.flash = None

    # Pause overlay
    if _paused and not board.game_over:
        overlay = pygame.Surface((TOTAL_WIDTH, TOTAL_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        surface.blit(overlay, (0, 0))
        _draw_text(surface, _font_title, "PAUSED",
                   (TOTAL_WIDTH // 2 - 45, TOTAL_HEIGHT // 2 - 15))

    # Game over overlay
    if board.game_over:
        overlay = pygame.Surface((TOTAL_WIDTH, TOTAL_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill(BLACK)
        surface.blit(overlay, (0, 0))
        _draw_text(surface, _font_title, "GAME OVER",
                   (TOTAL_WIDTH // 2 - 70, TOTAL_HEIGHT // 2 - 40))
        _draw_text(surface, _font, f"Score: {board.score}",
                   (TOTAL_WIDTH // 2 - 60, TOTAL_HEIGHT // 2))


def run():
    """Main game loop with intro screen."""
    global _paused, _INTRO_TIME

    _ensure_initialized()

    # Intro screen state
    _show_intro = True
    _intro_surf = _ensure_intro_surface(TOTAL_WIDTH, TOTAL_HEIGHT)

    board = Board()
    drop_timer = 0.0
    _soft_drop = False

    # Double-buffer surface for screen shake
    _shake_buf = pygame.Surface((TOTAL_WIDTH, TOTAL_HEIGHT))

    running = True
    try:
        while running:
            dt = CLOCK.tick(60) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False

                    elif _show_intro:
                        if event.key in (
                            pygame.K_RETURN, pygame.K_SPACE,
                            pygame.K_r, pygame.K_s, pygame.K_p,
                            pygame.K_UP, pygame.K_DOWN,
                            pygame.K_LEFT, pygame.K_RIGHT,
                            pygame.K_LSHIFT, pygame.K_LCTRL,
                            pygame.K_a, pygame.K_b, pygame.K_c,
                            pygame.K_x, pygame.K_z,
                        ):
                            _show_intro = False
                            _shutdown_intro()

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and _show_intro:
                    btn_rect = pygame.Rect(
                        TOTAL_WIDTH // 2 - 80,
                        int(TOTAL_HEIGHT * 0.22) + 100,
                        160, 36,
                    )
                    if btn_rect.collidepoint(event.pos):
                        _show_intro = False
                        _shutdown_intro()

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False

                    elif _show_intro:
                        if event.key in (
                            pygame.K_RETURN, pygame.K_SPACE,
                            pygame.K_r, pygame.K_s, pygame.K_p,
                            pygame.K_UP, pygame.K_DOWN,
                            pygame.K_LEFT, pygame.K_RIGHT,
                            pygame.K_LSHIFT, pygame.K_LCTRL,
                            pygame.K_a, pygame.K_b, pygame.K_c,
                            pygame.K_x, pygame.K_z,
                        ):
                            _show_intro = False
                            _shutdown_intro()

                    elif event.key == pygame.K_p:
                        _paused = not _paused

                    elif event.key == pygame.K_r and board.game_over:
                        board.reset()
                        drop_timer = 0.0

                    elif event.key == pygame.K_DOWN:
                        _soft_drop = True
                        if not _paused and not board.game_over and board.current:
                            board.move_down(soft_drop=True)

                    elif event.key in (pygame.K_LSHIFT, pygame.K_c) and not _paused and not board.game_over:
                        board.hold_piece()

                    elif not _paused and not board.game_over and board.current:
                        if event.key == pygame.K_LEFT:
                            board.move_left()
                        elif event.key == pygame.K_RIGHT:
                            board.move_right()
                        elif event.key in (pygame.K_UP, pygame.K_x):
                            board.rotate(clockwise=True)
                        elif event.key == pygame.K_z:
                            board.rotate(clockwise=False)
                        elif event.key == pygame.K_SPACE:
                            board.hard_drop()

                elif event.type == pygame.KEYUP:
                    if event.key == pygame.K_DOWN:
                        _soft_drop = False

            if _show_intro:
                _INTRO_TIME += dt
                _draw_intro_screen(_intro_surf, _INTRO_TIME)
                SCREEN.blit(_intro_surf, (0, 0))
                pygame.display.flip()
                continue

            # Auto-drop
            if not _paused and not board.game_over and board.current:
                drop_timer += dt
                speed = board.drop_speed()
                while drop_timer >= speed:
                    drop_timer -= speed
                    if not board.move_down(soft_drop=_soft_drop):
                        board._lock()
                        drop_timer = 0.0
                        break

            render(_shake_buf, board)

            # Blit with shake offset (clamp to prevent edge clipping)
            sx, sy = 0, 0
            if board.shake:
                sx, sy = board.shake.offset()
                if not board.shake.active:
                    board.shake = None
            # Clamp so the surface never shifts off the visible area
            sx = max(0, sx)
            sy = max(0, sy)
            SCREEN.blit(_shake_buf, (sx, sy))
            pygame.display.flip()

    finally:
        _shutdown()
