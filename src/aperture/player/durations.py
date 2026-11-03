"""Lengths of playlist items that have not been played yet, found in the background.

Tags first: mutagen reads MP3, FLAC, Ogg and MP4/M4A lengths from headers at once. Anything
else (MKV, WebM, AVI…) is opened by a silent QMediaPlayer, one file at a time, which reports
the duration as soon as the container is parsed. Results are cached for the session.
"""

from __future__ import annotations

import logging
from collections import deque
from pathlib import Path

from PySide6.QtCore import QObject, QTimer, QUrl, Signal
from PySide6.QtMultimedia import QMediaPlayer

from aperture.core.media import is_url

log = logging.getLogger(__name__)

PROBE_TIMEOUT_MS = 5_000
UNKNOWN = -1  # probed, but the length could not be found


def tag_duration(path: Path) -> int | None:
    """Length in ms from the file's headers, or None when mutagen cannot tell."""
    try:
        from mutagen import File as MutagenFile

        audio = MutagenFile(path)
    except Exception:  # noqa: BLE001 — any unreadable file: fall back to the decoder
        return None
    length = getattr(getattr(audio, "info", None), "length", None)
    return round(length * 1000) if isinstance(length, int | float) and length > 0 else None


class DurationProbe(QObject):
    changed = Signal()  # new lengths are known

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._known: dict[str, int] = {}  # str(path) -> ms, or UNKNOWN
        self._queue: deque[Path] = deque()
        self._current: Path | None = None
        self._decoder = QMediaPlayer(self)  # no audio or video output: never plays
        self._decoder.mediaStatusChanged.connect(self._on_status)
        self._timeout = QTimer(self, singleShot=True, interval=PROBE_TIMEOUT_MS)
        self._timeout.timeout.connect(self._give_up)
        self._batch = QTimer(self, singleShot=True, interval=0)
        self._batch.timeout.connect(self.changed)

    def duration(self, item: Path | str) -> int | None:
        """Length in ms; None while unknown or not found."""
        value = self._known.get(str(item))
        return value if value is not None and value > 0 else None

    def known(self) -> dict[str, int]:
        return {k: v for k, v in self._known.items() if v > 0}

    def remember(self, item: Path | str, duration_ms: int) -> None:
        """A length found elsewhere: the main player, or a saved playlist."""
        if duration_ms > 0 and self._known.get(str(item)) != duration_ms:
            self._known[str(item)] = duration_ms
            self._batch.start()

    def request(self, items: list[Path | str]) -> None:
        """Find the lengths of `items` not known yet. Streams are skipped (often endless)."""
        for item in items:
            if is_url(item) or str(item) in self._known:
                continue
            path = Path(item)
            if path in self._queue or path == self._current:
                continue
            found = tag_duration(path)
            if found is not None:
                self.remember(path, found)
            else:
                self._queue.append(path)
        self._next()

    def stop(self) -> None:
        self._queue.clear()
        self._timeout.stop()
        self._current = None
        self._decoder.setSource(QUrl())

    def _next(self) -> None:
        if self._current is not None or not self._queue:
            return
        self._current = self._queue.popleft()
        self._timeout.start()
        self._decoder.setSource(QUrl.fromLocalFile(str(self._current)))

    def _on_status(self, status: QMediaPlayer.MediaStatus) -> None:
        if self._current is None:
            return
        if status in (QMediaPlayer.MediaStatus.LoadedMedia, QMediaPlayer.MediaStatus.BufferedMedia):
            self._done(self._decoder.duration())
        elif status == QMediaPlayer.MediaStatus.InvalidMedia:
            self._done(UNKNOWN)

    def _give_up(self) -> None:
        if self._current is not None:
            log.info("no length for %s within %d ms", self._current, PROBE_TIMEOUT_MS)
            self._done(UNKNOWN)

    def _done(self, duration_ms: int) -> None:
        self._timeout.stop()
        path, self._current = self._current, None
        self._known[str(path)] = duration_ms if duration_ms > 0 else UNKNOWN
        self._batch.start()
        self._decoder.setSource(QUrl())
        self._next()
