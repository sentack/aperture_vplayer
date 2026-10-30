"""Audio boost past 100%, by playing the decoded audio ourselves.

QAudioOutput cannot go above full volume. While a boost is on, the player's QAudioOutput is
detached and a QAudioBufferOutput receives the decoded audio instead; each buffer is
amplified with a soft limiter (aperture.core.gain) and written to our own QAudioSink. At
100% the normal path is restored untouched. If this Qt lacks the pieces, boost stays off.
"""

from __future__ import annotations

import logging
from array import array

from PySide6.QtCore import QObject, Signal
from PySide6.QtMultimedia import (
    QAudioFormat,
    QAudioOutput,
    QAudioSink,
    QMediaDevices,
    QMediaPlayer,
)

from aperture.core.gain import MAX_BOOST, boost

log = logging.getLogger(__name__)

_TYPECODES = {
    QAudioFormat.SampleFormat.Int16: "h",
    QAudioFormat.SampleFormat.Int32: "i",
    QAudioFormat.SampleFormat.Float: "f",
}
MAX_BACKLOG_S = 0.5  # drop audio rather than let it drift behind the picture


def _buffer_bytes(buffer) -> bytes:
    for read in (lambda: buffer.constData(), lambda: buffer.data()):
        try:
            data = read()
        except (AttributeError, TypeError):
            continue
        if data is not None:
            return data.tobytes() if hasattr(data, "tobytes") else bytes(data)
    return b""


class AudioBoost(QObject):
    unavailable = Signal(str)

    def __init__(
        self, player: QMediaPlayer, output: QAudioOutput, parent: QObject | None = None
    ) -> None:
        super().__init__(parent)
        self._player = player
        self._output = output
        self._gain = 1.0
        self._capture = None  # QAudioBufferOutput while boosting
        self._sink: QAudioSink | None = None
        self._device = None
        self._format: QAudioFormat | None = None
        self._backlog = bytearray()
        output.volumeChanged.connect(self._sync_volume)
        output.mutedChanged.connect(self._sync_volume)

    @property
    def gain(self) -> float:
        return self._gain

    def set_gain(self, gain: float) -> bool:
        """Apply a boost between 1.0 and MAX_BOOST; False if this system cannot boost."""
        gain = min(MAX_BOOST, max(1.0, gain))
        if gain > 1.0 and self._capture is None and not self._start():
            return False
        self._gain = gain
        if gain == 1.0:
            self._stop()
        return True

    def _start(self) -> bool:
        try:
            from PySide6.QtMultimedia import QAudioBufferOutput
        except ImportError:
            self.unavailable.emit("Audio boost needs a newer Qt (6.8 or later)")
            return False
        self._capture = QAudioBufferOutput(self)
        self._capture.audioBufferReceived.connect(self._on_buffer)
        self._player.setAudioOutput(None)
        self._player.setAudioBufferOutput(self._capture)
        return True

    def _stop(self) -> None:
        if self._capture is None:
            return
        self._player.setAudioBufferOutput(None)
        self._player.setAudioOutput(self._output)
        self._capture.deleteLater()
        self._capture = None
        if self._sink is not None:
            self._sink.stop()
            self._sink.deleteLater()
        self._sink, self._device, self._format = None, None, None
        self._backlog.clear()

    def _open_sink(self, fmt: QAudioFormat) -> bool:
        if self._sink is not None:
            self._sink.stop()
            self._sink.deleteLater()
        self._sink = QAudioSink(QMediaDevices.defaultAudioOutput(), fmt, self)
        self._device = self._sink.start()
        self._format = fmt
        self._backlog.clear()
        self._sync_volume()
        if self._device is None:
            log.warning("audio boost: cannot open the audio device")
            self.unavailable.emit("Audio boost couldn't open the audio device")
            self.set_gain(1.0)
            return False
        return True

    def _on_buffer(self, buffer) -> None:
        fmt = buffer.format()
        typecode = _TYPECODES.get(fmt.sampleFormat())
        if typecode is None:
            return
        if self._format is None or fmt != self._format:
            if not self._open_sink(fmt):
                return
        samples = array(typecode)
        samples.frombytes(_buffer_bytes(buffer))
        self._backlog += boost(samples, self._gain).tobytes()
        limit = int(MAX_BACKLOG_S * fmt.sampleRate() * fmt.bytesPerFrame())
        if len(self._backlog) > limit:
            del self._backlog[: len(self._backlog) - limit]
        written = self._device.write(bytes(self._backlog))
        if written > 0:
            del self._backlog[:written]

    def _sync_volume(self, *_) -> None:
        if self._sink is not None:
            self._sink.setVolume(0.0 if self._output.isMuted() else self._output.volume())
