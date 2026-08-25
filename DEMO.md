# Demo — Scoring Modernization (innovation/scoring)

## How to try it

```bash
git checkout innovation/scoring
uv run python tetris.py
```

## What works

- **Soft drop**: Hold DOWN key to accelerate piece descent. Each cell gives 1 point (Tetris DS standard).
- **Hard drop**: Space bar drops instantly. Each cell covered gives 2 points.
- **Combos**: Consecutive line clears across pieces award bonus points (50 × combo_count × level).
- **Back-to-back**: Consecutive Tetrises (4-line clears) award 1.5× multiplier.
- All existing game mechanics work. All 184 tests pass.

## Next increment

- Show combo count and B2B status on the sidebar
- Add soft drop visual acceleration
