# Python Tetris

A small Pygame Tetris clone — fun project that demonstrates what the Qwen3.6-35B coding model can produce end-to-end, from architecture through implementation, testing, and polish.

A small Pygame Tetris clone designed to stay beginner-friendly while using a maintainable project structure.

## Features

- 10x20 board with all 7 tetrominoes
- 7-bag randomization for fairer piece distribution
- Rotation with basic wall kicks
- Ghost piece and next-piece preview
- Scoring, line clears, level progression, and faster fall speed
- Pause, restart, and game-over handling

## Requirements

- Python 3.10+
- `pygame`

## Setup

```bash
pip install pygame
```

## Run

From the project root:

```bash
python tetris.py
```

## Controls

- `Left / Right`: move piece
- `Down`: soft drop
- `Up` or `X`: rotate clockwise
- `Z`: rotate counterclockwise
- `Space`: hard drop
- `P`: pause
- `R`: restart
- `Esc`: quit

## Project Layout

```text
python-tetris/
├── README.md
├── tetris.py
└── tetris_game/
    ├── __init__.py
    ├── app.py
    ├── board.py
    ├── piece.py
    └── settings.py
```

## Architecture

- `tetris.py` is a thin launcher so the root command stays simple.
- `tetris_game/settings.py` holds constants, colors, dimensions, scoring values, and shape definitions.
- `tetris_game/piece.py` defines the `Piece` class, which knows its rotation states and occupied cells.
- `tetris_game/board.py` manages the game rules: collision detection, bag randomization, movement, line clearing, scoring, and game-over logic.
- `tetris_game/app.py` contains the Pygame window, input handling, rendering, pause logic, and the main game loop.

## Game Flow

1. The app opens the Pygame window and creates a `Board`.
2. The board spawns a current piece and a next piece from a shuffled 7-bag.
3. The main loop advances time and drops the current piece based on the current level speed.
4. Player input moves, rotates, soft-drops, or hard-drops the active piece.
5. When a piece can no longer move down, it locks into the grid.
6. Full lines are removed, score and level are updated, and a new piece spawns.
7. The game ends when a newly spawned piece collides immediately.

## Notes On Rotation

This project uses a simple wall-kick system that feels close to standard play while staying easy to read. It is not a full exact implementation of official SRS for every rotation transition.

## Possible Next Improvements

- Add hold piece support
- Implement full SRS kick tables
- Add sound effects and music
- Save high scores to disk
- Add automated tests for board logic

