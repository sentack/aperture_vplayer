"""QMediaPlayer bound to a Playlist, exposed to QML as `player`."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from PySide6.QtCore import Property, QObject, QTimer, QUrl, Signal, Slot
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer

from aperture.core import (
    RATES,
    History,
    Playlist,
    dialog_filters,
    expand_paths,
    format_rate,
    format_time,
    step_rate,
)
from aperture.player.tracks import TrackSelector, is_subtitle
from aperture.player.urls import to_paths

# "Previous" restarts the current file once playback is past this point.
RESTART_THRESHOLD_MS = 3000
# How often the resume point is written while playing.
CHECKPOINT_INTERVAL_MS = 10_000

_UNLOADED = (
    QMediaPlayer.MediaStatus.NoMedia,
    QMediaPlayer.MediaStatus.LoadingMedia,
    QMediaPlayer.MediaStatus.InvalidMedia,
)


class PlayerController(QObject):
    playingChanged = Signal()
    positionChanged = Signal()
    durationChanged = Signal()
    seekableChanged = Signal()
    volumeChanged = Signal()
    mutedChanged = Signal()
    playlistChanged = Signal()
    errorChanged = Signal()
    rateChanged = Signal()
    recentChanged = Signal()
    # Short-lived feedback for the UI toast ("Speed 1.5×", "Resumed at 14:22").
    noticed = Signal(str)

    def __init__(self, history: History | None = None, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._playlist = Playlist()
        self._history = history if history is not None else History()
        self._loaded: Path | None = None  # file currently set as the player's source
        self._pending_resume: int | None = None
        self._error = ""

        self._audio = QAudioOutput(self)
        self._player = QMediaPlayer(self)
        self._player.setAudioOutput(self._audio)
        self.tracks = TrackSelector(self._player, self)
        self.tracks.noticed.connect(self.noticed)

        self._checkpoint_timer = QTimer(self)
        self._checkpoint_timer.setInterval(CHECKPOINT_INTERVAL_MS)
        self._checkpoint_timer.timeout.connect(self._checkpoint)

        self._player.playbackStateChanged.connect(self._on_playback_state)
        self._player.positionChanged.connect(lambda _: self.positionChanged.emit())
        self._player.durationChanged.connect(lambda _: self.durationChanged.emit())
        self._player.seekableChanged.connect(self._on_seekable)
        self._player.playbackRateChanged.connect(lambda _: self.rateChanged.emit())
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

    def _get_rate(self) -> float:
        return self._player.playbackRate()

    def _set_rate(self, value: float) -> None:
        self._player.setPlaybackRate(min(RATES[-1], max(RATES[0], value)))

    rate = Property(float, _get_rate, _set_rate, notify=rateChanged)

    @Property(str, notify=rateChanged)
    def rateLabel(self) -> str:
        return format_rate(self._player.playbackRate())

    @Property(list, constant=True)
    def rates(self) -> list[float]:
        return list(RATES)

    @Property(list, notify=recentChanged)
    def recentFiles(self) -> list[dict[str, str]]:
        entries = []
        for path in self._history.recent:
            resume = self._history.resume_point(path)
            entries.append(
                {
                    "name": path.name,
                    "folder": path.parent.name,
                    "path": str(path),
                    "resume": format_time(resume / 1000) if resume else "",
                }
            )
        return entries

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
        """Replace the playlist and start its first file. Folders expand to their videos."""
        files = expand_paths(paths)
        if not files:
            return
        self._checkpoint()
        self._playlist.clear()
        self._playlist.add(files)
        self._load(0)

    def add_paths(self, paths: Iterable[Path | str]) -> None:
        """Append to the playlist; start playing only if nothing is loaded."""
        start = len(self._playlist)
        if not self._playlist.add(expand_paths(paths)):
            return
        if self._playlist.current is None:
            self._load(start)
        else:
            self.playlistChanged.emit()

    @Slot(list)
    def openUrls(self, urls: list) -> None:
        self.open_paths(self._take_subtitles(to_paths(urls)))

    @Slot(list)
    def addUrls(self, urls: list) -> None:
        self.add_paths(self._take_subtitles(to_paths(urls)))

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

    @Slot(str)
    def openRecent(self, path: str) -> None:
        if Path(path).is_file():
            self.open_paths([path])
            return
        self._history.remove_recent(path)
        self._history.save()
        self.recentChanged.emit()
        self.noticed.emit(f"Not found: {Path(path).name}")

    @Slot()
    def clearRecent(self) -> None:
        self._history.clear_recent()
        self._history.save()
        self.recentChanged.emit()

    @Slot()
    def stop(self) -> None:
        self._checkpoint()
        self._player.stop()

    @Slot(int)
    def seek(self, position_ms: int) -> None:
        if self._player.isSeekable():
            self._player.setPosition(min(max(0, position_ms), self._player.duration()))

    @Slot(int)
    def seekBy(self, delta_ms: int) -> None:
        if not self._player.isSeekable():
            return
        duration = self._player.duration()
        target = min(max(0, self._player.position() + delta_ms), duration)
        self._player.setPosition(target)
        self.noticed.emit(f"{format_time(target / 1000)} / {format_time(duration / 1000)}")

    @Slot(float)
    def adjustVolume(self, delta: float) -> None:
        self._set_volume(self._audio.volume() + delta)
        self.noticed.emit(f"Volume {round(self._audio.volume() * 100)}%")

    @Slot(int)
    def stepRate(self, steps: int) -> None:
        self._set_rate(step_rate(self._player.playbackRate(), steps))
        self.noticed.emit(f"Speed {self.rateLabel}")

    @Slot()
    def resetRate(self) -> None:
        self._set_rate(1.0)
        self.noticed.emit(f"Speed {self.rateLabel}")

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
        self.noticed.emit("Muted" if self._audio.isMuted() else "Sound on")

    @Slot(int, result=str)
    def formatTime(self, ms: int) -> str:
        return format_time(ms / 1000)

    @Slot()
    def shutdown(self) -> None:
        """Persist the resume point; call before the app quits."""
        self._checkpoint()

    # --- internals ---------------------------------------------------------

    def _take_subtitles(self, paths: list[Path]) -> list[Path]:
        """Route dropped or picked subtitle files to the loaded video; return the rest."""
        subtitles = [p for p in paths if is_subtitle(p) and p.is_file()]
        if subtitles:
            if self._loaded is None:
                self.noticed.emit("Open a video before adding subtitles")
            else:
                self.tracks.add_files(subtitles)
        return [p for p in paths if p not in subtitles]

    def _load(self, index: int) -> None:
        self._checkpoint()
        path = self._playlist.select(index)
        self._set_error("")
        self._history.touch(path)
        self._loaded = path
        self._pending_resume = self._history.resume_point(path)
        self._player.setSource(QUrl.fromLocalFile(str(path)))
        self.tracks.reset(path)
        self._player.play()
        self._history.save()
        self.playlistChanged.emit()
        self.recentChanged.emit()

    def _unload(self) -> None:
        self._checkpoint()
        self._loaded = None
        self._pending_resume = None
        self._player.stop()
        self._player.setSource(QUrl())
        self.tracks.reset(None)
        self._set_error("")
        self.playlistChanged.emit()

    def _checkpoint(self) -> None:
        """Record the loaded file's position as its resume point."""
        # Before a pending resume lands, position is 0 and would wipe the stored point.
        if self._loaded is None or self._pending_resume is not None:
            return
        if self._player.mediaStatus() in _UNLOADED:
            return
        position, duration = self._player.position(), self._player.duration()
        self._history.remember_position(self._loaded, position, duration)
        self._history.save()
        self.recentChanged.emit()

    def _apply_resume(self) -> None:
        target = self._pending_resume
        if target is None or not self._player.isSeekable():
            return
        self._pending_resume = None
        duration = self._player.duration()
        if duration and target >= duration:
            return
        self._player.setPosition(target)
        self.noticed.emit(f"Resumed at {format_time(target / 1000)}")

    def _on_playback_state(self, state: QMediaPlayer.PlaybackState) -> None:
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self._checkpoint_timer.start()
        else:
            self._checkpoint_timer.stop()
            # Stopped already rewound to 0; stop() checkpoints before that happens.
            if state == QMediaPlayer.PlaybackState.PausedState:
                self._checkpoint()
        self.playingChanged.emit()

    def _on_seekable(self, seekable: bool) -> None:
        if seekable:
            self._apply_resume()
        self.seekableChanged.emit()

    def _on_media_status(self, status: QMediaPlayer.MediaStatus) -> None:
        if status in (QMediaPlayer.MediaStatus.LoadedMedia, QMediaPlayer.MediaStatus.BufferedMedia):
            self._apply_resume()
        elif status == QMediaPlayer.MediaStatus.InvalidMedia:
            self._pending_resume = None
        elif status == QMediaPlayer.MediaStatus.EndOfMedia:
            if self._loaded is not None:
                self._history.forget_position(self._loaded)
                self._history.save()
                self.recentChanged.emit()
            if self._playlist.has_next:
                self._load(self._playlist.index + 1)

    def _set_error(self, message: str) -> None:
        if message != self._error:
            self._error = message
            self.errorChanged.emit()
