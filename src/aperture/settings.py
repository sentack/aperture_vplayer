"""User preferences persisted next to the history file."""

from __future__ import annotations

from pathlib import Path

from aperture.core.storage import read_json, write_json
from aperture.theme import ACCENTS, DEFAULT_ACCENT

THEME_MODES = ("system", "dark", "light")


class Settings:
    """In-memory when `path` is None. Unknown or invalid stored values fall back to defaults."""

    def __init__(self, path: Path | None = None) -> None:
        self._path = path
        self._theme_mode = "system"
        self._accent = DEFAULT_ACCENT
        data = read_json(path) if path is not None else None
        if isinstance(data, dict):
            if data.get("theme") in THEME_MODES:
                self._theme_mode = data["theme"]
            if data.get("accent") in ACCENTS:
                self._accent = data["accent"]

    @property
    def theme_mode(self) -> str:
        return self._theme_mode

    @theme_mode.setter
    def theme_mode(self, value: str) -> None:
        if value not in THEME_MODES:
            raise ValueError(f"unknown theme mode: {value!r}")
        self._theme_mode = value

    @property
    def accent(self) -> str:
        return self._accent

    @accent.setter
    def accent(self, value: str) -> None:
        if value not in ACCENTS:
            raise ValueError(f"unknown accent: {value!r}")
        self._accent = value

    def save(self) -> None:
        if self._path is not None:
            write_json(self._path, {"version": 1, "theme": self._theme_mode, "accent": self._accent})
