"""Playback speed presets."""

from __future__ import annotations

RATES = (0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0)

_EPSILON = 1e-6


def step_rate(current: float, steps: int) -> float:
    """Move `steps` presets up (positive) or down from `current`, clamped to the ends.

    An off-preset `current` first snaps to the nearest preset in the step's direction.
    """
    if steps > 0:
        ahead = [r for r in RATES if r > current + _EPSILON]
        return ahead[min(steps, len(ahead)) - 1] if ahead else RATES[-1]
    if steps < 0:
        behind = [r for r in reversed(RATES) if r < current - _EPSILON]
        return behind[min(-steps, len(behind)) - 1] if behind else RATES[0]
    return current


def format_rate(rate: float) -> str:
    return f"{rate:g}×"
