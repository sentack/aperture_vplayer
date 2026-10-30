"""Decode a real frame from each codec Aperture claims to play, using Qt's own FFmpeg.

Samples are encoded on the fly with the `ffmpeg` command-line tool (installed in CI), so
the check runs against files, not assumptions. Skipped when PySide6 or ffmpeg is missing.
"""

import os
import shutil
import subprocess

import pytest

pytest.importorskip("PySide6.QtMultimedia")
if shutil.which("ffmpeg") is None:
    pytest.skip("needs the ffmpeg command-line tool to make samples", allow_module_level=True)

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QEventLoop, QTimer, QUrl  # noqa: E402
from PySide6.QtGui import QGuiApplication  # noqa: E402
from PySide6.QtMultimedia import QMediaPlayer, QVideoSink  # noqa: E402

VIDEO = ["-f", "lavfi", "-i", "testsrc=size=160x90:rate=24:duration=1"]
AUDIO = ["-f", "lavfi", "-i", "sine=frequency=440:duration=1"]

AV1_NOTE = (
    "Qt's prebuilt FFmpeg has no software AV1 decoder (no dav1d), so AV1 plays only where "
    "the graphics hardware decodes it"
)

SAMPLES = [
    pytest.param("h264.mp4", VIDEO + ["-c:v", "libx264", "-pix_fmt", "yuv420p"], id="H.264"),
    pytest.param(
        "hevc.mp4",
        VIDEO + ["-c:v", "libx265", "-tag:v", "hvc1", "-x265-params", "log-level=error"],
        id="HEVC",
    ),
    pytest.param("vp8.webm", VIDEO + ["-c:v", "libvpx", "-b:v", "200k"], id="VP8"),
    pytest.param(
        "vp9.webm",
        VIDEO + AUDIO + ["-c:v", "libvpx-vp9", "-b:v", "200k", "-c:a", "libopus"],
        id="VP9+Opus",
    ),
    pytest.param(
        "av1.mkv",
        VIDEO + ["-c:v", "libaom-av1", "-cpu-used", "8", "-crf", "50", "-b:v", "0"],
        id="AV1",
        marks=pytest.mark.xfail(reason=AV1_NOTE, strict=False),
    ),
]


@pytest.fixture(scope="module")
def app():
    return QGuiApplication.instance() or QGuiApplication([])


def encode(tmp_path, name, args):
    out = tmp_path / name
    result = subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *args, str(out)],
        capture_output=True, text=True, timeout=120,
    )  # fmt: skip
    if result.returncode != 0:
        pytest.skip(f"this ffmpeg cannot encode {name}: {result.stderr.strip()[:200]}")
    return out


def first_frame(path, timeout_ms=10_000):
    """True once Qt decodes a valid video frame from `path`; also returns the player error."""
    player, sink = QMediaPlayer(), QVideoSink()
    player.setVideoSink(sink)
    loop, got = QEventLoop(), {"frame": False}

    def on_frame(frame):
        if frame.isValid():
            got["frame"] = True
            loop.quit()

    sink.videoFrameChanged.connect(on_frame)
    player.errorOccurred.connect(lambda *_: loop.quit())
    QTimer.singleShot(timeout_ms, loop.quit)
    player.setSource(QUrl.fromLocalFile(str(path)))
    player.play()
    loop.exec()
    player.stop()
    return got["frame"], player.errorString()


@pytest.mark.parametrize(("name", "args"), SAMPLES)
def test_codec_decodes(app, tmp_path, name, args):
    sample = encode(tmp_path, name, args)
    decoded, error = first_frame(sample)
    assert decoded, f"no frame from {name}: {error or 'timed out'}"
