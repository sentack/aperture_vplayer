"""Saved and recently used playlists, exposed to QML as `playlists`.

Saving writes an `.aplaylist` (or `.m3u8` when asked) and remembers it; opening a playlist
file, and replacing or closing a playlist of two or more items, add to the recent list, from
which any of them can be reopened.

A playlist opened from (or saved to) a file stays tied to it: adding or removing files marks
it unsaved, and `saveChanges` writes them back, or autosave does as they happen.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import Property, QObject, QTimer, QUrl, Signal, Slot

from aperture.core.formats import PLAYLIST_EXTENSIONS
from aperture.core.playlist_file import (
    PLAYLIST_EXTENSION,
    keep_missing,
    read_playlist,
    write_playlist,
)
from aperture.core.playlist_history import PlaylistHistory
from aperture.core.timefmt import format_time

log = logging.getLogger(__name__)

# Autosave waits this long after a change, so adding a folder of files is one write.
AUTOSAVE_DELAY_MS = 400


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
    fileChanged = Signal()  # the playlist's file, or whether it has unsaved changes
    noticed = Signal(str)
    # A playlist file was written: on Linux the .aplaylist type is registered then.
    saved = Signal(str)

    def __init__(
        self,
        player: QObject,
        history: PlaylistHistory,
        clock: Callable[[], float] = time.time,
        parent: QObject | None = None,
        autosave: Callable[[], bool] = lambda: False,
    ) -> None:
        super().__init__(parent)
        self._player = player  # PlayerController
        self._history = history
        self._clock = clock
        self._autosave = autosave
        # The file the playlist came from, what it lists, and the playlist as last written.
        self._file: Path | None = None
        self._entries: list = []
        self._written: list[str] = []
        self._unsaved = False
        self._autosave_timer = QTimer(self, singleShot=True, interval=AUTOSAVE_DELAY_MS)
        self._autosave_timer.timeout.connect(self._write_back)
        player.playlistRetired.connect(self._remember)
        player.playlistFileOpened.connect(self._opened_file)
        player.playlistReplaced.connect(self._detach)
        player.playlistChanged.connect(self.refresh)

    @Property(str, notify=fileChanged)
    def fileName(self) -> str:
        """The open playlist file's name, "" when the playlist isn't from a file."""
        return self._file.name if self._file is not None else ""

    @Property(bool, notify=fileChanged)
    def unsaved(self) -> bool:
        """Files were added or removed since the playlist file was opened or saved."""
        return self._unsaved

    @Slot(result=bool)
    def saveChanges(self) -> bool:
        """Write the playlist back into the file it came from."""
        self._autosave_timer.stop()
        if self._file is None:
            return False
        if not self._write_back():
            return False
        self.noticed.emit(f"Saved changes to {self._file.name}")
        return True

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
        self._attach(path, list(items), items)
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
        if entry.saved and Path(entry.saved).is_file():
            # Its file, as it is now: that keeps the playlist tied to it, ready to save.
            self._player.open_paths([Path(entry.saved)])
            return
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
        try:
            entries = read_playlist(Path(path))
        except (OSError, ValueError):
            entries = None
        self._attach(Path(path), entries if entries is not None else list(items), items)

    # --- the playlist's file -------------------------------------------------

    def _attach(self, path: Path, entries: list, items: list) -> None:
        self._file = path
        self._entries = entries
        self._written = [str(item) for item in items]
        self._set_unsaved(False)
        self.fileChanged.emit()

    def _detach(self) -> None:
        if self._autosave_timer.isActive():  # a change still to save, before it goes
            self._autosave_timer.stop()
            self._write_back()
        if self._file is not None:
            self._file = None
            self._entries, self._written = [], []
            self._set_unsaved(False)
            self.fileChanged.emit()

    def refresh(self) -> None:
        """Compare the playlist with its file; autosave, if on, writes the difference."""
        if self._file is None:
            return
        current = [str(item) for item in self._player.playlist_items()]
        self._set_unsaved(current != self._written)
        if self._unsaved and self._autosave() and current:
            self._autosave_timer.start()

    def _set_unsaved(self, unsaved: bool) -> None:
        if unsaved != self._unsaved:
            self._unsaved = unsaved
            self.fileChanged.emit()

    def _write_back(self) -> bool:
        if self._file is None:
            return False
        items = list(self._player.playlist_items())
        entries = keep_missing(self._entries, self._written, items)
        try:
            write_playlist(self._file, entries, self._player.durations.known())
        except OSError as exc:
            log.warning("cannot save playlist %s", self._file, exc_info=True)
            self.noticed.emit(f"Couldn't save {self._file.name}: {exc.strerror or exc}")
            return False
        self._entries = entries
        self._written = [str(item) for item in items]
        self._set_unsaved(False)
        self._history.record(
            items, self._clock(), name=self._file.stem, saved=str(self._file),
            durations=self._player.durations.known(),
        )  # fmt: skip
        self._history.save()
        self.changed.emit()
        self.saved.emit(str(self._file))
        return True
