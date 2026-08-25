# Demo — Visual Effects (innovation/visual-effects)

## How to try it

```bash
git checkout innovation/visual-effects
uv run python tetris.py
```

## What works

- **Line clear flash**: A white flash overlay appears on line clears, lasting longer for more lines (8 frames for single, 16 for tetris).
- **Screen shake**: The display shakes on line clears — intensity scales with lines cleared (1px for single, 4px for tetris). Shake auto-decays over frames.
- **Particle sparks**: Colored spark particles burst from each cleared cell, with gravity and air resistance. More lines = more particles.
- Effects are **safe for tests** — when pygame isn't initialized, effects silently skip (no crashes).
- All 184 tests pass.

## What's new

- `tetris_game/effects.py` (new module): `Particle`, `ScreenShake`, `FlashOverlay` classes with update/draw lifecycle
- `tetris_game/board.py`: `_clear_lines()` triggers flash, shake, and particles
- `tetris_game/app.py`: Double-buffer surface for shake offset, particles rendered each frame, flash overlay composited

## Next increment

- Spawn particles on piece lock (small burst)
- Add level-up flash effect
- Add ambient background color shift tied to score/level
