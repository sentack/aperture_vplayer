"""Online lyrics and subtitle search for the playing file, exposed to QML as `online`.

Lyrics come from LRCLIB (free, no account) and are embedded into the audio file. Subtitles
come from OpenSubtitles, which needs the user's own API key; the chosen file is saved next
to the video as `<name>.<language>.srt` and loaded at once. Every failure ends in a message
in the dialog, never an exception: these are services that can be slow, limited or down.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from pathlib import Path
from urllib.parse import quote, urlencode

from PySide6.QtCore import Property, QLocale, QObject, QUrl, Signal, Slot
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest

from aperture import __version__
from aperture.core import is_audio, is_video, parse_lyrics
from aperture.core.media import is_url
from aperture.core.online import (
    LRCLIB_SEARCH,
    OPENSUBTITLES_API,
    PROJECT_URL,
    LyricsResult,
    SubtitleResult,
    describe_failure,
    guess_title_year,
    lrclib_query,
    opensubtitles_query,
    parse_download_link,
    parse_lrclib,
    parse_subtitle_search,
    subtitle_path,
)
from aperture.core.timefmt import format_time
from aperture.settings import Settings

log = logging.getLogger(__name__)

TIMEOUT_MS = 20_000
MAX_SUBTITLE_BYTES = 5 * 1024 * 1024
LYRICS, SUBTITLES = "lyrics", "subtitles"

# (HTTP status or None when the server never answered, body, whether the transfer failed)
Done = Callable[[int | None, bytes, bool], None]


class OnlineSearch(QObject):
    changed = Signal()
    # A result was saved and loaded: the dialog closes.
    chosen = Signal()
    noticed = Signal(str)

    def __init__(
        self,
        player: QObject,
        lyrics: QObject,
        tracks: QObject,
        settings: Settings,
        data_dir: Path,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._player = player  # PlayerController: mediaLoaded, duration
        self._lyrics = lyrics  # LyricsController: store()
        self._tracks = tracks  # TrackSelector: add_files()
        self._settings = settings
        self._data_dir = data_dir
        self._network = QNetworkAccessManager(self)
        self._reply: QNetworkReply | None = None
        self._media: Path | None = None
        self._kind = ""
        self._busy = False
        self._status = ""
        self._lyrics_results: list[LyricsResult] = []
        self._subtitle_results: list[SubtitleResult] = []
        self._language = ""
        player.mediaLoaded.connect(self._on_media)

    # --- state -------------------------------------------------------------

    @Property(bool, notify=changed)
    def canSearchLyrics(self) -> bool:
        return self._media is not None and is_audio(self._media)

    @Property(bool, notify=changed)
    def canSearchSubtitles(self) -> bool:
        return self._media is not None and is_video(self._media)

    @Property(str, notify=changed)
    def kind(self) -> str:
        """What the dialog searches for: "lyrics" or "subtitles"."""
        return self._kind

    @Property(bool, notify=changed)
    def busy(self) -> bool:
        return self._busy

    @Property(str, notify=changed)
    def status(self) -> str:
        return self._status

    @Property(bool, notify=changed)
    def needsKey(self) -> bool:
        return self._kind == SUBTITLES and not self._settings.opensubtitles_key

    @Property("QVariantMap", notify=changed)
    def fields(self) -> dict[str, str]:
        """The search form's starting values, guessed from the file: always editable."""
        if self._media is None:
            return {}
        if self._kind == LYRICS:
            from aperture.core.lyrics_tags import song_fields

            return song_fields(self._media)
        title, year = guess_title_year(self._media.name)
        return {"title": title, "year": year, "language": _system_language()}

    @Property(list, notify=changed)
    def results(self) -> list[dict[str, str]]:
        if self._kind == LYRICS:
            return [
                {
                    "title": r.track or "Untitled",
                    "detail": " · ".join(
                        part
                        for part in (
                            r.artist,
                            r.album,
                            format_time(r.duration_s) if r.duration_s > 0 else "",
                        )
                        if part
                    ),
                    "badge": "Synced" if r.synced else "Plain",
                }
                for r in self._lyrics_results
            ]
        return [
            {
                "title": r.release,
                "detail": " · ".join(
                    part
                    for part in (
                        r.language.upper(),
                        f"{r.downloads:,} downloads",
                        "Hearing impaired" if r.hearing_impaired else "",
                    )
                    if part
                ),
                "badge": "",
            }
            for r in self._subtitle_results
        ]

    # --- commands ----------------------------------------------------------

    @Slot(str)
    def begin(self, kind: str) -> None:
        """Open the search for `kind` on the playing file, from a clean slate."""
        self.cancel()
        self._kind = kind if kind in (LYRICS, SUBTITLES) else ""
        self._lyrics_results, self._subtitle_results = [], []
        self._status = ""
        self.changed.emit()

    @Slot(str, str, str)
    def searchLyrics(self, title: str, artist: str, album: str) -> None:
        if not title.strip():
            self._set_status("Enter the song's title to search.")
            return
        url = _url(LRCLIB_SEARCH, lrclib_query(title, artist, album))
        self._start("Searching LRCLIB…")
        self._send("GET", url, self._lrclib_headers(), None, self._on_lyrics)

    @Slot(str, str, str)
    def searchSubtitles(self, title: str, year: str, language: str) -> None:
        if not self._settings.opensubtitles_key:
            self._set_status(
                "Subtitle search needs an OpenSubtitles API key. Add yours in Settings → Subtitles."
            )
            return
        if not title.strip():
            self._set_status("Enter the film or show's title to search.")
            return
        self._language = language.split(",")[0].strip().lower()
        url = _url(f"{OPENSUBTITLES_API}/subtitles", opensubtitles_query(title, year, language))
        self._start("Searching OpenSubtitles…")
        self._send("GET", url, self._opensubtitles_headers(), None, self._on_subtitles)

    @Slot(int)
    def choose(self, index: int) -> None:
        if self._busy or self._media is None:
            return
        if self._kind == LYRICS and 0 <= index < len(self._lyrics_results):
            self._use_lyrics(self._lyrics_results[index])
        elif self._kind == SUBTITLES and 0 <= index < len(self._subtitle_results):
            self._download_subtitle(self._subtitle_results[index])

    @Slot()
    def cancel(self) -> None:
        if self._reply is not None:
            reply, self._reply = self._reply, None
            reply.abort()
        if self._busy:
            self._busy = False
            self._status = ""
            self.changed.emit()

    # --- lyrics ------------------------------------------------------------

    def _on_lyrics(self, status: int | None, data: bytes, failed: bool) -> None:
        parsed = _json(data) if status == 200 else None
        if parsed is None:
            self._finish(describe_failure("LRCLIB", status, failed))
            return
        duration_s = self._player.property("duration") / 1000
        self._lyrics_results = parse_lrclib(parsed, duration_s)
        self._finish(
            _found(len(self._lyrics_results))
            if self._lyrics_results
            else "No lyrics found. Try fewer words, or check the spelling."
        )

    def _use_lyrics(self, result: LyricsResult) -> None:
        lines = parse_lyrics(result.text)
        if lines and self._lyrics.store(lines, origin="from LRCLIB"):
            self.chosen.emit()

    # --- subtitles ---------------------------------------------------------

    def _on_subtitles(self, status: int | None, data: bytes, failed: bool) -> None:
        parsed = _json(data) if status == 200 else None
        if parsed is None:
            self._finish(describe_failure("OpenSubtitles", status, failed))
            return
        self._subtitle_results = parse_subtitle_search(parsed)
        self._finish(
            _found(len(self._subtitle_results))
            if self._subtitle_results
            else "No subtitles found. Try the title alone, or another language."
        )

    def _download_subtitle(self, result: SubtitleResult) -> None:
        video, language = self._media, result.language or self._language
        url = QUrl(f"{OPENSUBTITLES_API}/download")
        body = json.dumps({"file_id": result.file_id}).encode()
        headers = dict(self._opensubtitles_headers(), **{"Content-Type": "application/json"})

        def on_link(status: int | None, data: bytes, failed: bool) -> None:
            link = parse_download_link(_json(data)) if status == 200 else None
            if link is None:
                self._finish(describe_failure("OpenSubtitles", status, failed))
                return
            self._send("GET", QUrl(link), {"User-Agent": _agent()}, None, on_file)

        def on_file(status: int | None, data: bytes, failed: bool) -> None:
            if status != 200 or not data or len(data) > MAX_SUBTITLE_BYTES:
                self._finish(describe_failure("OpenSubtitles", status, failed))
                return
            if video != self._media:  # another file started meanwhile: it isn't for this one
                self._finish("")
                return
            saved = self._save_subtitle(video, language, data)
            if saved is None:
                self._finish("Couldn't save the subtitle file.")
                return
            self._finish("")
            self._tracks.add_files([saved])
            self.chosen.emit()

        self._start("Downloading…")
        self._send("POST", url, headers, body, on_link)

    def _save_subtitle(self, video: Path, language: str, data: bytes) -> Path | None:
        """Next to the video; in Aperture's own folder when that one is read-only."""
        for folder in (video.parent, self._data_dir / "subtitles"):
            try:
                folder.mkdir(parents=True, exist_ok=True)
                path = subtitle_path(folder / video.name, language)
                path.write_bytes(data)
                return path
            except OSError:
                log.warning("cannot save subtitles in %s", folder, exc_info=True)
        return None

    # --- network -----------------------------------------------------------

    def _send(self, method: str, url: QUrl, headers: dict, body: bytes | None, done: Done) -> None:
        request = QNetworkRequest(url)
        for name, value in headers.items():
            request.setRawHeader(name.encode(), value.encode())
        request.setTransferTimeout(TIMEOUT_MS)
        if method == "POST":
            reply = self._network.post(request, body)
        else:
            reply = self._network.get(request)
        self._reply = reply
        reply.finished.connect(lambda: self._finished(reply, done))

    def _finished(self, reply: QNetworkReply, done: Done) -> None:
        reply.deleteLater()
        if reply is not self._reply:  # cancelled, or replaced by a newer request
            return
        self._reply = None
        status = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        failed = reply.error() != QNetworkReply.NetworkError.NoError
        if failed:
            log.info("%s: %s", reply.url().host(), reply.errorString())
        done(status if isinstance(status, int) else None, bytes(reply.readAll().data()), failed)

    def _lrclib_headers(self) -> dict[str, str]:
        return {"User-Agent": f"Aperture {__version__} ({PROJECT_URL})"}

    def _opensubtitles_headers(self) -> dict[str, str]:
        return {
            "Api-Key": self._settings.opensubtitles_key,
            "User-Agent": _agent(),
            "Accept": "application/json",
        }

    # --- helpers -----------------------------------------------------------

    def _on_media(self, path: str) -> None:
        self._media = Path(path) if path and not is_url(path) else None
        self.changed.emit()

    def _start(self, message: str) -> None:
        self.cancel()
        self._busy = True
        self._status = message
        self.changed.emit()

    def _finish(self, message: str) -> None:
        self._busy = False
        self._status = message
        self.changed.emit()

    def _set_status(self, message: str) -> None:
        self._status = message
        self.changed.emit()


def _agent() -> str:
    return f"Aperture v{__version__}"  # OpenSubtitles asks for "AppName vX.Y.Z"


def _url(base: str, query: dict[str, str]) -> QUrl:
    """`base?query`, every value percent-encoded (titles can hold &, + and =)."""
    return QUrl(f"{base}?{urlencode(query, quote_via=quote)}", QUrl.ParsingMode.StrictMode)


def _json(data: bytes) -> object:
    try:
        return json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return None


def _found(count: int) -> str:
    return f"{count} result{'s' if count != 1 else ''}. Pick one to use it."


def _system_language() -> str:
    code = QLocale.system().name().split("_")[0].lower()
    return code if len(code) == 2 and code.isalpha() else "en"
