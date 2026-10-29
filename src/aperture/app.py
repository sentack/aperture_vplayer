"""Application bootstrap."""

from __future__ import annotations

import logging
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


def load_ui(app, data_dir: Path, on_warnings=None):
    """Create the controllers, expose them to QML and load the main window.

    Returns `(engine, player)`; the engine has no root objects if QML failed to load.
    `on_warnings` receives lists of QQmlError, connected before loading so none are missed.
    """
    from PySide6.QtCore import QUrl
    from PySide6.QtQml import QQmlApplicationEngine

    from aperture.core import History
    from aperture.player import PlayerController
    from aperture.player.lyrics import LyricsController
    from aperture.player.thumbnails import PROVIDER_ID, ThumbnailImages, ThumbnailService
    from aperture.preferences import PreferencesController
    from aperture.settings import Settings
    from aperture.theme.controller import ThemeController

    settings = Settings(data_dir / "settings.json")
    player = PlayerController(History(data_dir / "history.json"), app)
    appearance = ThemeController(settings, app)
    prefs = PreferencesController(settings, app)
    prefs.resetDone.connect(appearance.reload)

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
    context.setContextProperty("theme", appearance.palette)
    context.setContextProperty("appearance", appearance)
    context.setContextProperty("prefs", prefs)
    context.setContextProperty("thumbs", thumbnails)
    engine.load(QUrl.fromLocalFile(str(QML_DIR / "Main.qml")))
    return engine, player


def run(argv: list[str] | None = None) -> int:
    from PySide6.QtCore import QEvent, QObject, QStandardPaths, QTimer, qInstallMessageHandler
    from PySide6.QtGui import QGuiApplication, QIcon

    from aperture.logs import setup_logging

    app = QGuiApplication(sys.argv if argv is None else argv)
    app.setApplicationName("Aperture")
    app.setDesktopFileName(DESKTOP_ID)
    app.setWindowIcon(QIcon(str(ICON_PATH)))

    data_dir = Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation))
    setup_logging(data_dir)
    qInstallMessageHandler(_qt_message)

    engine, player = load_ui(app, data_dir)
    if not engine.rootObjects():
        log.critical("could not load the user interface from %s", QML_DIR)
        return 1

    # macOS hands Finder "Open With" and Dock drops to the app as FileOpen events, not argv.
    # A multi-file open arrives as one event per file; batch them into a single queue.
    pending: list[str] = []
    flush = QTimer(app, singleShot=True, interval=150)
    flush.timeout.connect(lambda: (player.open_paths(pending.copy()), pending.clear()))

    class FileOpenFilter(QObject):
        def eventFilter(self, obj, event) -> bool:
            if event.type() == QEvent.Type.FileOpen:
                pending.append(event.file())
                flush.start()
                return True
            return False

    file_opener = FileOpenFilter(app)
    app.installEventFilter(file_opener)

    player.open_paths(app.arguments()[1:])
    code = app.exec()
    # Tear QML down while `player` is still alive so bindings never see it vanish.
    del engine
    return code
