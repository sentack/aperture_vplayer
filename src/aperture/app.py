"""Application bootstrap."""

from __future__ import annotations

import sys
from pathlib import Path

QML_DIR = Path(__file__).parent / "ui" / "qml"


def run(argv: list[str] | None = None) -> int:
    from PySide6.QtCore import QUrl
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlApplicationEngine

    app = QGuiApplication(sys.argv if argv is None else argv)
    app.setApplicationName("Aperture")

    engine = QQmlApplicationEngine()
    engine.load(QUrl.fromLocalFile(str(QML_DIR / "Main.qml")))
    if not engine.rootObjects():
        return 1
    return app.exec()
