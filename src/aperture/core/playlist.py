"""Ordered media queue with a cursor, repeat and shuffle. No Qt, no filesystem access."""

from __future__ import annotations

import random
from collections.abc import Iterable
from pathlib import Path

from aperture.core.media import is_url

# Repeat modes, in the order the control-bar button cycles through them.
REPEAT_OFF, REPEAT_ALL, REPEAT_ONE = "off", "all", "one"
REPEAT_MODES = (REPEAT_OFF, REPEAT_ALL, REPEAT_ONE)


class Playlist:
    """Items in the order they were added, plus the order they play in.

    The play order is the list order, or with shuffle on a random one that starts at the
    playing item, so every item plays once before any repeats. Next and previous follow the
    play order; repeat decides what happens at its end.
    """

    def __init__(self, rng: random.Random | None = None) -> None:
        self._items: list[Path] = []
        self._index = -1
        self._order: list[int] = []  # item indexes in play order
        self._repeat = REPEAT_OFF
        self._shuffle = False
        self._rng = rng or random.Random()

    def __len__(self) -> int:
        return len(self._items)

    @property
    def items(self) -> tuple[Path, ...]:
        return tuple(self._items)

    @property
    def index(self) -> int:
        """Cursor position in `items`, -1 when nothing selected."""
        return self._index

    @property
    def current(self) -> Path | None:
        return self._items[self._index] if self._index >= 0 else None

    # --- repeat and shuffle ------------------------------------------------

    @property
    def repeat(self) -> str:
        return self._repeat

    @repeat.setter
    def repeat(self, mode: str) -> None:
        if mode not in REPEAT_MODES:
            raise ValueError(f"unknown repeat mode {mode!r}")
        self._repeat = mode

    @property
    def shuffle(self) -> bool:
        return self._shuffle

    @shuffle.setter
    def shuffle(self, on: bool) -> None:
        self._shuffle = bool(on)
        self._reorder()

    # --- navigation --------------------------------------------------------

    @property
    def has_next(self) -> bool:
        return self.next_index() is not None

    @property
    def has_previous(self) -> bool:
        return self.previous_index() is not None

    def next_index(self, finished: bool = False) -> int | None:
        """What plays after the current item; None when playback should stop.

        `finished` means the current item played to its end (rather than the user asking
        for the next one): only then does repeat-one play it again.
        """
        if not self._items:
            return None
        if self._index < 0:
            return self._order[0]
        if finished and self._repeat == REPEAT_ONE:
            return self._index
        position = self._order.index(self._index)
        if position + 1 < len(self._order):
            return self._order[position + 1]
        return self._order[0] if self._repeat != REPEAT_OFF else None

    def previous_index(self) -> int | None:
        if self._index < 0:
            return None
        position = self._order.index(self._index)
        if position > 0:
            return self._order[position - 1]
        return self._order[-1] if self._repeat != REPEAT_OFF and len(self._order) > 1 else None

    def advance(self, finished: bool = False) -> int | None:
        """Like next_index, but a shuffled playlist that wraps around is reshuffled first."""
        target = self.next_index(finished)
        if target is None or not self._shuffle or self._index < 0 or target == self._index:
            return target
        if self._order.index(self._index) == len(self._order) - 1:  # wrapping around
            rest = [i for i in self._order if i != self._index]
            self._rng.shuffle(rest)
            self._order = rest + [self._index]  # the item just played comes last
            return self._order[0]
        return target

    # --- editing -----------------------------------------------------------

    def add(self, paths: Iterable[Path | str]) -> int:
        """Append paths, cursor untouched. Returns count added.

        Shuffled, the new items land at random places among those not played yet.
        """
        before = len(self._items)
        self._items.extend(p if is_url(p) else Path(p) for p in paths)
        added = list(range(before, len(self._items)))
        if not self._shuffle:
            self._order.extend(added)
            return len(added)
        start = self._order.index(self._index) + 1 if self._index >= 0 else 0
        for item in added:
            self._order.insert(self._rng.randint(start, len(self._order)), item)
        return len(added)

    def select(self, index: int) -> Path:
        self._check(index)
        self._index = index
        return self._items[index]

    def remove(self, index: int) -> None:
        """Drop one item. Removing current moves cursor onto its successor (or new last)."""
        self._check(index)
        del self._items[index]
        self._order = [i - (i > index) for i in self._order if i != index]
        if index < self._index:
            self._index -= 1
        elif index == self._index:
            self._index = min(self._index, len(self._items) - 1)

    def clear(self) -> None:
        self._items.clear()
        self._order.clear()
        self._index = -1

    def _reorder(self) -> None:
        order = list(range(len(self._items)))
        if self._shuffle:
            self._rng.shuffle(order)
            if self._index >= 0:  # the playing item stays first; the rest follow at random
                order.remove(self._index)
                order.insert(0, self._index)
        self._order = order

    def _check(self, index: int) -> None:
        if not 0 <= index < len(self._items):
            raise IndexError(index)
