"""Intro splash screen: particles, falling pieces, title, controls, start button."""

import math
import random
import pygame

from .settings import (
    BG_COLOR,
    WHITE,
    GRAY,
    CELL_SIZE,
    TOTAL_WIDTH,
    TOTAL_HEIGHT,
    TETROMINO_COLORS,
    TETROMINO_TYPES,
    SHAPES,
)


# Module-level intro state
_INTRO_PARTICLES = None
_INTRO_PIECES = None
_INTRO_TIME = 0.0


def _ensure_intro_surface(width: int, height: int):
    """Create a back-buffer for intro rendering."""
    buf = pygame.Surface((width, height))
    buf.fill(BG_COLOR)
    return buf


def _spawn_intro_particles(count: int = 120):
    """Create colorful floating particles for the intro background."""
    global _INTRO_PARTICLES
    particles = []
    for _ in range(count):
        particles.append({
            "x": random.uniform(0, TOTAL_WIDTH),
            "y": random.uniform(0, TOTAL_HEIGHT),
            "vx": random.uniform(-0.3, 0.3),
            "vy": random.uniform(-0.5, -0.1),
            "size": random.uniform(1.5, 4.0),
            "color": random.choice(list(TETROMINO_COLORS.values())),
            "alpha": random.uniform(0.15, 0.5),
            "wobble_phase": random.uniform(0, 2 * math.pi),
            "wobble_speed": random.uniform(0.02, 0.06),
            "wobble_amp": random.uniform(0.3, 1.0),
        })
    _INTRO_PARTICLES = particles
    return particles


def _spawn_intro_falling_pieces(count: int = 15):
    """Create falling tetromino silhouettes for the intro background."""
    global _INTRO_PIECES
    pieces = []
    for _ in range(count):
        ptype = random.choice(TETROMINO_TYPES)
        cells = SHAPES[ptype][0]
        min_r = min(r for r, _ in cells)
        max_r = max(r for r, _ in cells)
        min_c = min(c for _, c in cells)
        max_c = max(c for _, c in cells)
        pieces.append({
            "type": ptype,
            "cells": cells,
            "min_r": min_r, "max_r": max_r,
            "min_c": min_c, "max_c": max_c,
            "x": random.uniform(0, TOTAL_WIDTH - 80),
            "y": random.uniform(-200, -20),
            "speed": random.uniform(0.3, 1.0),
            "rotation": random.randint(0, 3),
            "color": TETROMINO_COLORS[ptype],
            "alpha": random.uniform(0.06, 0.15),
            "size_mult": random.uniform(0.7, 1.3),
        })
    _INTRO_PIECES = pieces
    return pieces


def _draw_intro_piece(p, elapsed, surface):
    """Draw a single falling intro piece with rotation and bobbing."""
    cell_sz = CELL_SIZE * p["size_mult"]
    bob_y = math.sin(elapsed * 1.5 + p["x"] * 0.01) * 8.0
    rot_cells = SHAPES[p["type"]][int(p["rotation"]) % 4]
    for dr, dc in rot_cells:
        px = int(p["x"] + (dc - p["min_c"]) * cell_sz)
        py = int(p["y"] + (dr - p["min_r"]) * cell_sz + bob_y)
        rect = pygame.Rect(px, py, int(cell_sz), int(cell_sz))
        alpha_surf = pygame.Surface((int(cell_sz), int(cell_sz)), pygame.SRCALPHA)
        alpha_surf.fill((*p["color"], int(255 * p["alpha"])))
        surface.blit(alpha_surf, rect.topleft)


def _draw_intro_screen(surface: pygame.Surface, elapsed: float,
                       draw_text, font_title, font, font_small):
    """Draw the full intro splash screen. Mutates surface in place."""
    surface.fill(BG_COLOR)

    # ── Background particles ──
    if _INTRO_PARTICLES is None:
        _spawn_intro_particles()
    for p in _INTRO_PARTICLES:
        p["x"] += p["vx"] + math.sin(elapsed * p["wobble_speed"] + p["wobble_phase"]) * p["wobble_amp"]
        p["y"] += p["vy"]
        if p["y"] < -10:
            p["y"] = TOTAL_HEIGHT + 10
        if p["x"] < -10:
            p["x"] = TOTAL_WIDTH + 10
        elif p["x"] > TOTAL_WIDTH + 10:
            p["x"] = -10
        s = max(1, round(p["size"] * p["alpha"]))
        alpha_val = int(255 * p["alpha"])
        color = (*p["color"], alpha_val)
        pygame.draw.rect(surface, color, (int(p["x"]), int(p["y"]), s, s))

    # ── Falling tetromino silhouettes ──
    if _INTRO_PIECES is None:
        _spawn_intro_falling_pieces()
    for p in _INTRO_PIECES:
        p["y"] += p["speed"]
        p["rotation"] = (p["rotation"] + 0.02) % 4
        if p["y"] > TOTAL_HEIGHT + 50:
            p["y"] = -50
            p["x"] = random.uniform(0, TOTAL_WIDTH - 80)
        _draw_intro_piece(p, elapsed, surface)

    # ── Title "TETRIS" with glow ──
    title_y = int(TOTAL_HEIGHT * 0.22)
    title_x = TOTAL_WIDTH // 2 - 50

    for glow in range(5, 0, -1):
        glow_surf = pygame.Surface((160, 50), pygame.SRCALPHA)
        draw_text(glow_surf, font_title, "TETRIS", (0, 0))
        glow_surf.set_alpha(int(40 / glow))
        surface.blit(glow_surf, (title_x, title_y))

    hue_t = math.sin(elapsed * 1.2) * 0.5 + 0.5
    r = int(200 + 55 * hue_t)
    g = int(80 + 80 * (1.0 - hue_t))
    b = int(240 - 100 * hue_t)
    draw_text(surface, font_title, "TETRIS", (title_x, title_y), color=(r, g, b))

    # ── Start button ──
    btn_w = 160
    btn_h = 36
    btn_x = TOTAL_WIDTH // 2 - btn_w // 2
    btn_y = title_y + 100
    pulse = math.sin(elapsed * 3.0) * 0.5 + 0.5
    btn_color = tuple(int(c * 0.7 + 60 * pulse) for c in TETROMINO_COLORS["I"])
    btn_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
    pygame.draw.rect(surface, btn_color, btn_rect, border_radius=6)
    pygame.draw.rect(surface, WHITE, btn_rect, 2, border_radius=6)
    btn_surf = pygame.Surface((160, 30), pygame.SRCALPHA)
    draw_text(btn_surf, font, "START", (0, 0), color=BG_COLOR)
    surface.blit(btn_surf, (btn_x + 20, btn_y + 3))

    # ── Decorative line ──
    line_y = title_y + 150
    line_w = int(160 + 40 * math.sin(elapsed * 2.0))
    line_color_alpha = int(180 + 75 * math.sin(elapsed * 1.5))
    pygame.draw.line(surface, (255, 255, 255, line_color_alpha),
                       (TOTAL_WIDTH // 2 - line_w // 2, line_y),
                       (TOTAL_WIDTH // 2 + line_w // 2, line_y), 2)

    # ── Controls section ──
    controls_y = int(TOTAL_HEIGHT * 0.46)
    draw_text(surface, font_small, "CONTROLS", (TOTAL_WIDTH // 2 - 30, controls_y),
                color=GRAY)
    controls_y += 25

    controls = [
        ("← →", "Move"),
        ("↑ / X", "Rotate CW"),
        ("Z", "Rotate CCW"),
        ("Space", "Hard Drop"),
        ("C / Shift", "Hold"),
        ("↓", "Soft Drop"),
        ("P", "Pause"),
        ("Esc", "Quit"),
    ]
    for key, desc in controls:
        key_surf = pygame.Surface((80, 20), pygame.SRCALPHA)
        draw_text(key_surf, font_small, key, (0, 0), color=WHITE)
        val_surf = pygame.Surface((100, 20), pygame.SRCALPHA)
        draw_text(val_surf, font_small, desc, (0, 0), color=GRAY)
        surface.blit(key_surf, (TOTAL_WIDTH // 2 - 100, controls_y))
        surface.blit(val_surf, (TOTAL_WIDTH // 2 + 20, controls_y))
        controls_y += 20

    # ── Animated tetromino showcase ──
    showcase_y = int(TOTAL_HEIGHT * 0.78)
    for i, (ptype, color) in enumerate(zip(TETROMINO_TYPES, TETROMINO_COLORS.values())):
        rot = int(elapsed * 0.8 + i * 0.7) % 4
        cells = SHAPES[ptype][rot]
        min_r = min(r for r, _ in cells)
        max_r = max(r for r, _ in cells)
        min_c = min(c for _, c in cells)
        max_c = max(c for _, c in cells)
        piece_w = (max_c - min_c + 1) * 12
        spacing = TOTAL_WIDTH // (len(TETROMINO_TYPES) + 1)
        px = spacing * (i + 1) - piece_w // 2
        py = showcase_y + int(math.sin(elapsed * 2.0 + i) * 5)
        for dr, dc in cells:
            cx = px + (dc - min_c) * 12
            cy = py + (dr - min_r) * 12
            rect = pygame.Rect(cx, cy, 12, 12)
            pygame.draw.rect(surface, color, rect)
            pygame.draw.rect(surface,
                              tuple(min(255, c + 40) for c in color),
                              rect, 1)

    # ── Corner accents ──
    accent_t = int(elapsed * 200) % 256
    corner_size = 8
    for cx, cy in [(0, 0), (TOTAL_WIDTH - corner_size, 0),
                    (0, TOTAL_HEIGHT - corner_size),
                    (TOTAL_WIDTH - corner_size, TOTAL_HEIGHT - corner_size)]:
        accent_surf = pygame.Surface((corner_size, corner_size), pygame.SRCALPHA)
        accent_color = (*TETROMINO_COLORS[TETROMINO_TYPES[accent_t % 7]], 120)
        pygame.draw.rect(accent_surf, accent_color, accent_surf.get_rect())
        surface.blit(accent_surf, (cx, cy))


def shutdown_intro():
    """Reset intro state when transitioning to gameplay."""
    global _INTRO_PARTICLES, _INTRO_PIECES, _INTRO_TIME
    _INTRO_PARTICLES = None
    _INTRO_PIECES = None
    _INTRO_TIME = 0.0
