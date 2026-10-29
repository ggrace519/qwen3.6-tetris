# AGENTS.md — Python Tetris

## Quick Start

```bash
uv venv && uv pip install pygame     # setup (project uses uv)
python tetris.py                     # run
.venv/bin/pytest tests/              # test
.venv/bin/pytest tests/ --cov=tetris_game --cov-report=term-missing  # coverage
```
## Instructions
- Code should be complete and cover edge cases where applicable.
- Tests and documentation should be written/updated as new code is added. Tests should also cover edge cases and be adversarial in nature.
- Git should be initialized and used properly. All new work should occur on its own, themed branch. It should be tested and reviewed adversarialy before asking the user for permission to merge into main.
- Keep modules <= 600 lines and organize code so that related functions are in each module.


## Structure

```
tetris.py              # thin launcher → tetris_game.app.run()
tetris_game/
  settings.py          # constants, colors, SHAPES (7 pieces × 4 rotations), LINE_SCORES, drop_speed(),
                       # LOCK_DELAY_FRAMES, DAS_FRAMES, ARR_FRAMES
  piece.py             # Piece class: type, rotation(0-3), row, col=3, cells(), rotate(), move()
  board.py             # Board: grid, collision, 7-bag randomizer, movement, rotation+wall-kick,
                       # hard_drop, ghost_row, lock, line-clear, scoring, game-over, reset(),
                       # start_lock_delay, tick_lock_delay, reset_lock_delay
  intro.py             # intro splash screen: particles, falling pieces, title, controls, start button
  app.py               # pygame init, render(), run() (event loop, auto-drop, DAS/ARR, pause, game-over overlay)
tests/
  test_settings.py     # dimensions, colors, shape validity, scoring, speed, DAS/ARR constants
  test_piece.py        # init, cells, rotate, move, absolute cells
  test_board.py        # init, bag, collision, movement, rotation/wall-kick,
                       # hard_drop, ghost_row, line-clear, lock, game-over, reset
  test_effects.py      # Particle, ScreenShake, FlashOverlay, spawn helpers, Board integration
  test_scoring.py      # hold piece, next queue, soft drop, hard drop, line clears, B2B, combos
  test_lock_delay.py   # lock delay init, start/tick/reset, integration, hard drop skip
  test_das.py          # DAS/ARR constants
  test_app.py          # pygame init/shutdown, _draw_cell, _draw_text, _draw_sidebar, render, run(),
                       # intro screen particles/pieces, event loop
```

## Architecture Notes

- `board.py` is the source of truth for game rules. `piece.py` owns piece geometry. `settings.py` owns constants. `intro.py` owns intro splash screen rendering. `app.py` is purely presentation + loop.
- All tetromino rotation states are **pre-computed normalized 90° CW rotations**. Do NOT compute them geometrically.
- The wall-kick system tries shifts `[+1, -1, +2, -2]` on failed rotation, then reverts if none work.
- `Board.reset()` calls `self.__init__()` — safe in this single-threaded game, but any external reference to `self.current` or `self.grid` becomes stale.
- `_lock()` asserts cells are in-bounds; if a piece somehow lands with cells outside `[0,9]×[0,19]`, the assertion fires. Normal gameplay prevents this via collision detection.
- Lock delay (ARE): when a piece collides moving down, `start_lock_delay()` begins a 24-frame timer. Player movement/rotation during this window resets the timer (`reset_lock_delay()`). On timer expiry, `tick_lock_delay()` returns True and `_lock()` is called. Hard drop skips lock delay entirely.
- DAS/ARR: LEFT/RIGHT key-hold tracking in app.py. After `DAS_FRAMES` (10) the key starts repeating at `ARR_FRAMES` (2) intervals.

## Testing Gotchas

- Rendering tests require `SDL_VIDEODRIVER=dummy` + `SDL_AUDIODRIVER=dummy` env vars. These are set in `tests/test_app.py` module-level.
- The `app` module uses a `fresh_pygame` fixture that calls `_shutdown()` then `_ensure_initialized()`. Tests using it must not assert `_initialized` or `_font` via imported names (use `app_mod._initialized` via the module reference instead).
- `pygame.time.Clock.tick` is read-only; patch `CLOCK` with a MagicMock, not its attributes.
- `pytest.MagicMock` does not exist; use `unittest.mock.MagicMock`.

