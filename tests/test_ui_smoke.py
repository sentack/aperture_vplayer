"""Load the real QML against the real controllers, offscreen.

Catches what unit tests cannot: QML syntax errors, missing types, bad bindings.
Skipped when PySide6 is not installed.
"""

import os
from pathlib import Path

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

    lyrics.save([{"time": 1000, "text": "first"}, {"time": 3000, "text": "second"}])
    app.processEvents()
    assert read_embedded(song).startswith("[00:01.00]first")  # into the file itself
    assert not (tmp_path / "Song.lrc").exists()  # no sidecar for a format that holds lyrics
    assert lyrics.property("synced") and lyrics.property("plainText") == "first\nsecond"

    wav = tmp_path / "Take.wav"  # can't hold lyrics: they go beside it
    wav.write_bytes(bytes(64))
    player.mediaLoaded.emit(str(wav))
    lyrics.save([{"time": -1, "text": "plain"}])
    assert (tmp_path / "Take.lrc").read_text(encoding="utf-8") == "plain\n"

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


def test_single_window_setting_toggles_from_settings(ui, app):
    engine, _, warnings = ui
    prefs = engine.rootContext().contextProperty("prefs")
    window = engine.rootObjects()[0]
    window.setProperty("settingsOpen", True)
    app.processEvents()
    assert prefs.property("singleWindow") is True
    prefs.setProperty("singleWindow", False)
    app.processEvents()
    assert prefs.property("singleWindow") is False
    prefs.setProperty("singleWindow", True)
    app.processEvents()
    assert messages(warnings) == []


def test_repeat_and_shuffle_cycle_and_are_remembered(ui, app, tmp_path):
    from aperture.settings import Settings

    _, player, warnings = ui
    player.cycleRepeat()
    player.cycleRepeat()
    player.toggleShuffle()
    app.processEvents()
    assert player.property("repeatMode") == "one" and player.property("shuffle") is True
    saved = Settings(tmp_path / "settings.json")  # the ui fixture keeps its data in tmp_path
    assert saved.repeat == "one" and saved.shuffle is True
    player.cycleRepeat()
    assert player.property("repeatMode") == "off"
    assert messages(warnings) == []


class FakeNetwork:
    """Stands in for OnlineSearch._send: answers each request from a script, synchronously."""

    def __init__(self, *answers):
        self.answers = list(answers)  # (status, body) per request, in order
        self.requests = []

    def __call__(self, method, url, headers, body, done):
        self.requests.append((method, bytes(url.toEncoded()).decode(), headers, body))
        status, data = self.answers.pop(0)
        done(status, data, status is None or status >= 400)


def test_lyrics_search_embeds_the_chosen_result(ui, app, tmp_path):
    import json

    from aperture.core.lyrics_tags import read_embedded

    engine, player, warnings = ui
    online = engine.rootContext().contextProperty("online")
    song = tmp_path / "Band - Song.mp3"
    song.write_bytes(bytes(512))
    player.mediaLoaded.emit(str(song))
    assert online.property("canSearchLyrics") and not online.property("canSearchSubtitles")

    online.begin("lyrics")
    assert online.property("fields")["artist"] == "Band"  # from the file name: no tags
    synced = "[00:01.00]one\n[00:02.00]two"
    answer = [{"trackName": "Song", "artistName": "Band", "duration": 200, "syncedLyrics": synced}]
    online._send = FakeNetwork((200, json.dumps(answer).encode()))
    online.searchLyrics("Song", "Band", "")
    assert "track_name=Song" in online._send.requests[0][1]
    assert online.property("results")[0]["badge"] == "Synced"

    chosen = []
    online.chosen.connect(lambda: chosen.append(True))
    online.choose(0)
    assert chosen and read_embedded(song).startswith("[00:01.00]one")
    lyrics = engine.rootContext().contextProperty("lyrics")
    assert lyrics.property("synced") and lyrics.property("source") == "Embedded"
    assert messages(warnings) == []


def test_lyrics_search_failures_are_messages(ui, app, tmp_path):
    engine, player, _ = ui
    online = engine.rootContext().contextProperty("online")
    player.mediaLoaded.emit(str(tmp_path / "a.mp3"))
    online.begin("lyrics")
    online._send = FakeNetwork((200, b"[]"), (None, b""), (503, b""))
    online.searchLyrics("Nothing", "", "")
    assert online.property("status").startswith("No lyrics found")
    online.searchLyrics("Song", "", "")
    assert online.property("status").startswith("Couldn't reach LRCLIB")
    online.searchLyrics("Song", "", "")
    assert "unavailable" in online.property("status") and not online.property("busy")
    online.searchLyrics("  ", "", "")
    assert "title" in online.property("status")


def test_subtitle_search_needs_a_key_then_downloads_next_to_the_video(ui, app, tmp_path):
    import json

    engine, player, warnings = ui
    online = engine.rootContext().contextProperty("online")
    prefs = engine.rootContext().contextProperty("prefs")
    video = tmp_path / "The.Movie.2014.1080p.mkv"
    video.write_bytes(b"")
    player.mediaLoaded.emit(str(video))
    online.begin("subtitles")
    assert online.property("fields")["title"] == "The Movie"
    assert online.property("needsKey")
    online._send = FakeNetwork()
    online.searchSubtitles("The Movie", "2014", "en")
    assert "API key" in online.property("status") and online._send.requests == []

    prefs.setProperty("openSubtitlesKey", "  secret-key ")
    assert not online.property("needsKey")
    found = {"language": "en", "release": "The.Movie.2014", "files": [{"file_id": 7}]}
    search = {"data": [{"attributes": found}]}
    online._send = FakeNetwork(
        (200, json.dumps(search).encode()),
        (200, json.dumps({"link": "https://dl.example/7.srt"}).encode()),
        (200, b"1\n00:00:01,000 --> 00:00:02,000\nHello\n"),
    )
    online.searchSubtitles("The Movie", "2014", "en")
    method, url, headers, _ = online._send.requests[0]
    assert headers["Api-Key"] == "secret-key" and headers["User-Agent"].startswith("Aperture v")
    assert "query=The%20Movie" in url and "year=2014" in url
    online.choose(0)
    assert [r[0] for r in online._send.requests] == ["GET", "POST", "GET"]
    assert json.loads(online._send.requests[1][3]) == {"file_id": 7}
    saved = tmp_path / "The.Movie.2014.1080p.en.srt"
    assert saved.read_bytes().endswith(b"Hello\n")
    assert player.tracks.property("subtitleOptions")[-1] == saved.name
    assert messages(warnings) == []


def test_search_dialog_and_menu_entries_load_cleanly(ui, app, tmp_path):
    from PySide6.QtCore import QObject

    engine, player, warnings = ui
    window = engine.rootObjects()[0]
    player.mediaLoaded.emit(str(tmp_path / "clip.mkv"))
    dialog = window.findChild(QObject, "searchDialog")
    dialog.begin("subtitles")
    app.processEvents()
    assert dialog.property("open")
    dialog.close()
    menu = window.findChild(QObject, "quickMenu")
    menu.open()
    app.processEvents()
    menu.close()
    app.processEvents()
    assert messages(warnings) == []


def test_playlists_are_remembered_saved_and_reopened(ui, app, tmp_path):
    engine, player, warnings = ui
    playlists = engine.rootContext().contextProperty("playlists")
    videos = [tmp_path / name for name in ("Ep 1.mkv", "Ep 2.mkv", "Ep 3.mkv")]
    for video in videos:
        video.write_bytes(b"")
    player.open_paths(videos)
    player.clearPlaylist()  # a cleared playlist of two or more is remembered
    (first,) = playlists.property("recent")
    assert first["name"] == tmp_path.name and first["detail"].startswith("3 items")

    playlists.open(0)
    assert [Path(p).name for p in player.playlist_items()] == ["Ep 1.mkv", "Ep 2.mkv", "Ep 3.mkv"]
    from PySide6.QtCore import QUrl

    assert playlists.save(QUrl.fromLocalFile(str(tmp_path / "Binge")))  # suffix added
    saved = tmp_path / "Binge.aplaylist"
    assert saved.read_text().splitlines()[2] == "Ep 1.mkv"  # relative to its folder
    assert playlists.property("recent")[0]["name"] == "Binge"

    player.clearPlaylist()
    player.open_paths([saved])  # double-clicking the file does this
    assert len(player.playlist_items()) == 3
    assert playlists.property("recent")[0]["saved"] == str(saved)
    playlists.remove(0)
    assert all(r["name"] != "Binge" for r in playlists.property("recent"))
    assert messages(warnings) == []


def test_files_opened_from_outside_ask_before_joining(ui, app, tmp_path):
    from PySide6.QtCore import QObject

    engine, player, warnings = ui
    opening = engine.rootContext().contextProperty("opening")
    window = engine.rootObjects()[0]
    started = []
    opening._new_window = started.append  # what "Open in new window" would launch
    a, b = tmp_path / "a.mkv", tmp_path / "b.mkv"
    for f in (a, b):
        f.write_bytes(b"")
    player.open_paths([a])
    opening.offer([str(b)])
    opening.offer([str(b)])  # the same file again joins, not doubles
    app.processEvents()
    assert opening.property("pending") and opening.property("names") == ["b.mkv"]
    assert window.findChild(QObject, "openChoice").property("open")
    opening.addToPlaylist()
    assert [Path(p).name for p in player.playlist_items()] == ["a.mkv", "b.mkv"]
    opening.offer([str(tmp_path / "c.mkv")])
    opening.openInNewWindow()
    assert started == [[str(tmp_path / "c.mkv")]] and not opening.property("pending")
    opening.offer([str(a)])
    opening.dismiss()
    assert len(player.playlist_items()) == 2
    assert messages(warnings) == []


def test_icons_fill_their_own_box_so_they_centre(ui, app):
    # Qt's Shape resets its implicit size to its paths' bounding box. Icons then centred a
    # smaller box than the 24-unit grid they draw on, and sat off-centre (the play button).
    engine, _, warnings = ui
    window = engine.rootObjects()[0]
    window.show()
    app.processEvents()
    icons = []

    def walk(item):
        for child in item.childItems():
            if child.property("glyph") is not None and child.property("size"):
                icons.append(child)
            walk(child)

    walk(window.contentItem())
    assert icons
    for icon in icons:
        size = icon.property("size")
        assert (icon.width(), icon.height()) == (size, size)
    assert not messages(warnings)


def test_window_reopens_at_the_size_it_was_left(app, tmp_path):
    from PySide6.QtCore import QEventLoop, QTimer
    from PySide6.QtGui import QWindow

    from aperture.app import load_ui
    from aperture.settings import Settings
    from aperture.window_memory import SETTLE_MS

    def settle():
        loop = QEventLoop()
        QTimer.singleShot(SETTLE_MS + 200, loop.quit)
        loop.exec()

    def launch():
        engine, _ = load_ui(app, tmp_path, settings=Settings(path))
        return engine, engine.rootObjects()[0], engine.rootContext().contextProperty("windowSize")

    def close(engine, window):
        window.close()
        engine.deleteLater()
        _flush_deletes(app)
        for child in app.children():
            if type(child).__module__.startswith("aperture."):
                child.deleteLater()
        _flush_deletes(app)

    path = tmp_path / "settings.json"
    settings = Settings(path)
    settings.window_size = [760, 500]  # fits the offscreen test screen (800 wide)
    settings.save()
    engine, window, memory = launch()
    try:
        assert (window.width(), window.height()) == (760, 500)
        window.resize(740, 480)  # the user resizes it
        settle()
        window.showMaximized()  # maximizing doesn't replace the size to come back to
        settle()
        memory.save()
    finally:
        close(engine, window)
    saved = Settings(path)
    assert saved.window_size == [740, 480]
    if not saved.window_maximized:
        pytest.skip("this platform cannot maximize windows")
    engine, window, memory = launch()  # reopens maximized, and un-maximizes to that size
    try:
        settle()
        assert window.visibility() == QWindow.Visibility.Maximized
        window.showNormal()
        settle()
        assert (window.width(), window.height()) == (740, 480)
    finally:
        close(engine, window)


def test_changes_to_a_playlist_file_are_saved_back(ui, app, tmp_path):
    from PySide6.QtCore import QEventLoop, QTimer

    from aperture.core.playlist_file import read_playlist
    from aperture.player.playlists import AUTOSAVE_DELAY_MS

    engine, player, warnings = ui
    playlists = engine.rootContext().contextProperty("playlists")
    prefs = engine.rootContext().contextProperty("prefs")
    a, b, c = (tmp_path / f"{n}.mkv" for n in "abc")
    for f in (a, b, c):
        f.write_bytes(b"")
    unplugged = tmp_path / "usb" / "x.mkv"  # listed, but not there right now
    saved = tmp_path / "Mine.aplaylist"
    saved.write_text(f"#EXTM3U\na.mkv\n{unplugged}\nb.mkv\n")
    player.open_paths([saved])
    assert playlists.property("fileName") == "Mine.aplaylist"
    assert not playlists.property("unsaved")

    player.add_paths([c])
    assert playlists.property("unsaved")  # the Save button shows
    assert playlists.saveChanges()
    assert read_playlist(saved) == [a, unplugged, b, c]  # the missing one is kept
    assert not playlists.property("unsaved")

    prefs.setProperty("autosavePlaylist", True)
    player.removeIndex(0)  # a.mkv
    loop = QEventLoop()
    QTimer.singleShot(AUTOSAVE_DELAY_MS + 300, loop.quit)
    loop.exec()
    assert read_playlist(saved) == [unplugged, b, c]
    assert not playlists.property("unsaved")

    player.add_paths([a])  # a change still waiting is written before the playlist goes
    player.clearPlaylist()
    assert read_playlist(saved) == [unplugged, b, c, a]
    assert playlists.property("fileName") == ""
    prefs.setProperty("autosavePlaylist", False)
    assert messages(warnings) == []
