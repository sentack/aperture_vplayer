"""Audio boost on a real, playing file: turning it on mid-playback must keep the sound."""

import os
import shutil
import subprocess

import pytest

pytest.importorskip("PySide6.QtMultimedia")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QGuiApplication  # noqa: E402
from test_durations import wait  # noqa: E402


@pytest.fixture(scope="module")
def app():
    return QGuiApplication.instance() or QGuiApplication([])


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="needs ffmpeg")
def test_boost_turned_on_while_playing_still_gets_the_audio(app, tmp_path):
    from aperture.player.controller import PlayerController

    tone = tmp_path / "tone.flac"
    subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
         "-f", "lavfi", "-i", "sine=frequency=440:duration=8", str(tone)],
        check=True, timeout=60,
    )  # fmt: skip
    player = PlayerController()
    if player.boost._capture is None:
        pytest.skip("audio boost needs Qt 6.8 or later")
    try:
        player.open_paths([tone])
        if not wait(app, lambda: player.position > 300, seconds=10):
            pytest.skip("this machine cannot play audio")
        buffers = []
        unavailable = []
        player.boost._capture.audioBufferReceived.connect(buffers.append)
        player.boost.unavailable.connect(unavailable.append)
        player.audioBoost = 1.5
        # The decoded audio must reach the boost. Detaching the normal output before
        # attaching the boost's left the player with no audio at all: silence.
        assert wait(app, lambda: len(buffers) >= 5 or unavailable, seconds=5)
        assert buffers
        if unavailable:
            # No sound device (CI): boost gives up on the first buffer and normal playback
            # carries on, as it should.
            assert player.audioBoost == 1.0
        else:
            assert player.audioBoost == 1.5
            player.audioBoost = 1.0
            assert player.audioBoost == 1.0
    finally:
        player.shutdown()
