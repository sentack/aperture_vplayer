"""Audio and subtitle track selection, exposed to QML as `tracks`.

Subtitle choices mix embedded streams, which VideoOutput renders itself, with external
SRT/VTT files, whose current cue QML draws from `subtitleText`.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import Property, QLocale, QObject, Signal, Slot
from PySide6.QtMultimedia import QMediaMetaData, QMediaPlayer

from aperture.core import SUBTITLE_EXTENSIONS, CueTrack, find_sidecars, load_cues, track_label
from aperture.player.urls import to_paths


@dataclass(frozen=True, slots=True)
class _Source:
    label: str
    embedded: int | None = None  # stream index of an embedded track
    path: Path | None = None  # file of an external one


def _meta_label(index: int, meta: QMediaMetaData) -> str:
    title = meta.stringValue(QMediaMetaData.Key.Title) or None
    language = None
    value = meta.value(QMediaMetaData.Key.Language)
    try:
        if value is not None and QLocale.Language(value) != QLocale.Language.AnyLanguage:
            language = QLocale.languageToString(QLocale.Language(value))
    except (TypeError, ValueError):
        pass
    return track_label(index, title, language)


def is_subtitle(path: Path) -> bool:
    return path.suffix.lower() in SUBTITLE_EXTENSIONS


class TrackSelector(QObject):
    subtitlesChanged = Signal()
    subtitleTextChanged = Signal()
    audioChanged = Signal()
    noticed = Signal(str)

    def __init__(self, player: QMediaPlayer, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._player = player
        self._files: list[_Source] = []
        self._embedded: list[_Source] = []
        self._active: _Source | None = None
        self._last: _Source | None = None  # what toggleSubtitles turns back on
        # Turn on the first sidecar subtitle file automatically when a video loads.
        self.auto_select = True
        self._cues: CueTrack | None = None
        self._text = ""

        player.tracksChanged.connect(self._on_tracks)
        player.activeTracksChanged.connect(lambda: self.audioChanged.emit())
        player.positionChanged.connect(self._update_text)

    @property
    def _sources(self) -> list[_Source]:
        return self._files + self._embedded

    # --- subtitles ---------------------------------------------------------

    @Property(list, notify=subtitlesChanged)
    def subtitleOptions(self) -> list[str]:
        return [source.label for source in self._sources]

    @Property(int, notify=subtitlesChanged)
    def subtitleIndex(self) -> int:
        sources = self._sources
        return sources.index(self._active) if self._active in sources else -1

    @Property(str, notify=subtitleTextChanged)
    def subtitleText(self) -> str:
        return self._text

    @Slot(int)
    def selectSubtitle(self, index: int) -> None:
        sources = self._sources
        self._activate(sources[index] if 0 <= index < len(sources) else None)

    @Slot()
    def toggleSubtitles(self) -> None:
        if self._active is not None:
            self._last = self._active
            self._activate(None)
            self.noticed.emit("Subtitles off")
            return
        sources = self._sources
        target = self._last if self._last in sources else next(iter(sources), None)
        if target is None:
            self.noticed.emit("No subtitles")
        elif self._activate(target):
            self.noticed.emit(f"Subtitles: {target.label}")

    @Slot(list)
    def addSubtitleUrls(self, urls: list) -> None:
        self.add_files(p for p in to_paths(urls) if is_subtitle(p))

    def add_files(self, paths: Iterable[Path]) -> None:
        """Offer external subtitle files for the loaded video and switch to the last one."""
        added = None
        for path in paths:
            added = _Source(path.name, path=path)
            if added not in self._files:
                self._files.append(added)
        if added is not None and self._activate(added):
            self.noticed.emit(f"Subtitles: {added.label}")

    def reset(self, video: Path | None) -> None:
        """Forget the previous file's tracks; pick up sidecar subtitles for `video`."""
        self._files = [_Source(p.name, path=p) for p in find_sidecars(video)] if video else []
        self._embedded = []
        self._last = None
        self._activate(self._files[0] if self._files and self.auto_select else None)
        self.audioChanged.emit()

    # --- audio -------------------------------------------------------------

    @Property(list, notify=audioChanged)
    def audioOptions(self) -> list[str]:
        return [_meta_label(i, meta) for i, meta in enumerate(self._player.audioTracks())]

    @Property(int, notify=audioChanged)
    def audioIndex(self) -> int:
        return self._player.activeAudioTrack()

    @Slot(int)
    def selectAudio(self, index: int) -> None:
        if 0 <= index < len(self._player.audioTracks()):
            self._player.setActiveAudioTrack(index)

    @Slot()
    def cycleAudio(self) -> None:
        options = self.audioOptions
        if len(options) < 2:
            self.noticed.emit("Only one audio track")
            return
        index = (self._player.activeAudioTrack() + 1) % len(options)
        self._player.setActiveAudioTrack(index)
        self.noticed.emit(f"Audio: {options[index]}")

    # --- internals ---------------------------------------------------------

    def _activate(self, source: _Source | None) -> bool:
        cues = None
        if source is not None and source.path is not None:
            try:
                cues = CueTrack(load_cues(source.path))
            except OSError:
                self.noticed.emit(f"Can't read {source.label}")
                return False
            if not len(cues):
                self.noticed.emit(f"No subtitles found in {source.label}")
                return False
        self._cues = cues
        self._active = source
        embedded = source.embedded if source is not None and source.embedded is not None else -1
        self._player.setActiveSubtitleTrack(embedded)
        self._update_text(self._player.position())
        self.subtitlesChanged.emit()
        return True

    def _on_tracks(self) -> None:
        self._embedded = [
            _Source(_meta_label(i, meta), embedded=i)
            for i, meta in enumerate(self._player.subtitleTracks())
        ]
        if self._active not in self._sources:
            self._active = None
        # The backend may enable a default stream on its own; keep the user's choice instead.
        active = self._active
        self._player.setActiveSubtitleTrack(
            active.embedded if active is not None and active.embedded is not None else -1
        )
        self.subtitlesChanged.emit()
        self.audioChanged.emit()

    def _update_text(self, position_ms: int) -> None:
        text = self._cues.text_at(position_ms) if self._cues is not None else ""
        if text != self._text:
            self._text = text
            self.subtitleTextChanged.emit()
