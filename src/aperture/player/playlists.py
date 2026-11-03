"""Saved and recently used playlists, exposed to QML as `playlists`.

Saving writes an `.aplaylist` (or `.m3u8` when asked) and remembers it; opening a playlist
file, and replacing or closing a playlist of two or more items, add to the recent list, from
which any of them can be reopened.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import Property, QObject, QUrl, Signal, Slot

from aperture.core.formats import PLAYLIST_EXTENSIONS
from aperture.core.playlist_file import PLAYLIST_EXTENSION, write_playlist
from aperture.core.playlist_history import PlaylistHistory
from aperture.core.timefmt import format_time

log = logging.getLogger(__name__)


def when(then: float, now: float) -> str:
    """"Today", "Yesterday", "3 days ago", or a date for older ones."""
    days = int((now - then) // 86_400) if then else -1
    if days < 0:
        return ""
    if days == 0:
        return "Today"
    if days == 1:
        return "Yesterday"
    if days < 7:
        return f"{days} days ago"
    local = time.localtime(then)
    return f"{local.tm_mday} {time.strftime('%b %Y', local)}"


class PlaylistLibrary(QObject):
    changed = Signal()
    noticed = Signal(str)
    # A playlist file was written: on Linux the .aplaylist type is registered then.
    saved = Signal(str)

    def __init__(
        self,
        player: QObject,
        history: PlaylistHistory,
        clock: Callable[[], float] = time.time,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._player = player  # PlayerController
        self._history = history
        self._clock = clock
        player.playlistRetired.connect(self._remember)
        player.playlistFileOpened.connect(self._opened_file)

    @Property(list, notify=changed)
    def recent(self) -> list[dict[str, str]]:
        """Newest first: name, and "12 items · 1:02:13 · Yesterday"."""
        now = self._clock()
        rows = []
        for entry in self._history.entries:
            lengths = [entry.durations.get(item, 0) for item in entry.items]
            parts = [f"{len(entry.items)} items" if len(entry.items) != 1 else "1 item"]
            if all(lengths):
                parts.append(format_time(sum(lengths) / 1000))
            parts.append(when(entry.used, now))
            rows.append(
                {
                    "name": entry.name,
                    "detail": " · ".join(p for p in parts if p),
                    "saved": entry.saved,
                }
            )
        return rows

    @Property(bool, notify=changed)
    def hasRecent(self) -> bool:
        return bool(self._history.entries)

    @Slot(QUrl, result=bool)
    def save(self, url: QUrl) -> bool:
        """Write the current playlist to `url` (a file dialog's choice)."""
        items = self._player.playlist_items()
        if not items:
            self.noticed.emit("The playlist is empty")
            return False
        path = Path(url.toLocalFile() if url.isLocalFile() else url.toString())
        if path.suffix.lower() not in PLAYLIST_EXTENSIONS:
            path = path.with_name(path.name + PLAYLIST_EXTENSION)
        durations = self._player.durations.known()
        try:
            write_playlist(path, items, durations)
        except OSError as exc:
            log.warning("cannot save playlist %s", path, exc_info=True)
            self.noticed.emit(f"Couldn't save the playlist: {exc.strerror or exc}")
            return False
        self._history.record(
            items, self._clock(), name=path.stem, saved=str(path), durations=durations
        )
        self._history.save()
        self.changed.emit()
        self.noticed.emit(f"Saved playlist {path.name}")
        self.saved.emit(str(path))
        return True

    @Slot(int)
    def open(self, index: int) -> None:
        entries = self._history.entries
        if not 0 <= index < len(entries):
            return
        entry = entries[index]
        for item, length in entry.durations.items():
            self._player.durations.remember(item, length)
        self._player.open_paths(list(entry.items))
        self._history.record(list(entry.items), self._clock())  # now the newest
        self._history.save()
        self.changed.emit()

    @Slot(int)
    def remove(self, index: int) -> None:
        self._history.remove(index)
        self._history.save()
        self.changed.emit()

    @Slot()
    def clear(self) -> None:
        self._history.clear()
        self._history.save()
        self.changed.emit()

    def _remember(self, items: list) -> None:
        durations = self._player.durations.known()
        if self._history.record(items, self._clock(), durations=durations):
            self._history.save()
            self.changed.emit()

    def _opened_file(self, path: str, items: list) -> None:
        stem = Path(path).stem
        self._history.record(items, self._clock(), name=stem, saved=path)
        self._history.save()
        self.changed.emit()
