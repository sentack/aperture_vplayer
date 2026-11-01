"""Application bootstrap."""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

QML_DIR = Path(__file__).parent / "ui" / "qml"
ICON_PATH = Path(__file__).parent / "resources" / "aperture.svg"
# Matches the .desktop file name, so Wayland compositors pair the window with its icon.
DESKTOP_ID = "io.github.sentack.Aperture"

log = logging.getLogger(__name__)


def _qt_message(mode, context, message: str) -> None:
    """Route qWarning/QML errors into the log file instead of only stderr."""
    from PySide6.QtCore import QtMsgType

    levels = {
        QtMsgType.QtDebugMsg: logging.DEBUG,
        QtMsgType.QtInfoMsg: logging.INFO,
        QtMsgType.QtWarningMsg: logging.WARNING,
        QtMsgType.QtCriticalMsg: logging.ERROR,
        QtMsgType.QtFatalMsg: logging.CRITICAL,
    }
    logging.getLogger("qt").log(levels.get(mode, logging.WARNING), "%s", message)


def apply_decoder_choice(hardware_decoding: bool) -> None:
    """Software-only decoding when hardware decoding is off. Must run before Qt Multimedia starts.

    Qt's FFmpeg backend reads these once: "none" matches no hardware device type, and
    turning off GPU texture conversion fixes the "sound but a black picture" failure some
    VP8/VP9 (WebM) streams show with hardware decoders. A variable the user already set wins.
    """
    if not hardware_decoding:
        os.environ.setdefault("QT_FFMPEG_DECODING_HW_DEVICE_TYPES", "none")
        os.environ.setdefault("QT_DISABLE_HW_TEXTURES_CONVERSION", "1")


def restart_command() -> tuple[str, list[str]]:
    """Program and arguments that start Aperture again, frozen or from source."""
    if getattr(sys, "frozen", False):
        return sys.executable, []
    return sys.executable, ["-m", "aperture"]


def load_ui(app, data_dir: Path, on_warnings=None, settings=None):
    """Create the controllers, expose them to QML and load the main window.

    Returns `(engine, player)`; the engine has no root objects if QML failed to load.
    `on_warnings` receives lists of QQmlError, connected before loading so none are missed.
    `settings` is read from `data_dir` when not given.
    """
    from PySide6.QtCore import QUrl
    from PySide6.QtQml import QQmlApplicationEngine

    from aperture.core import History
    from aperture.defaults import DefaultPlayerController
    from aperture.keys import KeymapController
    from aperture.player import PlayerController
    from aperture.player.lyrics import LyricsController
    from aperture.player.thumbnails import PROVIDER_ID, ThumbnailImages, ThumbnailService
    from aperture.preferences import PreferencesController
    from aperture.settings import Settings
    from aperture.theme.controller import ThemeController
    from aperture.update.controller import UpdateController
    from aperture.update.install import detect
    from aperture.build import load_build_info

    settings = settings if settings is not None else Settings(data_dir / "settings.json")
    player = PlayerController(History(data_dir / "history.json"), app)
    appearance = ThemeController(settings, app)
    prefs = PreferencesController(settings, app)
    keymap = KeymapController(settings, mac=sys.platform == "darwin", parent=app)
    prefs.resetDone.connect(appearance.reload)
    prefs.resetDone.connect(keymap.reload)

    # New sessions start from the saved defaults; the speed in use is remembered as it changes.
    player.volume = settings.default_volume
    player.rate = settings.start_rate
    player.rateChanged.connect(lambda: prefs.remember_rate(player.rate))
    prefs.rateSelected.connect(lambda rate: setattr(player, "rate", rate))

    def follow_prefs() -> None:
        player.tracks.auto_select = settings.subtitles_auto
        player.resume_mode = settings.resume_mode

    follow_prefs()
    prefs.changed.connect(follow_prefs)

    # Repeat and shuffle carry over to the next session.
    player.repeatMode = settings.repeat
    player.shuffle = settings.shuffle

    def remember_play_mode() -> None:
        settings.repeat = player.repeatMode
        settings.shuffle = player.shuffle
        settings.save()

    player.playModeChanged.connect(remember_play_mode)

    def reset_play_mode() -> None:
        player.repeatMode = settings.repeat
        player.shuffle = settings.shuffle

    prefs.resetDone.connect(reset_play_mode)
    defaults = DefaultPlayerController(settings, ICON_PATH, app)
    defaults.noticed.connect(player.noticed)
    lyrics = LyricsController(player, app)
    lyrics.noticed.connect(player.noticed)
    player.lyricsDropped.connect(lyrics.load_files)
    thumbnail_images = ThumbnailImages()
    thumbnails = ThumbnailService(thumbnail_images, app)
    player.mediaLoaded.connect(thumbnails.setFile)
    app.aboutToQuit.connect(player.shutdown)

    engine = QQmlApplicationEngine()
    if on_warnings is not None:
        engine.warnings.connect(on_warnings)
    engine.addImageProvider(PROVIDER_ID, thumbnail_images)
    context = engine.rootContext()
    context.setContextProperty("player", player)
    context.setContextProperty("tracks", player.tracks)
    context.setContextProperty("lyrics", lyrics)
    context.setContextProperty("defaults", defaults)
    context.setContextProperty("theme", appearance.palette)
    context.setContextProperty("appearance", appearance)
    context.setContextProperty("prefs", prefs)
    context.setContextProperty("keymap", keymap)
    updates = UpdateController(data_dir, detect(), load_build_info(), app.quit, app)
    updates.noticed.connect(player.noticed)
    context.setContextProperty("updates", updates)
    context.setContextProperty("thumbs", thumbnails)
    engine.load(QUrl.fromLocalFile(str(QML_DIR / "Main.qml")))
    return engine, player


def run(argv: list[str] | None = None) -> int:
    from PySide6.QtCore import (
        QEvent,
        QObject,
        QProcess,
        QStandardPaths,
        Qt,
        qInstallMessageHandler,
    )
    from PySide6.QtGui import QGuiApplication, QIcon

    from aperture.logs import setup_logging
    from aperture.settings import Settings

    # Names first: they decide the data folder, and settings decide decoding before Qt starts.
    QGuiApplication.setApplicationName("Aperture")
    app_data = QStandardPaths.StandardLocation.AppDataLocation
    data_dir = Path(QStandardPaths.writableLocation(app_data))
    settings = Settings(data_dir / "settings.json")
    apply_decoder_choice(settings.hardware_decoding)

    app = QGuiApplication(sys.argv if argv is None else argv)
    app.setDesktopFileName(DESKTOP_ID)
    app.setWindowIcon(QIcon(str(ICON_PATH)))

    setup_logging(data_dir)
    qInstallMessageHandler(_qt_message)

    from aperture.core.launch import absolute_args
    from aperture.instance import LaunchRouter, claim, take_over

    # Single window (the default): if Aperture is already running, it takes these files and
    # this launch ends here. A multi-file "Open" that starts one process per file becomes
    # one playlist this way. With the setting off, every launch is its own window.
    launch_args = absolute_args(app.arguments()[1:], os.getcwd())
    instance = None
    if settings.single_window:
        forwarded, instance = claim(data_dir, launch_args)
        if forwarded:
            return 0

    from aperture.update.controller import apply_pending, mark_launched
    from aperture.update.install import detect

    # An update the user chose to install "later" goes in now, before any window opens.
    if apply_pending(data_dir, detect()):
        return 0

    engine, player = load_ui(app, data_dir, settings=settings)

    def restart() -> None:
        player.shutdown()
        if instance is not None:
            instance.close()  # or the new process would hand itself to this one and quit
        program, arguments = restart_command()
        if QProcess.startDetached(program, arguments):
            app.quit()
        else:
            player.noticed.emit("Couldn't restart Aperture. Close and open it again.")

    engine.rootContext().contextProperty("prefs").restartRequested.connect(restart)
    if not engine.rootObjects():
        log.critical("could not load the user interface from %s", QML_DIR)
        return 1
    mark_launched(data_dir)  # an updater waiting on this version can keep it now

    from aperture.core.media import is_url

    window = engine.rootObjects()[0]

    def open_files(files: list[str]) -> None:
        if len(files) == 1 and is_url(files[0]):
            player.openUrl(files[0])
        else:
            player.open_paths(files)

    def bring_to_front() -> None:
        window.setWindowStates(window.windowStates() & ~Qt.WindowState.WindowMinimized)
        window.raise_()
        window.requestActivate()

    router = LaunchRouter(open_files, player.add_paths, bring_to_front, parent=app)

    def receive(args: list[str]) -> None:
        router.submit(args, from_elsewhere=True)

    if instance is not None:
        instance.received.connect(receive)

    def follow_single_window() -> None:
        """The setting applies at once: stop or start taking other launches' files."""
        nonlocal instance
        if settings.single_window and instance is None:
            instance = take_over(data_dir)
            if instance is not None:
                instance.received.connect(receive)
        elif not settings.single_window and instance is not None:
            instance.close()
            instance = None

    engine.rootContext().contextProperty("prefs").changed.connect(follow_single_window)

    # macOS hands Finder "Open With" and Dock drops to the app as FileOpen events, not argv:
    # one event per file, which the router gathers into one playlist like separate launches.
    class FileOpenFilter(QObject):
        def eventFilter(self, obj, event) -> bool:
            if event.type() == QEvent.Type.FileOpen:
                router.submit([event.file()])
                return True
            return False

    file_opener = FileOpenFilter(app)
    app.installEventFilter(file_opener)

    router.submit(launch_args)
    code = app.exec()
    # Tear QML down while `player` is still alive so bindings never see it vanish.
    del engine
    return code
