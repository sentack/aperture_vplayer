"""Human labels for audio and embedded subtitle tracks."""

from __future__ import annotations


def track_label(index: int, title: str | None, language: str | None) -> str:
    """`English · Commentary`, `English`, `Commentary`, or `Track 2` (index is 0-based)."""
    parts = [p.strip() for p in (language, title) if p and p.strip()]
    if len(parts) == 2 and parts[0].casefold() == parts[1].casefold():
        parts = parts[:1]
    return " · ".join(parts) or f"Track {index + 1}"
