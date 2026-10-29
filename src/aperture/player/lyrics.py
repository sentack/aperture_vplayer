"""Lyrics for the playing audio file, exposed to QML as `lyrics`.

Sources, in order: a sidecar `<stem>.lrc` / `<stem>.txt`, then lyrics embedded in the file's
tags. The editor saves an LRC sidecar and can also embed the same text into the file.
"""

from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import Property, QObject, Signal, Slot

from aperture.core import LyricLine, LyricsTrack, find_lyrics, format_lrc, is_audio, parse_lyrics
from aperture.core.subtitles import decode
from aperture.player.urls import to_paths

log = logging.getLogger(__name__)


class LyricsController(QObject):
    changed = Signal()
    currentChanged = Signal()
    noticed = Signal(str)

    def __init__(self, player: QObject, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._player = player  # PlayerController: position, seek(), mediaLoaded
        self._audio: Path | None = None
        self._track = LyricsTrack([])
        self._source = ""
        self._current = -1

        player.mediaLoaded.connect(self._on_media)
        player.positionChanged.connect(self._follow)

    # --- state -------------------------------------------------------------

    @Property(bool, notify=changed)
    def audioFile(self) -> bool:
        """True while an audio file is loaded: the player shows lyrics instead of video."""
        return self._audio is not None

    @Property(bool, notify=changed)
    def available(self) -> bool:
        return bool(self._track.lines)

    @Property(bool, notify=changed)
    def synced(self) -> bool:
        return self._track.synced

    @Property(list, notify=changed)
    def lines(self) -> list[dict[str, object]]:
        return [
            {"time": -1 if line.time_ms is None else line.time_ms, "text": line.text}
            for line in self._track.lines
        ]

    @Property(str, notify=changed)
    def source(self) -> str:
        return self._source

    @Property(str, notify=changed)
    def plainText(self) -> str:
        """Current lyrics without timing, as a starting point for the editor."""
        return "\n".join(line.text for line in self._track.lines if line.text)

    @Property(bool, notify=changed)
    def canEmbed(self) -> bool:
        from aperture.core.lyrics_tags import EMBEDDABLE

        return self._audio is not None and self._audio.suffix.lower() in EMBEDDABLE

    @Property(int, notify=currentChanged)
    def currentIndex(self) -> int:
        return self._current

    # --- commands ----------------------------------------------------------

    @Slot(int)
    def seekToLine(self, index: int) -> None:
        if self._track.synced and 0 <= index < len(self._track.lines):
            self._player.seek(self._track.lines[index].time_ms)

    @Slot(list)
    def loadUrls(self, urls: list) -> None:
        self.load_files(to_paths(urls))

    def load_files(self, paths: list[Path | str]) -> None:
        if self._audio is None:
            self.noticed.emit("Play an audio file before adding lyrics")
            return
        for path in map(Path, paths):
            if self._load_file(path):
                self.noticed.emit(f"Lyrics: {path.name}")
                return
        self.noticed.emit("No lyrics found in that file")

    @Slot(list, bool)
    def save(self, rows: list, embed: bool) -> None:
        """Write `rows` ({time: ms or -1, text}) as `<stem>.lrc`, and into the file if `embed`."""
        if self._audio is None:
            return
        lines = [
            LyricLine(None if int(row.get("time", -1)) < 0 else int(row["time"]), str(row["text"]))
            for row in rows
            if str(row.get("text", "")).strip() or int(row.get("time", -1)) >= 0
        ]
        if not lines:
            self.noticed.emit("Nothing to save")
            return
        text = format_lrc(lines)
        sidecar = self._audio.with_suffix(".lrc")
        try:
            sidecar.write_text(text, encoding="utf-8")
        except OSError as exc:
            log.warning("cannot write %s", sidecar, exc_info=True)
            self.noticed.emit(f"Couldn't save lyrics: {exc.strerror or exc}")
            return
        message = f"Saved {sidecar.name}"
        if embed:
            from aperture.core.lyrics_tags import LyricsTagError, embed as embed_lyrics

            try:
                embed_lyrics(self._audio, text)
                message += " and embedded it"
            except LyricsTagError as exc:
                log.warning("embedding lyrics failed: %s", exc)
                message += f" — couldn't embed: {exc}"
        self._set_track(lines, sidecar.name)
        self.noticed.emit(message)

    # --- internals ---------------------------------------------------------

    def _on_media(self, path: str) -> None:
        self._audio = Path(path) if path and is_audio(path) else None
        self._set_track([], "")
        if self._audio is None:
            return
        sidecar = find_lyrics(self._audio)
        if sidecar is not None and self._load_file(sidecar):
            return
        from aperture.core.lyrics_tags import read_embedded

        embedded = read_embedded(self._audio)
        if embedded:
            self._set_track(parse_lyrics(embedded), "Embedded")

    def _load_file(self, path: Path) -> bool:
        try:
            lines = parse_lyrics(decode(path.read_bytes()))
        except OSError:
            log.warning("cannot read lyrics %s", path, exc_info=True)
            return False
        if not lines:
            return False
        self._set_track(lines, path.name)
        return True

    def _set_track(self, lines: list[LyricLine], source: str) -> None:
        self._track = LyricsTrack(lines)
        self._source = source
        self.changed.emit()
        self._follow()

    def _follow(self) -> None:
        index = self._track.index_at(self._player.position) if self._track.synced else -1
        if index != self._current:
            self._current = index
            self.currentChanged.emit()
