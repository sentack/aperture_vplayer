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


def _flush_deletes(app) -> None:
    from PySide6.QtCore import QCoreApplication, QEvent

    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    app.processEvents()


@pytest.fixture
def ui(app, tmp_path):
    from aperture.app import load_ui

    warnings = []
    engine, player = load_ui(app, tmp_path, on_warnings=lambda errors: warnings.extend(errors))
    app.processEvents()
    yield engine, player, warnings
    for window in engine.rootObjects():
        window.close()
    # load_ui parents its controllers (players, decoders) to the app. Destroy each test's set
    # now, while Qt is fully running: left to interpreter exit, macOS crashes tearing down
    # dozens of media players at once. The QML goes first, so no binding sees a deleted object.
    # Only Aperture's own controllers go: the app also owns Qt internals (input devices, popup
    # helpers) that Qt creates on demand and must not be deleted.
    engine.deleteLater()
    _flush_deletes(app)
    for child in app.children():
        if type(child).__module__.startswith("aperture."):
            child.deleteLater()
    _flush_deletes(app)


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


def test_default_player_prompt_wires_cleanly(ui, app):
    engine, _, warnings = ui
    defaults = engine.rootContext().contextProperty("defaults")
    assert defaults.property("status") in ("default", "other", "unknown")
    defaults.dismiss()
    app.processEvents()
    assert not defaults.property("promptVisible")
    assert messages(warnings) == []


def test_phase_8_player_commands_without_media(ui, app):
    engine, player, warnings = ui
    notices = []
    player.noticed.connect(notices.append)
    assert player.openUrl("not a url") is False
    player.cycleLoop()  # nothing loaded: no loop
    assert player.property("loopA") == -1 and player.property("loopB") == -1
    player.stepFrame(1)
    player.screenshot()
    app.processEvents()
    assert "No picture to capture" in notices
    assert messages(warnings) == []


def test_rebinding_shortcuts_through_keymap(ui, app):
    from PySide6.QtCore import Qt

    engine, _, warnings = ui
    keymap = engine.rootContext().contextProperty("keymap")
    ctrl = Qt.KeyboardModifier.ControlModifier.value
    assert keymap.sequenceFor(Qt.Key.Key_U.value, ctrl) == "Ctrl+U"
    assert keymap.sequenceFor(Qt.Key.Key_Shift.value, 0) == ""
    assert "already used for Open URL" in keymap.bind("mute", "Ctrl+U")
    keymap.unbind("open_url")
    assert keymap.bind("mute", "Ctrl+U") == ""
    assert keymap.keys.value("mute") == "Ctrl+U"
    keymap.resetShortcuts()
    assert keymap.keys.value("mute") == "M"
    window = engine.rootObjects()[0]
    window.setProperty("settingsOpen", True)
    app.processEvents()
    window.setProperty("settingsOpen", False)
    app.processEvents()
    assert messages(warnings) == []


def test_quick_menu_and_url_dialog_open_cleanly(ui, app):
    from PySide6.QtCore import QObject

    engine, _, warnings = ui
    window = engine.rootObjects()[0]
    menu = window.findChild(QObject, "quickMenu")
    dialog = window.findChild(QObject, "urlDialog")
    assert menu is not None and dialog is not None
    menu.open()
    app.processEvents()
    assert menu.property("visible")
    menu.close()
    dialog.setProperty("open", True)
    app.processEvents()
    dialog.setProperty("open", False)
    app.processEvents()
    assert messages(warnings) == []


def test_hardware_decoding_toggle_flags_restart(ui, app):
    engine, _, warnings = ui
    prefs = engine.rootContext().contextProperty("prefs")
    assert prefs.property("restartNeeded") is False
    prefs.setProperty("hardwareDecoding", not prefs.property("hardwareDecoding"))
    assert prefs.property("restartNeeded") is True
    prefs.setProperty("hardwareDecoding", not prefs.property("hardwareDecoding"))
    assert prefs.property("restartNeeded") is False
    assert messages(warnings) == []


def test_about_page_shows_version_without_network(ui, app):
    from PySide6.QtCore import QObject

    from aperture import __version__

    engine, _, warnings = ui
    updates = engine.rootContext().contextProperty("updates")
    assert updates.property("currentVersion") == __version__
    assert updates.property("state") == "idle"
    window = engine.rootObjects()[0]
    dialog = window.findChild(QObject, "settingsDialog")
    window.setProperty("settingsOpen", True)
    dialog.setProperty("page", 5)
    app.processEvents()
    window.setProperty("settingsOpen", False)
    app.processEvents()
    assert messages(warnings) == []


def test_phase_10_commands_without_media(ui, app):
    engine, player, warnings = ui
    tracks = engine.rootContext().contextProperty("tracks")
    notices = []
    player.noticed.connect(notices.append)
    assert player.property("chapters") == [] and player.property("currentChapter") == -1
    player.nextChapter()
    assert "This file has no chapters" in notices
    tracks.nudgeSubtitles(100)
    tracks.nudgeSubtitles(100)
    assert tracks.property("subtitleDelay") == 200
    tracks.resetSubtitleDelay()
    assert tracks.property("subtitleDelay") == 0
    player.setProperty("audioBoost", 1.5)  # switches to the boosted path, or reports it can't
    player.setProperty("audioBoost", 1.0)
    assert player.property("audioBoost") == 1.0
    app.processEvents()
    assert messages(warnings) == []


def test_menus_with_chapters_and_boost_open_cleanly(ui, app):
    from PySide6.QtCore import QObject

    engine, _, warnings = ui
    window = engine.rootObjects()[0]
    menu = window.findChild(QObject, "quickMenu")
    menu.open()
    app.processEvents()
    menu.close()
    app.processEvents()
    assert messages(warnings) == []


def _visual_items(item):
    yield item
    for child in item.childItems():
        yield from _visual_items(child)


def _volume_key_works(app, window, player):
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest

    player.volume = 0.5
    QTest.keyClick(window, Qt.Key.Key_Down)
    app.processEvents()
    return player.volume < 0.5


def test_shortcuts_survive_rebinding_with_a_key_press(ui, app):
    # Rebinding rebuilt the rows mid-keypress, leaving the capture on: every shortcut stayed
    # dead until restart. Drive it like a user: listen on a row, press a key, close Settings.
    from PySide6.QtCore import QMetaObject, QObject, Qt
    from PySide6.QtTest import QTest

    engine, player, warnings = ui
    keymap = engine.rootContext().contextProperty("keymap")
    window = engine.rootObjects()[0]
    window.show()
    window.requestActivate()
    assert QTest.qWaitForWindowActive(window, 3000)
    window.setProperty("settingsOpen", True)
    window.findChild(QObject, "settingsDialog").setProperty("page", 4)
    app.processEvents()

    def row(action_id):
        for item in _visual_items(window.contentItem()):
            data = item.property("modelData")
            data = data.toVariant() if hasattr(data, "toVariant") else data
            if item.property("listening") is not None and isinstance(data, dict):
                if data.get("id") == action_id:
                    return item
        raise LookupError(action_id)

    QMetaObject.invokeMethod(row("mute"), "startListening")
    QTest.keyClick(window, Qt.Key.Key_K)
    app.processEvents()
    assert keymap.keys.value("mute") == "K"
    assert not keymap.property("capturing")

    QMetaObject.invokeMethod(row("mute"), "startListening")  # then Reset, still listening
    keymap.resetShortcuts()
    app.processEvents()
    window.setProperty("settingsOpen", False)
    app.processEvents()
    assert not keymap.property("capturing")
    assert _volume_key_works(app, window, player)
    assert messages(warnings) == []


def test_wheel_on_the_playlist_never_scrolls_what_is_underneath(ui, app):
    # The lyrics list sits under the playlist sheet; turns the sheet can't use leaked to it.
    from PySide6.QtCore import QPoint, QPointF, Qt, QUrl
    from PySide6.QtGui import QWheelEvent
    from PySide6.QtQml import QQmlComponent

    from aperture.app import QML_DIR

    engine, _, warnings = ui
    component = QQmlComponent(engine)
    component.setData(
        b"""
        import QtQuick
        Window {
            width: 800; height: 600; visible: true
            ListView {
                objectName: "under"
                anchors.fill: parent
                model: 200
                delegate: Text { text: index; height: 40 }
            }
            PlaylistPanel { x: 400; y: 50; width: 340; height: 400 }
        }
        """,
        QUrl.fromLocalFile(str(QML_DIR / "WheelProbe.qml")),
    )
    scene = component.create()
    assert scene is not None, component.errorString()
    app.processEvents()
    under = next(i for i in _visual_items(scene.contentItem()) if i.objectName() == "under")
    from PySide6.QtTest import QTest

    def turn(x):
        at = QPointF(x, 250)
        event = QWheelEvent(
            at, scene.mapToGlobal(at), QPoint(), QPoint(0, -360), Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.NoModifier, Qt.ScrollPhase.NoScrollPhase, False,
        )  # fmt: skip
        app.sendEvent(scene, event)
        QTest.qWait(300)  # Flickable animates wheel scrolling
        return under.property("contentY")

    assert turn(570) == 0  # on the sheet
    assert turn(100) > 0  # beside it: the probe really scrolls, so the check above means something
    scene.close()
    scene.deleteLater()
    assert messages(warnings) == []
