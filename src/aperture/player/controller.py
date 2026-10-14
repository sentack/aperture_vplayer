"""QMediaPlayer bound to a Playlist, exposed to QML as `player`."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from PySide6.QtCore import Property, QObject, QUrl, Signal, Slot
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer

from aperture.core import Playlist, dialog_filters, format_time

# "Previous" restarts the current file once playback is past this point.
RESTART_THRESHOLD_MS = 3000


def _to_paths(urls: Iterable[object]) -> list[Path]:
    paths = []
    for url in urls:
        url = url if isinstance(url, QUrl) else QUrl(str(url))
        paths.append(Path(url.toLocalFile() if url.isLocalFile() else url.toString()))
    return paths


class PlayerController(QObject):
    playingChanged = Signal()
    positionChanged = Signal()
    durationChanged = Signal()
    seekableChanged = Signal()
    volumeChanged = Signal()
    mutedChanged = Signal()
    playlistChanged = Signal()
    errorChanged = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._playlist = Playlist()
        self._error = ""

        self._audio = QAudioOutput(self)
        self._player = QMediaPlayer(self)
        self._player.setAudioOutput(self._audio)

        self._player.playbackStateChanged.connect(lambda _: self.playingChanged.emit())
        self._player.positionChanged.connect(lambda _: self.positionChanged.emit())
        self._player.durationChanged.connect(lambda _: self.durationChanged.emit())
        self._player.seekableChanged.connect(lambda _: self.seekableChanged.emit())
        self._player.mediaStatusChanged.connect(self._on_media_status)
        self._player.errorOccurred.connect(lambda _, message: self._set_error(message))
        self._audio.volumeChanged.connect(lambda _: self.volumeChanged.emit())
        self._audio.mutedChanged.connect(lambda _: self.mutedChanged.emit())

    # --- state -------------------------------------------------------------

    @Property(bool, notify=playingChanged)
    def playing(self) -> bool:
        return self._player.playbackState() == QMediaPlayer.PlaybackState.PlayingState

    @Property(int, notify=positionChanged)
    def position(self) -> int:
        return self._player.position()

    @Property(int, notify=durationChanged)
    def duration(self) -> int:
        return self._player.duration()

    @Property(bool, notify=seekableChanged)
    def seekable(self) -> bool:
        return self._player.isSeekable()

    def _get_volume(self) -> float:
        return self._audio.volume()

    def _set_volume(self, value: float) -> None:
        value = min(1.0, max(0.0, value))
        self._audio.setVolume(value)
        if value > 0 and self._audio.isMuted():
            self._audio.setMuted(False)

    volume = Property(float, _get_volume, _set_volume, notify=volumeChanged)

    @Property(bool, notify=mutedChanged)
    def muted(self) -> bool:
        return self._audio.isMuted()

    @Property(str, notify=errorChanged)
    def error(self) -> str:
        return self._error

    # --- playlist ----------------------------------------------------------

    @Property(bool, notify=playlistChanged)
    def hasMedia(self) -> bool:
        return self._playlist.current is not None

    @Property(str, notify=playlistChanged)
    def title(self) -> str:
        current = self._playlist.current
        return current.stem if current else ""

    @Property(str, notify=playlistChanged)
    def subtitle(self) -> str:
        current = self._playlist.current
        if current is None:
            return ""
        kind = current.suffix.lstrip(".").upper()
        return f"{self._playlist.index + 1} of {len(self._playlist)} · {kind}"

    @Property(list, notify=playlistChanged)
    def playlist(self) -> list[str]:
        return [path.name for path in self._playlist.items]

    @Property(int, notify=playlistChanged)
    def currentIndex(self) -> int:
        return self._playlist.index

    @Property(bool, notify=playlistChanged)
    def hasNext(self) -> bool:
        return self._playlist.has_next

    @Property(bool, notify=playlistChanged)
    def hasPrevious(self) -> bool:
        return self._playlist.has_previous

    @Property(list, constant=True)
    def nameFilters(self) -> list[str]:
        return dialog_filters()

    # --- commands ----------------------------------------------------------

    @Slot(QObject)
    def attachVideoOutput(self, output: QObject) -> None:
        self._player.setVideoOutput(output)

    def open_paths(self, paths: Iterable[Path | str]) -> None:
        """Replace the playlist and start its first file."""
        files = [Path(p) for p in paths if Path(p).is_file()]
        if not files:
            return
        self._playlist.clear()
        self._playlist.add(files)
        self._load(0)

    def add_paths(self, paths: Iterable[Path | str]) -> None:
        """Append to the playlist; start playing only if nothing is loaded."""
        start = len(self._playlist)
        if not self._playlist.add(Path(p) for p in paths if Path(p).is_file()):
            return
        if self._playlist.current is None:
            self._load(start)
        else:
            self.playlistChanged.emit()

    @Slot(list)
    def openUrls(self, urls: list) -> None:
        self.open_paths(_to_paths(urls))

    @Slot(list)
    def addUrls(self, urls: list) -> None:
        self.add_paths(_to_paths(urls))

    @Slot(int)
    def playIndex(self, index: int) -> None:
        if 0 <= index < len(self._playlist):
            self._load(index)

    @Slot(int)
    def removeIndex(self, index: int) -> None:
        if not 0 <= index < len(self._playlist):
            return
        was_current = index == self._playlist.index
        self._playlist.remove(index)
        if not was_current:
            self.playlistChanged.emit()
        elif self._playlist.current is None:
            self._unload()
        else:
            self._load(self._playlist.index)

    @Slot()
    def clearPlaylist(self) -> None:
        self._playlist.clear()
        self._unload()

    @Slot()
    def togglePlay(self) -> None:
        if self.playing:
            self._player.pause()
        elif self._playlist.current is not None:
            self._player.play()

    @Slot()
    def stop(self) -> None:
        self._player.stop()

    @Slot(int)
    def seek(self, position_ms: int) -> None:
        if self._player.isSeekable():
            self._player.setPosition(min(max(0, position_ms), self._player.duration()))

    @Slot()
    def playNext(self) -> None:
        if self._playlist.has_next:
            self._load(self._playlist.index + 1)

    @Slot()
    def playPrevious(self) -> None:
        if self._player.position() > RESTART_THRESHOLD_MS or not self._playlist.has_previous:
            self.seek(0)
        else:
            self._load(self._playlist.index - 1)

    @Slot()
    def toggleMute(self) -> None:
        self._audio.setMuted(not self._audio.isMuted())

    @Slot(int, result=str)
    def formatTime(self, ms: int) -> str:
        return format_time(ms / 1000)

    # --- internals ---------------------------------------------------------

    def _load(self, index: int) -> None:
        path = self._playlist.select(index)
        self._set_error("")
        self._player.setSource(QUrl.fromLocalFile(str(path)))
        self._player.play()
        self.playlistChanged.emit()

    def _unload(self) -> None:
        self._player.stop()
        self._player.setSource(QUrl())
        self._set_error("")
        self.playlistChanged.emit()

    def _on_media_status(self, status: QMediaPlayer.MediaStatus) -> None:
        if status == QMediaPlayer.MediaStatus.EndOfMedia and self._playlist.has_next:
            self._load(self._playlist.index + 1)

    def _set_error(self, message: str) -> None:
        if message != self._error:
            self._error = message
            self.errorChanged.emit()
