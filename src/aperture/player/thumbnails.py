"""Seek-bar preview frames, decoded by a second, silent QMediaPlayer.

Hover positions snap to a grid (`thumbnail_bucket`), only the newest request is decoded,
and finished frames are cached per bucket. QML shows them through the `thumbs` image
provider, using the URL in `ThumbnailService.source`.
"""

from __future__ import annotations

from collections import OrderedDict
from pathlib import Path

from PySide6.QtCore import Property, QObject, Qt, QTimer, QUrl, Signal, Slot
from PySide6.QtGui import QImage
from PySide6.QtMultimedia import QMediaPlayer, QVideoFrame, QVideoSink
from PySide6.QtQml import QQmlImageProviderBase
from PySide6.QtQuick import QQuickImageProvider

from aperture.core import thumbnail_bucket

PROVIDER_ID = "thumbs"
THUMB_WIDTH = 192
CACHE_LIMIT = 150
# Give up on a seek that never yields a frame (broken stream, audio-only file).
FRAME_TIMEOUT_MS = 1500


class ThumbnailImages(QQuickImageProvider):
    def __init__(self) -> None:
        super().__init__(QQmlImageProviderBase.ImageType.Image)
        self._images: dict[str, QImage] = {}

    def put(self, key: str, image: QImage) -> None:
        self._images[key] = image

    def discard(self, key: str) -> None:
        self._images.pop(key, None)

    def clear(self) -> None:
        self._images.clear()

    def requestImage(self, id: str, size, requestedSize) -> QImage:  # noqa: A002, N803 (Qt API)
        return self._images.get(id, QImage())


class ThumbnailService(QObject):
    sourceChanged = Signal()

    def __init__(self, images: ThumbnailImages, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._images = images
        self._file: Path | None = None
        self._ready = False  # decoder has the file loaded and can seek
        self._generation = 0  # keeps image ids unique across files
        self._wanted: int | None = None  # bucket under the pointer
        self._in_flight: int | None = None  # bucket being decoded
        self._cache: OrderedDict[int, str] = OrderedDict()  # bucket -> image id
        self._source = ""

        self._sink = QVideoSink(self)
        self._decoder = QMediaPlayer(self)  # no audio output: silent by construction
        self._decoder.setVideoSink(self._sink)
        self._sink.videoFrameChanged.connect(self._on_frame)
        self._decoder.mediaStatusChanged.connect(self._on_status)

        self._timeout = QTimer(self)
        self._timeout.setSingleShot(True)
        self._timeout.setInterval(FRAME_TIMEOUT_MS)
        self._timeout.timeout.connect(self._on_timeout)

    @Property(str, notify=sourceChanged)
    def source(self) -> str:
        """`image://thumbs/<id>` for the hovered bucket's frame, or "" while none is ready."""
        return self._source

    @Slot(str)
    def setFile(self, path: str) -> None:
        """Follow the main player's file. Decoding starts lazily on the first hover."""
        self._generation += 1
        self._file = Path(path) if path else None
        self._ready = False
        self._wanted = self._in_flight = None
        self._timeout.stop()
        self._cache.clear()
        self._images.clear()
        self._decoder.stop()
        self._decoder.setSource(QUrl())
        self._set_source("")

    @Slot(int, int)
    def request(self, position_ms: int, duration_ms: int) -> None:
        if self._file is None:
            return
        bucket = thumbnail_bucket(position_ms, duration_ms)
        self._wanted = bucket
        if bucket in self._cache:
            self._cache.move_to_end(bucket)
            self._set_source(self._url(self._cache[bucket]))
            return
        if self._decoder.source().isEmpty():
            self._decoder.setSource(QUrl.fromLocalFile(str(self._file)))
            self._decoder.pause()  # loads the file without playing it
            return
        self._pump()

    def _pump(self) -> None:
        if not self._ready or self._in_flight is not None or self._wanted is None:
            return
        if self._wanted in self._cache:
            return
        self._in_flight = self._wanted
        self._decoder.setPosition(self._in_flight)
        self._timeout.start()

    def _on_status(self, status: QMediaPlayer.MediaStatus) -> None:
        if status in (QMediaPlayer.MediaStatus.LoadedMedia, QMediaPlayer.MediaStatus.BufferedMedia):
            if not self._ready:
                if not self._decoder.hasVideo():
                    self._file = None
                    return
                self._ready = True
                self._pump()
        elif status == QMediaPlayer.MediaStatus.InvalidMedia:
            self._file = None

    def _on_frame(self, frame: QVideoFrame) -> None:
        bucket = self._in_flight
        if bucket is None or not frame.isValid():
            return  # e.g. the first frame shown when the file loads
        self._in_flight = None
        self._timeout.stop()
        image = frame.toImage()
        if not image.isNull():
            self._store(bucket, image.scaledToWidth(THUMB_WIDTH, Qt.SmoothTransformation))
        self._pump()

    def _on_timeout(self) -> None:
        self._in_flight = None
        self._pump()

    def _store(self, bucket: int, image: QImage) -> None:
        key = f"{self._generation}-{bucket}"
        self._images.put(key, image)
        self._cache[bucket] = key
        while len(self._cache) > CACHE_LIMIT:
            _, old = self._cache.popitem(last=False)
            self._images.discard(old)
        if bucket == self._wanted:
            self._set_source(self._url(key))

    @staticmethod
    def _url(key: str) -> str:
        return f"image://{PROVIDER_ID}/{key}"

    def _set_source(self, source: str) -> None:
        if source != self._source:
            self._source = source
            self.sourceChanged.emit()
