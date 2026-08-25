# Innovation Proposals — Python Tetris
*Generated 2026-08-25*

## How this codebase stands today

A clean, well-tested (184 tests) beginner Tetris clone with correct core mechanics: 7-bag randomizer, basic wall kicks, ghost piece, next piece preview, line clearing, and level progression. The architecture is tight — four modules with clear responsibilities. But it looks and feels like a tutorial project: flat solid-color cells with a bevel border, no animations, no feedback on interactions, no sound, no hold piece, and a single-piece preview. The render loop is a simple fill-and-draw with no frame blending, no sprite system, and no visual feedback on events.

## What the best in this space are doing

**Gameplay mechanics:** Official Tetris Guideline games (Puyo Puyo Tetris, Tetris Effect, Tetris 99) share a standardized spec: SRS rotation with full kick tables, hold piece, 5–7 piece next queue, lock delay (ARE=6 frames), DAS/ARR for key hold movement, Tetris DS scoring (soft/hard drop points, combos, back-to-back), T-spin detection, and combo tracking.

**Visual presentation:** Modern Tetris (Tetris Effect, TETR.IO, TETRIS 99) uses dynamic backgrounds that shift color and intensity based on game state — brighter during combos, darker during quiet moments. Pieces have gradient fills and specular highlights. Line clears flash white then fade. Lock impacts produce subtle screen shake. Ghost pieces render with transparency and outline. The sidebar shows a 5-piece queue with the next 4 smaller. Hold piece slot has a desaturated preview. Drop animations show the piece falling in a flash.

**Play engine depth:** Guideline games use 1-frame ARE (entry delay) for DAS/IRS/IHS input buffering. Non-guideline games (TETR.IO, Jstris, Cultris 2) skip ARE entirely for faster gameplay. Soft drop reaches 20–60 cells/sec. Hard drop is required. Some games use "sonic drop" (hard drop that still respects lock delay). At high levels, gravity can reach 20G (instant drop).

Sources: [Tetris Guideline](https://tetris.wiki/Tetris_Guideline), [SRS](https://harddrop.com/wiki/SRS), [DAS](https://tetris.wiki/DAS), [Scoring](https://tetris.wiki/Scoring), [Drop](https://tetris.wiki/Drop), [ARE](https://tetris.wiki/ARE), [Rotate/IRS](https://tetris.wiki/Rotate), [howtotetris.com](https://howtotetris.com/tetris-mechanisms/)

## Proposals (ranked)

### 1. Add hold piece + extended next queue
**Category:** feature
**Impact 5 · Novelty 3 · Effort 2 · Fit 5**

**The idea.** Add a hold piece slot (press a key to swap current piece into hold, retrieve held piece in its place) and expand next queue from 1 piece to 5. This is the single most recognizable missing feature — every modern Tetris has both, and they're deeply intertwined for strategy.

**Inspired by.** All Tetris Guideline games since Tetris Worlds (2001). Hold piece is mandatory in the guideline spec.

**Implementation sketch.**
- `settings.py`: Add `HOLD_KEY`, `NEXT_QUEUE_SIZE = 5`
- `board.py`: Add `self.hold_type: str | None = None`, `self.hold_used: bool = False`, `self.next_queue: list[str] = []`
- `_fill_bag`: Fill with 5 pieces instead of just 1 next piece. Pre-fill the queue.
- `_spawn_next`: Pull from `next_queue` instead of calling `_next_type` once. Append a new piece to queue when it runs low.
- `board.py`: New method `hold_piece()` — swaps current piece into hold, spawns from queue. Set `hold_used = True`. After lock, reset `hold_used = False` so next press works.
- `app.py`: Add key binding (default `C` or `LSHIFT`) for hold. In sidebar, add hold slot rendering above next piece.
- `piece.py`: No changes needed.

**Effort.** 3–4 hours. Mostly board.py and app.py. Straightforward state machine.

**First step.** Add `hold_type`, `hold_used`, and `next_queue` to Board, wire up `hold_piece()` method.

### 2. Lock delay (ARE) with DAS/ARR key repeat
**Category:** feature
**Impact 4 · Novelty 2 · Effort 3 · Fit 5**

**The idea.** Add a 0.4s (24 frames at 60fps) delay before a piece locks after landing, during which the player can still move/rotate (the "wiggle" mechanic). Implement DAS (Delayed Auto-Shift: 167ms hold before repeating) and ARR (Auto Repeat Rate: 33ms between repeats) for smooth sideways movement.

**Inspired by.** Tetris Guideline standard: DAS=10 frames, ARR=2 frames, ARE=6 frames.

**Implementation sketch.**
- `settings.py`: Add `LOCK_DELAY_FRAMES = 24`, `DAS_FRAMES = 10`, `ARR_FRAMES = 2`
- `app.py` event loop: Track key-down timestamps. For LEFT/RIGHT held > DAS frames, start repeating at ARR intervals. In the game loop, after a piece lands, start a `lock_timer` — if it hasn't elapsed, movement/rotation still works but the piece won't auto-drop into lock. On timer expiry, call `_lock()`.
- `app.py`: Store `self._lock_timer = 0` on Board, increment per frame in loop. When move/hit collision on the side, reset the timer.

**Effort.** 4–6 hours. The tricky part is the lock delay state machine in the main loop.

**First step.** Add lock delay timer to Board, test that pieces can wiggle after landing.

### 3. Modernize scoring to Tetris DS standard
**Category:** feature
**Impact 4 · Novelty 2 · Effort 1 · Fit 5**

**The idea.** Switch to the Tetris DS scoring table: single=100×level, double=300×level, triple=500×level, tetris=800×level. Add soft drop (1pt/cell), hard drop (2pt/cell), combo bonus (50×combo_count×level), and back-to-back multiplier (1.5× for consecutive special clears).

**Inspired by.** Tetris DS scoring table, used in all Guideline-compatible games since 2006.

**Implementation sketch.**
- `settings.py`: Update `LINE_SCORES` to `{1: 100, 2: 300, 3: 500, 4: 800}` (remove level multiply — it's in the values now)
- `board.py`: In `hard_drop()`, already scores `drop_dist * 2` — keep as-is (matches hard drop = 2pt/cell). In `move_down()`, add `self.score += 1` per cell. Track `self.last_clear_type` ("tetris"/"t-spin"/"other") for back-to-back. Track `self.combo_count` and `self.combo_timer` (combo must occur before next piece locks).
- `app.py`: Add soft drop key binding (already has DOWN). In the auto-drop loop, distinguish soft drop from gravity: soft drop = move_down() called by keypress (1pt/cell), gravity = auto-drop (0pt).
- Add a `score_breakdown` display or tooltip showing combo/BtB.

**Effort.** 2–3 hours. Mostly board.py scoring changes.

**First step.** Update LINE_SCORES and add soft drop points in `move_down()`.

### 4. SRS rotation with full kick tables
**Category:** architecture
**Impact 4 · Novelty 3 · Effort 4 · Fit 4**

**The idea.** Replace the simple `[+1, -1, +2, -2]` wall kick with the full SRS kick table. SRS has 5 rotation points (0=spawn, 1=R, 2=180, 3=LR) each with different kick offsets per piece type and rotation direction.

**Inspired by.** SRS spec from HardDrop Tetris Wiki and Tetris Guideline.

**Implementation sketch.**
- `settings.py`: Add `SRS_KICK_TABLES` dict keyed by `(piece_type, rotation_point, direction)`. Each entry is a list of `(dc, dr)` offsets to try. E.g., J/L at point 0→R: `[(-1,0), (0,0), (1,0), (1,-1), (-2,0)]`
- `piece.py`: Add `rotation_point` property (tracks which of 5 SRS positions the piece is in). `rotated_cells()` now looks up the next rotation point from a 4-state rotation cycle.
- `board.py`: `rotate()` now looks up the kick table for the piece's current point + direction, tries each offset in order. Revert on failure as before.

**Effort.** 6–8 hours. The kick tables are well-documented but large (~50 entries). Testing is critical.

**First step.** Define the SRS kick tables in settings.py, verify I-piece and O-piece kicks work.

### 5. Dynamic visual effects (particles, screen shake, line clear flash)
**Category:** wow
**Impact 4 · Novelty 4 · Effort 3 · Fit 4**

**The idea.** Add visual feedback that responds to game events: screen shake on Tetris clears, a flash overlay on line clears, particle burst on piece lock (sparks flying off the locked cells), and a subtle pulse on the sidebar when scoring. These are the "game feel" elements that separate a utility demo from a game people want to play.

**Inspired by.** Tetris Effect's ambient visual system (background shifts with game state), TETR.IO's particle system, and modern game design principles (Juice It Or Lose It — every interaction needs visual feedback). In pygame, this is achievable with overlay surfaces, sprite lists, and frame counting — no shader pipeline needed.

**Implementation sketch.**
- `tetris_game/effects.py` (new module): Central effects manager.
  - `Particle` class: position, velocity, life, color, size. Updated per frame with velocity decay. Rendered as small rects on a transparent overlay surface.
  - `ScreenShake` class: frame offset (dx, dy), intensity, decay. Applied by blitting the main surface with offset, then flipping.
  - `FlashOverlay` class: alpha-blended white surface that fades out over 8–12 frames. Triggered on line clears.
- `app.py render()`: After drawing the board, apply effects overlay. If screen shake is active, offset the entire blit. If flash is active, blit the flash surface over everything.
- Trigger points: `_clear_lines()` → flash + particles (colored sparks from cleared rows) + screen shake (intensity proportional to lines cleared). `_lock()` → small particle burst (3–4 sparks). `level_up` → flash + particles.
- `settings.py`: `PARTICLES_ENABLED = True`, `SHAKE_INTENSITY = 2`, `FLASH_DURATION = 8` frames.

**Effort.** 3–4 hours. New module, but patterns are simple — particle systems are a well-known game dev pattern.

**First step.** Create `effects.py` with a `Particle` class and a simple `spawn_sparks(row, color, count=8)` function. Test it rendering on a single cell.

### 6. Audio feedback
**Category:** wow
**Impact 3 · Novelty 3 · Effort 2 · Fit 4**

**The idea.** Add synthesized sound effects using pygame.mixer: drop thud, line clear fanfare, level up jingle, game over tone. Use simple oscillator-generated sounds (no external assets needed) via `pygame.sndarray` or raw audio buffers.

**Inspired by.** All commercial Tetris games use audio feedback for game states.

**Implementation sketch.**
- `settings.py`: Add `SOUND_ENABLED = True`, volume constants. Generate sound waveforms as numpy arrays or raw `array.array('h')`.
- `app.py`: In `_ensure_initialized()`, init `pygame.mixer`. Create sound objects for: lock (short low-frequency thud ~100ms), line clear (ascending arpeggio), tetris (bright fanfare), game over (descending tone).
- Call sounds from board events: `_lock()` → drop sound, `_clear_lines()` → line clear sound.

**Effort.** 2–3 hours. Pygame audio API is straightforward.

**First step.** Generate a simple drop-thud sound using `pygame.sndarray.make_sound()` with a decaying sine wave.

### 7. High score persistence
**Category:** DX
**Impact 3 · Novelty 1 · Effort 1 · Fit 4**

**The idea.** Save and load top 10 scores to a JSON file. Display on the sidebar or a dedicated "scores" screen. Simple but meaningful — gives players a reason to replay.

**Implementation sketch.**
- New file `tetris_game/scores.py`: `load_scores()`, `save_scores()`, `add_score(score, level, lines)` functions using JSON.
- `app.py`: On game over, prompt for name entry (simple text input), save score.
- `settings.py`: `SCORES_FILE = "scores.json"`

**Effort.** 1–2 hours.

**First step.** Create `scores.py` with load/save functions.

## Killed ideas (and why)

- **T-spin detection**: Complex to implement correctly (3-corner rule + pointing-side rule). Overkill for a beginner-friendly clone. Would require tracking the piece's pre-rotation position — feasible but low ROI.
- **Sonic drop**: TGM-style drop that lands but still respects lock delay. Cool concept but adds complexity to the drop state machine with marginal gameplay benefit for this audience.
- **IRS (Initial Rotation System)**: Allows rotation input during ARE before piece spawns. Powerful competitive mechanic but only useful with ARE + lock delay enabled, which is rare in Western Tetris. Adds state tracking to the spawn sequence.
- **AI bot**: Fascinating project but out of scope for upgrading the game itself. Would be a separate project.
- **Multiplayer/versus mode**: Requires networking, garbage system, sync. Massive scope.
- **Gradient piece rendering**: Would make cells look much more polished than flat colors. But it requires per-pixel surface manipulation or pre-rendered sprite sheets, which is a render pipeline change. Deferred — the particle system and effects (#5) give more impact per effort.
- **Colorblind modes**: Good accessibility feature, but the current palette (cyan/orange/purple/green/red/blue/yellow) is already colorblind-friendly for most types. Defer to later when we have a proper settings system.
- **Drop speed ramp (20G)**: Modern competitive Tetris accelerates to instant drop at high gravity. Overkill for a beginner game. The level speed curve is fine as-is.

## Suggested order of attack

**Phase 1 — Mechanics that change the game feel immediately:**
1. **#3 (scoring)** — 2–3 hours, almost zero risk. Updates existing methods, gives immediate feedback that the game is "leveling up."
2. **#1 (hold + next queue)** — 3–4 hours. The biggest single gameplay improvement. Changes sidebar layout but is architecturally clean.
3. **#2 (lock delay + DAS/ARR)** — 4–6 hours. Transforms movement from clunky to smooth. The wiggle mechanic makes everything feel better.

**Phase 2 — Presentation polish:**
4. **#5 (visual effects)** — 3–4 hours. New module, but the patterns are straightforward. Makes the game look and feel like a real product rather than a demo.
5. **#6 (audio)** — 2–3 hours. Synthesized sounds, no external assets. Pairs naturally with the visual effects.
6. **#7 (high scores)** — 1–2 hours. Quick win, good morale boost.

**Phase 3 — Deep architecture:**
7. **#4 (SRS rotation)** — 6–8 hours. Most invasive change. Do it last because it requires the most careful testing and could break existing game feel if the kick tables aren't dialed in right.
