# Demo — All Innovations Merged

## How to try it

```bash
uv run python tetris.py
```

## What works (all 3 innovations merged)

- **Hold piece**: Press `C` or `Left Shift` to swap current piece into hold slot, retrieve later. Each piece can be held once per turn (reset after lock). Dimmed when already used.
- **Extended next queue**: Sidebar shows next piece (5 pieces ahead from 7-bag).
- **Soft drop**: Hold DOWN key to accelerate. Each cell gives 1 point (Tetris DS).
- **Hard drop**: Space bar drops instantly. Each cell gives 2 points.
- **Combos**: Consecutive line clears across pieces award bonus (50 × count × level).
- **Back-to-back**: Consecutive Tetrises award 1.5× multiplier.
- **Line clear flash**: White flash overlay on line clears, longer for more lines.
- **Screen shake**: Display shakes on line clears — intensity scales with lines cleared.
- **Particle sparks**: Colored sparks burst from cleared cells with gravity.
- All 184 tests pass.
