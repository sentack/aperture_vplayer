"""Application bootstrap."""

from __future__ import annotations

import sys
from pathlib import Path

QML_DIR = Path(__file__).parent / "ui" / "qml"


def run(argv: list[str] | None = None) -> int:
    from PySide6.QtCore import QUrl
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlApplicationEngine

    from aperture.player import PlayerController
    from aperture.theme import ACCENTS, DARK, DEFAULT_ACCENT, qml_palette

    app = QGuiApplication(sys.argv if argv is None else argv)
    app.setApplicationName("Aperture")

    player = PlayerController(app)
    engine = QQmlApplicationEngine()
    context = engine.rootContext()
    context.setContextProperty("player", player)
    context.setContextProperty("theme", qml_palette(DARK, ACCENTS[DEFAULT_ACCENT]))
    engine.load(QUrl.fromLocalFile(str(QML_DIR / "Main.qml")))
    if not engine.rootObjects():
        return 1

    player.open_paths(app.arguments()[1:])
    code = app.exec()
    # Tear QML down while `player` is still alive so bindings never see it vanish.
    del engine
    return code
