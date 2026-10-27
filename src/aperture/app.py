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
    from aperture.player.thumbnails import PROVIDER_ID, ThumbnailImages, ThumbnailService
    from aperture.settings import Settings
    from aperture.theme.controller import ThemeController

    player = PlayerController(History(data_dir / "history.json"), app)
    appearance = ThemeController(Settings(data_dir / "settings.json"), app)
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
    context.setContextProperty("theme", appearance.palette)
    context.setContextProperty("appearance", appearance)
    context.setContextProperty("thumbs", thumbnails)
    engine.load(QUrl.fromLocalFile(str(QML_DIR / "Main.qml")))
    return engine, player


def run(argv: list[str] | None = None) -> int:
    from PySide6.QtCore import QStandardPaths, qInstallMessageHandler
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

    player.open_paths(app.arguments()[1:])
    code = app.exec()
    # Tear QML down while `player` is still alive so bindings never see it vanish.
    del engine
    return code
