"""Visual effects: particles, screen shake, flash overlay."""

import math
import random
import pygame

from .settings import (
    CELL_SIZE,
    BOARD_WIDTH,
    BOARD_HEIGHT,
)


def _pygame_ready() -> bool:
    """Return True if pygame is initialized (for test safety)."""
    try:
        return pygame.get_init()[0]
    except Exception:
        return False


# ------------------------------------------------------------------
# Particles
# ------------------------------------------------------------------

class Particle:
    """A single spark / confetti particle."""

    __slots__ = ("x", "y", "vx", "vy", "life", "max_life", "color", "size")

    def __init__(self, x: float, y: float, color: tuple,
                 vx: float = 0.0, vy: float = 0.0,
                 life: int = 15, size: int = 2):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.life = life
        self.max_life = life
        self.color = color
        self.size = size

    def update(self) -> bool:
        """Advance one frame.  Return True while alive."""
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.3            # gravity
        self.vx *= 0.98           # air resistance
        self.life -= 1
        return self.life > 0

    def draw(self, surface: pygame.Surface):
        alpha = max(0, self.life / self.max_life)
        s = max(1, round(self.size * alpha))
        color = (*self.color, int(255 * alpha))
        rect = pygame.Rect(int(self.x), int(self.y), s, s)
        pygame.draw.rect(surface, color, rect)


def spawn_sparks(row: int, col: int, color: tuple, count: int = 6) -> list[Particle]:
    """Spawn sparks at the centre of a board cell."""
    cx = col * CELL_SIZE + CELL_SIZE // 2
    cy = row * CELL_SIZE + CELL_SIZE // 2
    particles: list[Particle] = []
    for _ in range(count):
        angle = random.uniform(0, 2 * 3.14159)
        speed = random.uniform(1, 4)
        vx = math.cos(angle) * speed
        vy = math.sin(angle) * speed - 2
        particles.append(Particle(cx, cy, color, vx, vy, life=random.randint(10, 20)))
    return particles


def spawn_line_clear_sparks(cleared_rows: list[int],
                            grid: list[list],
                            count: int = 4) -> list[Particle]:
    """Spark particles along cleared rows."""
    particles: list[Particle] = []
    for r in cleared_rows:
        for c in range(BOARD_WIDTH):
            if grid[r][c] is not None:
                particles.extend(spawn_sparks(r, c, grid[r][c], count=count))
    return particles


# ------------------------------------------------------------------
# Screen shake
# ------------------------------------------------------------------

class ScreenShake:
    """Frame-offset screen shake with automatic decay."""

    __slots__ = ("intensity", "decay", "active")

    def __init__(self, intensity: int = 3, decay: float = 0.85):
        self.intensity = intensity
        self.decay = decay
        self.active = True

    def offset(self) -> tuple[int, int]:
        if not self.active:
            return (0, 0)
        dx = random.randint(-self.intensity, self.intensity)
        dy = random.randint(-self.intensity, self.intensity)
        self.intensity = max(0, round(self.intensity * self.decay))
        if self.intensity == 0:
            self.active = False
        return (dx, dy)


# ------------------------------------------------------------------
# Flash overlay
# ------------------------------------------------------------------

class FlashOverlay:
    """A white overlay that fades out over *frames* steps."""

    __slots__ = ("surface", "frames", "max_frames", "active")

    def __init__(self, width: int, height: int, frames: int = 10):
        self.frames = frames
        self.max_frames = frames
        self.active = self.frames > 0
        if _pygame_ready():
            self.surface = pygame.Surface((width, height))
            self.surface.fill((255, 255, 255))
        else:
            self.surface = None

    def tick(self) -> bool:
        if not self.active:
            return False
        self.frames -= 1
        if self.frames <= 0:
            self.active = False
        return True

    def draw(self, surface: pygame.Surface):
        if not self.active or self.surface is None:
            return
        alpha = max(0, int(180 * self.frames / self.max_frames))
        overlay = pygame.Surface((surface.get_width(), surface.get_height()))
        overlay.set_alpha(alpha)
        overlay.fill((255, 255, 255))
        surface.blit(overlay, (0, 0))
