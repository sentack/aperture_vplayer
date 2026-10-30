"""Temporary diagnostic: which step of the audio-boost path crashes Qt on macOS?

Run one case per process (a segfault ends the process), e.g.
    python .github/scripts/probe_boost_crash.py raw-detach-audio
Each case builds a media player, does one thing to its outputs, then destroys it the way the
app does on quit. Prints "<case>: survived" if Qt got through it.
"""

import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from PySide6.QtCore import QCoreApplication, QEvent, QObject  # noqa: E402
from PySide6.QtGui import QGuiApplication  # noqa: E402
from PySide6.QtMultimedia import QAudioBufferOutput, QAudioOutput, QMediaPlayer  # noqa: E402

CASES = {
    "raw-plain": "player + audio output, nothing else",
    "raw-detach-audio": "setAudioOutput(None), then the same output again",
    "raw-buffer": "attach then detach a QAudioBufferOutput, audio output untouched",
    "raw-both": "exactly what boost does: swap audio output for buffer output and back",
    "raw-both-player-first": "same as raw-both, but the player is created before its output",
    "raw-both-capture-first": "the fix: capture created first, so destroyed before the player",
    "controller-plain": "the app's PlayerController, no boost",
    "controller-boost": "the app's PlayerController, boost 150% then back to 100%",
}


def flush(app):
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    app.processEvents()


def main(case: str) -> None:
    app = QGuiApplication([])
    owner = QObject()
    if case.startswith("raw"):
        early = QAudioBufferOutput(owner) if case == "raw-both-capture-first" else None
        if case == "raw-both-player-first":
            player = QMediaPlayer(owner)
            audio = QAudioOutput(owner)
        else:
            audio = QAudioOutput(owner)
            player = QMediaPlayer(owner)
        player.setAudioOutput(audio)
        capture = early or QAudioBufferOutput(owner)
        if case == "raw-detach-audio":
            player.setAudioOutput(None)
            player.setAudioOutput(audio)
        elif case == "raw-buffer":
            player.setAudioBufferOutput(capture)
            player.setAudioBufferOutput(None)
        elif case in ("raw-both", "raw-both-player-first", "raw-both-capture-first"):
            player.setAudioOutput(None)
            player.setAudioBufferOutput(capture)
            app.processEvents()
            player.setAudioBufferOutput(None)
            player.setAudioOutput(audio)
    else:
        from aperture.player import PlayerController

        controller = PlayerController(parent=owner)
        if case == "controller-boost":
            controller.setProperty("audioBoost", 1.5)
            app.processEvents()
            controller.setProperty("audioBoost", 1.0)
    app.processEvents()
    owner.deleteLater()
    flush(app)
    print(f"{case}: survived", flush=True)


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in CASES:
        sys.exit("cases: " + ", ".join(CASES))
    main(sys.argv[1])
