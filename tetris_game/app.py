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
    DAS_FRAMES,
    ARR_FRAMES,
)
from .effects import Particle
from . import intro


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
    _intro_surf = intro._ensure_intro_surface(TOTAL_WIDTH, TOTAL_HEIGHT)

    board = Board()
    drop_timer = 0.0
    _soft_drop = False

    # DAS/ARR key-repeat state: maps key → frames held
    _das_timers: dict[int, int] = {}
    # ARR repeat timer: frames since last auto-repeat
    _arr_timer = 0

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
                            intro.shutdown_intro()

                    elif event.key == pygame.K_p:
                        _paused = not _paused

                    elif event.key == pygame.K_r and board.game_over:
                        board.reset()
                        drop_timer = 0.0

                    elif event.key == pygame.K_DOWN:
                        _soft_drop = True
                        if not _paused and not board.game_over and board.current:
                            if board.move_down(soft_drop=True):
                                if board._lock_delay_active:
                                    board.reset_lock_delay()

                    elif event.key in (pygame.K_LSHIFT, pygame.K_c) and not _paused and not board.game_over:
                        board.hold_piece()

                    elif not _paused and not board.game_over and board.current:
                        if event.key == pygame.K_LEFT:
                            _das_timers[pygame.K_LEFT] = 0
                            if board.move_left():
                                if board._lock_delay_active:
                                    board.reset_lock_delay()
                        elif event.key == pygame.K_RIGHT:
                            _das_timers[pygame.K_RIGHT] = 0
                            if board.move_right():
                                if board._lock_delay_active:
                                    board.reset_lock_delay()
                        elif event.key in (pygame.K_UP, pygame.K_x):
                            if board.rotate(clockwise=True):
                                if board._lock_delay_active:
                                    board.reset_lock_delay()
                        elif event.key == pygame.K_z:
                            if board.rotate(clockwise=False):
                                if board._lock_delay_active:
                                    board.reset_lock_delay()
                        elif event.key == pygame.K_SPACE:
                            board.hard_drop()

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and _show_intro:
                    btn_rect = pygame.Rect(
                        TOTAL_WIDTH // 2 - 80,
                        int(TOTAL_HEIGHT * 0.22) + 100,
                        160, 36,
                    )
                    if btn_rect.collidepoint(event.pos):
                        _show_intro = False
                        intro.shutdown_intro()

                elif event.type == pygame.KEYUP:
                    if event.key == pygame.K_DOWN:
                        _soft_drop = False
                    if event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                        _das_timers.pop(event.key, None)
                        _arr_timer = 0

            # DAS/ARR key-repeat processing
            if not _show_intro and not _paused and not board.game_over and board.current:
                for key in list(_das_timers.keys()):
                    _das_timers[key] += 1
                    if _das_timers[key] >= DAS_FRAMES:
                        _arr_timer += 1
                        if _arr_timer >= ARR_FRAMES:
                            _arr_timer = 0
                            if key == pygame.K_LEFT:
                                if board.move_left():
                                    if board._lock_delay_active:
                                        board.reset_lock_delay()
                            elif key == pygame.K_RIGHT:
                                if board.move_right():
                                    if board._lock_delay_active:
                                        board.reset_lock_delay()

            if _show_intro:
                intro._INTRO_TIME += dt
                intro._draw_intro_screen(_intro_surf, intro._INTRO_TIME,
                                         _draw_text, _font_title, _font, _font_small)
                SCREEN.blit(_intro_surf, (0, 0))
                pygame.display.flip()
                continue

            # Auto-drop with lock delay
            if not _paused and not board.game_over and board.current:
                drop_timer += dt
                speed = board.drop_speed()
                while drop_timer >= speed:
                    drop_timer -= speed
                    if not board.move_down(soft_drop=_soft_drop):
                        if board._lock_delay_active:
                            if board.tick_lock_delay():
                                board._lock()
                                drop_timer = 0.0
                                break
                        else:
                            board.start_lock_delay()
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
