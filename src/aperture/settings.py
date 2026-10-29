"""User preferences persisted next to the history file.

Every field maps to something visible: theme, accent, starting volume and speed, and how
subtitles look. Unknown or invalid stored values fall back to their defaults.
"""

from __future__ import annotations

from pathlib import Path

from aperture.core import RATES
from aperture.core.storage import read_json, write_json
from aperture.theme import ACCENTS, DEFAULT_ACCENT

THEME_MODES = ("system", "dark", "light")
# Subtitle size name -> multiplier on the base overlay font size.
SUBTITLE_SIZES = {"small": 0.8, "medium": 1.0, "large": 1.25, "xlarge": 1.5}
# `default_rate` value meaning "start at whatever speed was used last".
LAST_RATE = "last"
# Opening a file with a saved position: ask first, resume silently, or start over.
RESUME_MODES = ("ask", "always", "never")

DEFAULTS: dict[str, object] = {
    "theme": "system",
    "accent": DEFAULT_ACCENT,
    "volume": 1.0,
    "rate": 1.0,
    "last_rate": 1.0,
    "subtitles_auto": True,
    "subtitle_size": "medium",
    "resume": "ask",
}


def _number(value: object) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool)


def _valid(key: str, value: object) -> bool:
    match key:
        case "theme":
            return value in THEME_MODES
        case "accent":
            return value in ACCENTS
        case "volume":
            return _number(value) and 0 <= value <= 1
        case "rate":
            return value == LAST_RATE or (_number(value) and value in RATES)
        case "last_rate":
            return _number(value) and RATES[0] <= value <= RATES[-1]
        case "subtitles_auto":
            return isinstance(value, bool)
        case "subtitle_size":
            return value in SUBTITLE_SIZES
        case "resume":
            return value in RESUME_MODES
    return False


def _field(key: str) -> property:
    return property(lambda self: self._values[key], lambda self, value: self._set(key, value))


class Settings:
    """In-memory when `path` is None."""

    def __init__(self, path: Path | None = None) -> None:
        self._path = path
        self._values = dict(DEFAULTS)
        data = read_json(path) if path is not None else None
        if isinstance(data, dict):
            for key in DEFAULTS:
                if key in data and _valid(key, data[key]):
                    self._values[key] = data[key]

    theme_mode = _field("theme")
    accent = _field("accent")
    default_volume = _field("volume")
    default_rate = _field("rate")  # a preset from RATES, or LAST_RATE
    last_rate = _field("last_rate")
    subtitles_auto = _field("subtitles_auto")
    subtitle_size = _field("subtitle_size")
    resume_mode = _field("resume")

    @property
    def start_rate(self) -> float:
        """Speed a new session starts at."""
        rate = self._values["rate"]
        return float(self._values["last_rate"] if rate == LAST_RATE else rate)

    @property
    def subtitle_scale(self) -> float:
        return SUBTITLE_SIZES[self._values["subtitle_size"]]

    def reset(self) -> None:
        self._values = dict(DEFAULTS)

    def save(self) -> None:
        if self._path is not None:
            write_json(self._path, {"version": 2, **self._values})

    def _set(self, key: str, value: object) -> None:
        if not _valid(key, value):
            raise ValueError(f"invalid {key}: {value!r}")
        self._values[key] = value
