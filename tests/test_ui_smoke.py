"""Load the real QML against the real controllers, offscreen.

Catches what unit tests cannot: QML syntax errors, missing types, bad bindings.
Skipped when PySide6 is not installed.
"""

import os

import pytest

pytest.importorskip("PySide6.QtQuick")

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture(scope="module")
def app():
    from PySide6.QtGui import QGuiApplication

    return QGuiApplication.instance() or QGuiApplication([])


@pytest.fixture
def ui(app, tmp_path):
    from aperture.app import load_ui

    warnings = []
    engine, player = load_ui(app, tmp_path, on_warnings=lambda errors: warnings.extend(errors))
    app.processEvents()
    yield engine, player, warnings
    for window in engine.rootObjects():
        window.close()
    app.processEvents()
    del engine


def messages(warnings):
    return [w.toString() for w in warnings]


def test_main_window_loads_cleanly(ui):
    engine, _, warnings = ui
    assert engine.rootObjects()
    assert messages(warnings) == []


def test_theme_switch_rebinds_cleanly(ui, app):
    engine, _, warnings = ui
    appearance = engine.rootContext().contextProperty("appearance")
    for mode in ("light", "dark", "system"):
        appearance.setProperty("mode", mode)
        app.processEvents()
    appearance.setProperty("accent", "coral")
    app.processEvents()
    assert messages(warnings) == []


def test_settings_panel_opens_and_resets_cleanly(ui, app):
    engine, player, warnings = ui
    window = engine.rootObjects()[0]
    prefs = engine.rootContext().contextProperty("prefs")
    window.setProperty("settingsOpen", True)
    app.processEvents()
    prefs.setProperty("defaultRate", "last")
    prefs.setProperty("subtitleSize", "xlarge")
    prefs.setProperty("defaultVolume", 0.5)
    app.processEvents()
    assert prefs.property("subtitleScale") == 1.5
    prefs.reset()
    app.processEvents()
    assert prefs.property("defaultRate") == "1"
    window.setProperty("settingsOpen", False)
    app.processEvents()
    assert messages(warnings) == []


def test_speed_picked_in_settings_applies_now(ui, app):
    engine, player, warnings = ui
    prefs = engine.rootContext().contextProperty("prefs")
    prefs.setProperty("defaultRate", "1.5")
    app.processEvents()
    assert player.property("rate") == 1.5
    player.setProperty("rate", 0.75)
    assert player.property("rate") == 0.75
    assert messages(warnings) == []


def test_resume_prompt_idle_without_offer(ui, app):
    engine, player, warnings = ui
    assert player.property("resumeOffer") == 0
    player.declineResume()
    player.acceptResume()
    app.processEvents()
    assert messages(warnings) == []


def test_lyrics_save_and_embed(ui, app, tmp_path):
    from aperture.core.lyrics_tags import read_embedded

    engine, player, warnings = ui
    lyrics = engine.rootContext().contextProperty("lyrics")
    song = tmp_path / "Song.mp3"
    song.write_bytes(bytes(512))
    player.mediaLoaded.emit(str(song))  # what a real load announces
    app.processEvents()
    assert lyrics.property("audioFile") and not lyrics.property("available")

    lyrics.save([{"time": 1000, "text": "first"}, {"time": 3000, "text": "second"}], True)
    app.processEvents()
    assert (tmp_path / "Song.lrc").read_text(encoding="utf-8").startswith("[00:01.00]first")
    assert read_embedded(song).startswith("[00:01.00]first")
    assert lyrics.property("synced") and lyrics.property("plainText") == "first\nsecond"

    player.mediaLoaded.emit("")
    app.processEvents()
    assert not lyrics.property("audioFile")
    assert messages(warnings) == []
