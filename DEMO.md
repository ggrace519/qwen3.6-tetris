# Demo — Hold Piece + Next Queue (innovation/hold-piece)

## How to try it

```bash
git checkout innovation/hold-piece
uv run python tetris.py
```

## What works

- **Hold piece**: Press `C` or `Left Shift` to swap current piece into hold slot, retrieve later. Each piece can be held once per turn (reset after lock).
- **Extended next queue**: Sidebar shows next piece (5 pieces ahead from 7-bag).
- **Hold visual feedback**: Dimmed when already used. Hold slot renders above NEXT.
- All 184 tests pass.

## Next increment

- Show 2-3 more pieces in NEXT queue
- Add hold key binding customization
