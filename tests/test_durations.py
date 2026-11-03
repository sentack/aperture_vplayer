"""Playlist item lengths: from tags when mutagen can tell, else from a silent decoder."""

import os
import shutil
import subprocess

import pytest

pytest.importorskip("PySide6.QtMultimedia")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QEventLoop, QTimer  # noqa: E402
from PySide6.QtGui import QGuiApplication  # noqa: E402

needs_ffmpeg = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="needs ffmpeg")


@pytest.fixture(scope="module")
def app():
    return QGuiApplication.instance() or QGuiApplication([])


def clip(tmp_path, name, seconds, codec):
    out = tmp_path / name
    args = ["-f", "lavfi", "-i", f"testsrc=size=64x64:rate=10:duration={seconds}", *codec]
    result = subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *args, str(out)],
        capture_output=True, timeout=120,
    )  # fmt: skip
    if result.returncode != 0:
        pytest.skip(f"this ffmpeg cannot encode {name}")
    return out


def wait(app, until, seconds=20):
    """One QEventLoop.exec(), not a processEvents() loop (see test_instance.spin)."""
    loop = QEventLoop()
    poll = QTimer(interval=50)
    poll.timeout.connect(lambda: until() and loop.quit())
    QTimer.singleShot(seconds * 1000, loop.quit)
    poll.start()
    loop.exec()
    poll.stop()
    return until()


@needs_ffmpeg
def test_lengths_from_tags_and_from_the_decoder(app, tmp_path):
    from aperture.player.durations import DurationProbe, tag_duration

    mp4 = clip(tmp_path, "tagged.mp4", 3, ["-c:v", "libx264", "-pix_fmt", "yuv420p"])
    mkv = clip(tmp_path, "decoded.mkv", 4, ["-c:v", "libx264", "-pix_fmt", "yuv420p"])
    webm = clip(tmp_path, "decoded.webm", 2, ["-c:v", "libvpx", "-b:v", "100k"])
    broken = tmp_path / "broken.mkv"
    broken.write_bytes(b"not a video")
    assert abs(tag_duration(mp4) - 3000) < 150
    assert tag_duration(mkv) is None  # mutagen can't read Matroska: the decoder's job

    probe = DurationProbe()
    probe.request([mp4, mkv, webm, broken, "https://example.com/live.m3u8"])
    assert abs(probe.duration(mp4) - 3000) < 150  # known at once
    assert wait(app, lambda: probe.duration(webm) is not None and str(broken) in probe._known)
    assert abs(probe.duration(mkv) - 4000) < 150 and abs(probe.duration(webm) - 2000) < 150
    assert probe.duration(broken) is None
    assert probe.duration("https://example.com/live.m3u8") is None  # streams are never probed
    probe.stop()
