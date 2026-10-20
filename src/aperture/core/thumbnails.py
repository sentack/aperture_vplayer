"""Seek-bar preview timing: nearby hover positions share one decoded frame."""

from __future__ import annotations

# The grid never gets finer than this, however short the file...
MIN_STEP_MS = 2_000
# ...nor coarser than this many frames across the whole file.
STEPS = 120
# Seeking onto the very last millisecond often yields no frame.
END_GUARD_MS = 500


def thumbnail_bucket(position_ms: int, duration_ms: int) -> int:
    """Snap `position_ms` to the preview grid for a file `duration_ms` long (0 if unknown)."""
    step = max(MIN_STEP_MS, duration_ms // STEPS)
    position = max(0, position_ms)
    if duration_ms > 0:
        position = min(position, duration_ms)
    bucket = round(position / step) * step
    if duration_ms > 0:
        bucket = min(bucket, max(0, duration_ms - END_GUARD_MS))
    return bucket
