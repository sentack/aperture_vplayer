"""Ordered media queue with a cursor. No Qt, no filesystem access."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path


class Playlist:
    def __init__(self) -> None:
        self._items: list[Path] = []
        self._index = -1

    def __len__(self) -> int:
        return len(self._items)

    @property
    def items(self) -> tuple[Path, ...]:
        return tuple(self._items)

    @property
    def index(self) -> int:
        """Cursor position, -1 when nothing selected."""
        return self._index

    @property
    def current(self) -> Path | None:
        return self._items[self._index] if self._index >= 0 else None

    @property
    def has_next(self) -> bool:
        return 0 <= self._index < len(self._items) - 1

    @property
    def has_previous(self) -> bool:
        return self._index > 0

    def add(self, paths: Iterable[Path | str]) -> int:
        """Append paths, cursor untouched. Returns count added."""
        before = len(self._items)
        self._items.extend(Path(p) for p in paths)
        return len(self._items) - before

    def select(self, index: int) -> Path:
        self._check(index)
        self._index = index
        return self._items[index]

    def remove(self, index: int) -> None:
        """Drop one item. Removing current moves cursor onto its successor (or new last)."""
        self._check(index)
        del self._items[index]
        if index < self._index:
            self._index -= 1
        elif index == self._index:
            self._index = min(self._index, len(self._items) - 1)

    def clear(self) -> None:
        self._items.clear()
        self._index = -1

    def _check(self, index: int) -> None:
        if not 0 <= index < len(self._items):
            raise IndexError(index)
