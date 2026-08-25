"""Pygame window, input handling, rendering, pause logic, and main game loop."""

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
    SHAPES,
    TETROMINO_COLORS,
)


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


def _draw_sidebar(surface, board):
    """Draw the sidebar: title, hold piece, next piece, score, level, lines."""
    sidebar_x = BOARD_WIDTH * CELL_SIZE

    # Separator line
    pygame.draw.line(surface, GRAY, (sidebar_x, 0), (sidebar_x, TOTAL_HEIGHT), 2)

    y_offset = 20

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


def render(surface, board):
    """Clear screen and draw the entire game state."""
    surface.fill(BG_COLOR)

    # Grid background
    for r in range(BOARD_HEIGHT):
        for c in range(BOARD_WIDTH):
            x = c * CELL_SIZE
            y = r * CELL_SIZE
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
                x = gc * CELL_SIZE
                y = gr * CELL_SIZE
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
    _draw_sidebar(surface, board)

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
    """Main game loop."""
    global _paused

    _ensure_initialized()

    board = Board()
    drop_timer = 0.0
    _soft_drop = False

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

            render(SCREEN, board)
            pygame.display.flip()

    finally:
        _shutdown()
