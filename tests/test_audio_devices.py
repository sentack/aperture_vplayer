"""Sound follows the system's default output when it changes, without a restart."""

import os

import pytest

pytest.importorskip("PySide6.QtMultimedia")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QGuiApplication  # noqa: E402
from PySide6.QtMultimedia import QAudioDevice, QMediaDevices  # noqa: E402


@pytest.fixture(scope="module")
def app():
    return QGuiApplication.instance() or QGuiApplication([])


@pytest.fixture
def player(app):
    from aperture.player.controller import PlayerController

    controller = PlayerController()
    yield controller
    controller.shutdown()


def test_output_moves_to_the_new_default(player, monkeypatch):
    outputs = QMediaDevices.audioOutputs()
    if len(outputs) < 2:
        pytest.skip("needs two audio outputs")
    old, new = outputs[0], outputs[1]
    player._audio.setDevice(old)
    monkeypatch.setattr(QMediaDevices, "defaultAudioOutput", staticmethod(lambda: new))
    player._devices.audioOutputsChanged.emit()  # what Qt sends when the default changes
    assert player._audio.device() == new


def test_no_output_left_keeps_the_last_one(player, monkeypatch):
    before = player._audio.device()
    monkeypatch.setattr(QMediaDevices, "defaultAudioOutput", staticmethod(QAudioDevice))
    player._devices.audioOutputsChanged.emit()
    assert player._audio.device() == before


def test_boosted_sound_reopens_on_the_new_device(player):
    from PySide6.QtMultimedia import QAudioFormat

    boost = player.boost
    boost._format = QAudioFormat()  # as if a sink were open on the old device
    boost._backlog += b"\0" * 64
    player._audio.deviceChanged.emit()
    # The next buffer opens a sink on the output's new device.
    assert boost._format is None and boost._sink is None and not boost._backlog
