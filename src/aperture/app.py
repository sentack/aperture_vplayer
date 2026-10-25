"""Application bootstrap."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

QML_DIR = Path(__file__).parent / "ui" / "qml"

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


def run(argv: list[str] | None = None) -> int:
    from PySide6.QtCore import QStandardPaths, QUrl, qInstallMessageHandler
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlApplicationEngine

    from aperture.core import History
    from aperture.logs import setup_logging
    from aperture.player import PlayerController
    from aperture.player.thumbnails import PROVIDER_ID, ThumbnailImages, ThumbnailService
    from aperture.settings import Settings
    from aperture.theme.controller import ThemeController

    app = QGuiApplication(sys.argv if argv is None else argv)
    app.setApplicationName("Aperture")

    data_dir = Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation))
    setup_logging(data_dir)
    qInstallMessageHandler(_qt_message)
    player = PlayerController(History(data_dir / "history.json"), app)
    appearance = ThemeController(Settings(data_dir / "settings.json"), app)
    thumbnail_images = ThumbnailImages()
    thumbnails = ThumbnailService(thumbnail_images, app)
    player.mediaLoaded.connect(thumbnails.setFile)
    app.aboutToQuit.connect(player.shutdown)
    engine = QQmlApplicationEngine()
    engine.addImageProvider(PROVIDER_ID, thumbnail_images)
    context = engine.rootContext()
    context.setContextProperty("player", player)
    context.setContextProperty("tracks", player.tracks)
    context.setContextProperty("theme", appearance.palette)
    context.setContextProperty("appearance", appearance)
    context.setContextProperty("thumbs", thumbnails)
    engine.load(QUrl.fromLocalFile(str(QML_DIR / "Main.qml")))
    if not engine.rootObjects():
        log.critical("could not load the user interface from %s", QML_DIR)
        return 1

    player.open_paths(app.arguments()[1:])
    code = app.exec()
    # Tear QML down while `player` is still alive so bindings never see it vanish.
    del engine
    return code
