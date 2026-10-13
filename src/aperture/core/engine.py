"""Playback engine contract. Backends implement this protocol."""

from __future__ import annotations

from enum import Enum, auto
from pathlib import Path
from typing import Protocol


class PlaybackState(Enum):
    STOPPED = auto()
    PLAYING = auto()
    PAUSED = auto()


class PlaybackEngine(Protocol):
    @property
    def state(self) -> PlaybackState: ...

    @property
    def position(self) -> float:
        """Current position, seconds."""
        ...

    @property
    def duration(self) -> float:
        """Media length, seconds. 0 when unknown."""
        ...

    @property
    def volume(self) -> float:
        """Linear volume, 0.0-1.0."""
        ...

    def load(self, source: Path | str) -> None: ...
    def play(self) -> None: ...
    def pause(self) -> None: ...
    def stop(self) -> None: ...
    def seek(self, seconds: float) -> None: ...
    def set_volume(self, value: float) -> None: ...
