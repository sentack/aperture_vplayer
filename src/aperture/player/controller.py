"""QMediaPlayer bound to a Playlist, exposed to QML as `player`."""

from __future__ import annotations

import logging
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Property, QObject, QStandardPaths, QTimer, QUrl, Signal, Slot
from PySide6.QtMultimedia import QAudioOutput, QMediaMetaData, QMediaPlayer

from aperture.core import (
    RATES,
    History,
    Playlist,
    describe_error,
    dialog_filters,
    expand_paths,
    format_rate,
    format_time,
    step_rate,
)
from aperture.core.chapters import Chapter, chapter_at, read_chapters
from aperture.core.media import (
    display_name,
    display_stem,
    folder_label,
    frame_ms,
    is_url,
    kind_label,
    parse_stream_url,
    screenshot_name,
)
from aperture.player.boost import AudioBoost, make_capture
from aperture.player.tracks import TrackSelector, is_subtitle
from aperture.player.urls import to_paths

# "Previous" restarts the current file once playback is past this point.
RESTART_THRESHOLD_MS = 3000
# How often the resume point is written while playing.
CHECKPOINT_INTERVAL_MS = 10_000
# A "Resume from 14:22?" offer left unanswered this long counts as "start over".
RESUME_OFFER_MS = 12_000
# An A–B loop shorter than this is almost certainly a double tap, not a loop.
MIN_LOOP_MS = 500

log = logging.getLogger(__name__)

_ERROR_KINDS = {
    QMediaPlayer.Error.FormatError: "format",
    QMediaPlayer.Error.ResourceError: "resource",
    QMediaPlayer.Error.AccessDeniedError: "access",
    QMediaPlayer.Error.NetworkError: "network",
}

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
    # Path of the file now set as source, "" once unloaded.
    mediaLoaded = Signal(str)
    # Dropped or picked .lrc files, for the lyrics controller.
    lyricsDropped = Signal(list)
    loopChanged = Signal()
    chaptersChanged = Signal()
    chapterChanged = Signal()
    boostChanged = Signal()
    videoAspectChanged = Signal()
    hasVideoChanged = Signal()
    resumeOfferChanged = Signal()

    def __init__(self, history: History | None = None, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._playlist = Playlist()
        self._history = history if history is not None else History()
        self._loaded: Path | None = None  # file currently set as the player's source
        self._rate = 1.0  # re-applied on every load, so the speed survives file changes
        self._pending_resume: int | None = None  # resume position to seek to once seekable
        self._resume_offer = 0  # saved position the user is being asked about, 0 when none
        self._last_position = 0  # last position seen before a stop rewound to 0
        self._loop_a = -1  # A–B loop bounds in ms; -1 while unset
        self._loop_b = -1
        self._sink = None  # the VideoOutput's QVideoSink, for screenshots
        self._chapters: list[Chapter] = []
        self._chapter = -1
        self._aspect = 0.0
        # What to do with a saved position: ask, resume silently, or always start over.
        self.resume_mode = "ask"
        self._error_title = ""
        self._error = ""

        # The boost's capture object first: it must be destroyed before the player (see
        # make_capture), and children are destroyed in creation order.
        capture = make_capture(self)
        self._audio = QAudioOutput(self)
        self._player = QMediaPlayer(self)
        self._player.setAudioOutput(self._audio)
        self.tracks = TrackSelector(self._player, self)
        self.tracks.noticed.connect(self.noticed)

        self._checkpoint_timer = QTimer(self)
        self._checkpoint_timer.setInterval(CHECKPOINT_INTERVAL_MS)
        self._checkpoint_timer.timeout.connect(self._checkpoint)

        self._offer_timer = QTimer(self)
        self._offer_timer.setSingleShot(True)
        self._offer_timer.setInterval(RESUME_OFFER_MS)
        self._offer_timer.timeout.connect(self.declineResume)

        self._player.playbackStateChanged.connect(self._on_playback_state)
        self._player.positionChanged.connect(self._on_position)
        self._player.durationChanged.connect(lambda _: self.durationChanged.emit())
        self._player.seekableChanged.connect(self._on_seekable)
        self._player.hasVideoChanged.connect(lambda _: self.hasVideoChanged.emit())
        self._player.metaDataChanged.connect(self._on_metadata)
        self.boost = AudioBoost(self._player, self._audio, capture, self)
        self.boost.unavailable.connect(self.noticed)
        self._player.playbackRateChanged.connect(lambda _: self.rateChanged.emit())
        self._player.mediaStatusChanged.connect(self._on_media_status)
        self._player.errorOccurred.connect(self._on_error)
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

    @Property(bool, notify=hasVideoChanged)
    def hasVideo(self) -> bool:
        return self._player.hasVideo()

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

    def _get_boost(self) -> float:
        return self.boost.gain

    def _set_boost(self, value: float) -> None:
        if value != self.boost.gain and self.boost.set_gain(value):
            self.boostChanged.emit()
            self.noticed.emit(f"Audio boost {round(self.boost.gain * 100)}%")

    audioBoost = Property(float, _get_boost, _set_boost, notify=boostChanged)

    @Property(list, constant=True)
    def boostLevels(self) -> list[float]:
        return [1.0, 1.25, 1.5, 2.0]

    @Property(float, notify=videoAspectChanged)
    def videoAspect(self) -> float:
        """Width / height of the picture, 0 until the file reports its resolution."""
        return self._aspect

    # --- chapters ----------------------------------------------------------

    @Property(list, notify=chaptersChanged)
    def chapters(self) -> list[dict[str, object]]:
        return [
            {"time": c.start_ms, "title": c.title or f"Chapter {i + 1}"}
            for i, c in enumerate(self._chapters)
        ]

    @Property(int, notify=chapterChanged)
    def currentChapter(self) -> int:
        return self._chapter

    @Slot(int)
    def seekChapter(self, index: int) -> None:
        if 0 <= index < len(self._chapters):
            self.seek(self._chapters[index].start_ms)
            title = self._chapters[index].title or f"Chapter {index + 1}"
            self.noticed.emit(f"{index + 1}/{len(self._chapters)} · {title}")

    @Slot()
    def nextChapter(self) -> None:
        if not self._chapters:
            self.noticed.emit("This file has no chapters")
            return
        index = chapter_at(self._chapters, self._player.position()) + 1
        if index < len(self._chapters):
            self.seekChapter(index)
        else:
            self.noticed.emit("Already in the last chapter")

    @Slot()
    def previousChapter(self) -> None:
        """Back to this chapter's start, or to the previous one if just past the start."""
        if not self._chapters:
            self.noticed.emit("This file has no chapters")
            return
        position = self._player.position()
        index = chapter_at(self._chapters, position)
        if index > 0 and position - self._chapters[index].start_ms < RESTART_THRESHOLD_MS:
            index -= 1
        self.seekChapter(max(index, 0))

    @Property(str, notify=errorChanged)
    def errorTitle(self) -> str:
        """Short headline for the error card; "" when playback is fine."""
        return self._error_title

    @Property(str, notify=errorChanged)
    def error(self) -> str:
        return self._error

    def _get_rate(self) -> float:
        return self._player.playbackRate()

    def _set_rate(self, value: float) -> None:
        self._rate = min(RATES[-1], max(RATES[0], value))
        self._player.setPlaybackRate(self._rate)

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
                    "name": display_name(path),
                    "folder": folder_label(path),
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
        return display_stem(current) if current else ""

    @Property(str, notify=playlistChanged)
    def subtitle(self) -> str:
        current = self._playlist.current
        if current is None:
            return ""
        position = f"{self._playlist.index + 1} of {len(self._playlist)}"
        kind = kind_label(current)
        return f"{position} · {kind}" if kind else position

    @Property(QUrl, notify=playlistChanged)
    def mediaFolder(self) -> QUrl:
        """Folder of the loaded file, where subtitle pickers start."""
        if self._loaded is None or is_url(self._loaded):
            return QUrl()
        return QUrl.fromLocalFile(str(self._loaded.parent))

    @Property(list, notify=playlistChanged)
    def playlist(self) -> list[str]:
        return [display_name(item) for item in self._playlist.items]

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
        self._sink = output.property("videoSink")

    def open_paths(self, paths: Iterable[Path | str]) -> None:
        """Replace the playlist and start its first file. Folders expand to their videos."""
        paths = list(paths)
        self._report_missing(paths)
        files = expand_paths(paths)
        if not files:
            return
        self._checkpoint()
        self._playlist.clear()
        self._playlist.add(files)
        self._load(0)

    def add_paths(self, paths: Iterable[Path | str]) -> None:
        """Append to the playlist; start playing only if nothing is loaded."""
        paths = list(paths)
        self._report_missing(paths)
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
        if is_url(path):
            self.openUrl(path)
            return
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

    @Property(int, notify=resumeOfferChanged)
    def resumeOffer(self) -> int:
        """Saved position (ms) offered for resuming, 0 when nothing is being offered."""
        return self._resume_offer

    @Property(str, notify=resumeOfferChanged)
    def resumeOfferLabel(self) -> str:
        return format_time(self._resume_offer / 1000) if self._resume_offer else ""

    @Slot()
    def acceptResume(self) -> None:
        target = self._take_offer()
        if not target:
            return
        if self._player.isSeekable():
            self._player.setPosition(target)
        else:
            self._pending_resume = target
        self.noticed.emit(f"Resumed at {format_time(target / 1000)}")

    @Slot()
    def declineResume(self) -> None:
        """Start over: the saved point is replaced by the next checkpoint."""
        self._take_offer()

    @Slot(str, result=bool)
    def openUrl(self, text: str) -> bool:
        """Play a network stream. False, with a notice, if `text` is not a stream address."""
        url = parse_stream_url(text)
        if url is None:
            self.noticed.emit("That doesn't look like a video address (http, https, rtsp…)")
            return False
        self._checkpoint()
        self._playlist.clear()
        self._playlist.add([url])
        self._load(0)
        return True

    # --- A–B loop ----------------------------------------------------------

    @Property(int, notify=loopChanged)
    def loopA(self) -> int:
        return self._loop_a

    @Property(int, notify=loopChanged)
    def loopB(self) -> int:
        return self._loop_b

    @Slot()
    def cycleLoop(self) -> None:
        """First press sets A, the second sets B and starts looping, the third clears."""
        if self._loop_a < 0:
            self.setLoopA()
        elif self._loop_b < 0:
            self.setLoopB()
        else:
            self.clearLoop()

    @Slot()
    def setLoopA(self) -> None:
        if self._playlist.current is None:
            return
        self._loop_a = self._player.position()
        if 0 <= self._loop_b <= self._loop_a + MIN_LOOP_MS:
            self._loop_b = -1
        self.loopChanged.emit()
        self.noticed.emit(f"Loop start (A) at {format_time(self._loop_a / 1000)}")

    @Slot()
    def setLoopB(self) -> None:
        position = self._player.position()
        if self._loop_a < 0 or position < self._loop_a + MIN_LOOP_MS:
            self.noticed.emit("Set the loop end (B) after its start (A)")
            return
        self._loop_b = position
        self._player.setPosition(self._loop_a)
        self.loopChanged.emit()
        a, b = format_time(self._loop_a / 1000), format_time(self._loop_b / 1000)
        self.noticed.emit(f"Looping {a} – {b}")

    @Slot()
    def clearLoop(self) -> None:
        if self._loop_a < 0 and self._loop_b < 0:
            return
        self._loop_a = self._loop_b = -1
        self.loopChanged.emit()
        self.noticed.emit("Loop off")

    # --- frames ------------------------------------------------------------

    @Slot(int)
    def stepFrame(self, frames: int) -> None:
        """Pause and move `frames` frames (negative: back), using the file's frame rate."""
        if not self._player.isSeekable():
            return
        if self.playing:
            self._player.pause()
        rate = self._player.metaData().value(QMediaMetaData.Key.VideoFrameRate)
        try:
            step = frame_ms(float(rate)) if rate is not None else frame_ms(None)
        except (TypeError, ValueError):
            step = frame_ms(None)
        target = self._player.position() + round(frames * step)
        target = min(max(0, target), self._player.duration())
        self._player.setPosition(target)
        self.noticed.emit(f"Frame {format_time(target / 1000)}.{target % 1000:03d}")

    @Slot()
    def screenshot(self) -> None:
        """Save the frame on screen as a PNG in Pictures/Aperture."""
        frame = self._sink.videoFrame() if self._sink is not None else None
        if frame is None or not frame.isValid() or not self._player.hasVideo():
            self.noticed.emit("No picture to capture")
            return
        image = frame.toImage()
        pictures = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.PicturesLocation)
        folder = Path(pictures or Path.home()) / "Aperture"
        try:
            folder.mkdir(parents=True, exist_ok=True)
        except OSError:
            log.warning("cannot create %s", folder, exc_info=True)
            self.noticed.emit("Couldn't save the screenshot")
            return
        target = folder / screenshot_name(self.title, self._player.position(), datetime.now())
        if image.isNull() or not image.save(str(target), "PNG"):
            self.noticed.emit("Couldn't save the screenshot")
            return
        self.noticed.emit(f"Screenshot saved to {folder.name}/{target.name}")

    @Slot()
    def shutdown(self) -> None:
        """Persist the resume point; call before the app quits."""
        self._checkpoint()

    # --- internals ---------------------------------------------------------

    def _report_missing(self, paths: list[Path | str]) -> None:
        missing = [Path(p) for p in paths if not Path(p).exists()]
        if missing:
            more = f" and {len(missing) - 1} more" if len(missing) > 1 else ""
            self.noticed.emit(f"Not found: {missing[0].name}{more}")

    def _take_subtitles(self, paths: list[Path]) -> list[Path]:
        """Route subtitle and .lrc lyrics files to the loaded media; return the rest."""
        subtitles = [p for p in paths if is_subtitle(p) and p.is_file()]
        if subtitles:
            if self._loaded is None:
                self.noticed.emit("Open a video before adding subtitles")
            else:
                self.tracks.add_files(subtitles)
        lyrics = [p for p in paths if p.suffix.lower() == ".lrc" and p.is_file()]
        if lyrics:
            self.lyricsDropped.emit([str(p) for p in lyrics])
        return [p for p in paths if p not in subtitles and p not in lyrics]

    def _load(self, index: int) -> None:
        self._checkpoint()
        path = self._playlist.select(index)
        self._set_error("")
        self._history.touch(path)
        self._loaded = path
        self._take_offer()
        self._last_position = 0
        saved = self._history.resume_point(path)
        self._pending_resume = saved if self.resume_mode == "always" else None
        if saved and self.resume_mode == "ask":
            self._resume_offer = saved
            self._offer_timer.start()
            self.resumeOfferChanged.emit()
        if self._loop_a >= 0 or self._loop_b >= 0:
            self._loop_a = self._loop_b = -1
            self.loopChanged.emit()
        self._player.setSource(QUrl(path) if is_url(path) else QUrl.fromLocalFile(str(path)))
        self._player.setPlaybackRate(self._rate)
        self.tracks.reset(None if is_url(path) else path)
        self._set_chapters([] if is_url(path) else read_chapters(path))
        self.mediaLoaded.emit(str(path))
        self._player.play()
        self._history.save()
        self.playlistChanged.emit()
        self.recentChanged.emit()

    def _unload(self) -> None:
        self._checkpoint()
        self._loaded = None
        self._pending_resume = None
        self._take_offer()
        self._set_chapters([])
        self._player.stop()
        self._player.setSource(QUrl())
        self.tracks.reset(None)
        self.mediaLoaded.emit("")
        self._set_error("")
        self.playlistChanged.emit()

    def _checkpoint(self) -> None:
        """Record the loaded file's position as its resume point."""
        # Before a pending resume lands, or while the user is still deciding, the position
        # is near 0 and would wipe the stored point.
        if self._loaded is None or self._pending_resume is not None or self._resume_offer:
            return
        if self._player.mediaStatus() in _UNLOADED:
            return
        position, duration = self._player.position(), self._player.duration()
        # Closing the window stops the player, which rewinds it; keep where playback was.
        if self._player.playbackState() == QMediaPlayer.PlaybackState.StoppedState:
            position = self._last_position
        self._history.remember_position(self._loaded, position, duration)
        self._history.save()
        self.recentChanged.emit()

    def _take_offer(self) -> int:
        target, self._resume_offer = self._resume_offer, 0
        self._offer_timer.stop()
        if target:
            self.resumeOfferChanged.emit()
        return target

    def _on_position(self, position: int) -> None:
        if self._player.playbackState() != QMediaPlayer.PlaybackState.StoppedState:
            self._last_position = position
        if self._loop_b >= 0 and position >= self._loop_b:
            self._player.setPosition(self._loop_a)
        if self._chapters:
            chapter = chapter_at(self._chapters, position)
            if chapter != self._chapter:
                self._chapter = chapter
                self.chapterChanged.emit()
        self.positionChanged.emit()

    def _set_chapters(self, chapters: list[Chapter]) -> None:
        self._chapters = chapters
        self._chapter = -1
        self.chaptersChanged.emit()
        self.chapterChanged.emit()

    def _on_metadata(self) -> None:
        size = self._player.metaData().value(QMediaMetaData.Key.Resolution)
        try:
            aspect = size.width() / size.height() if size and size.height() > 0 else 0.0
        except AttributeError:
            aspect = 0.0
        if aspect != self._aspect:
            self._aspect = aspect
            self.videoAspectChanged.emit()

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
            # The backend can fall back to 1× when it opens a new file; insist on the chosen speed.
            if self._player.playbackRate() != self._rate:
                self._player.setPlaybackRate(self._rate)
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

    def _on_error(self, error: QMediaPlayer.Error, detail: str) -> None:
        if error == QMediaPlayer.Error.NoError:
            return
        log.warning("playback error for %s: %s (%s)", self._loaded, detail, error)
        name = display_name(self._loaded) if self._loaded is not None else "this file"
        friendly = describe_error(_ERROR_KINDS.get(error, "other"), name)
        self._set_error(friendly.title, friendly.message)

    def _set_error(self, title: str, message: str = "") -> None:
        if (title, message) != (self._error_title, self._error):
            self._error_title, self._error = title, message
            self.errorChanged.emit()
