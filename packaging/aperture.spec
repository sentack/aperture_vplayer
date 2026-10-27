# PyInstaller build: one-folder app at dist/aperture with QML, icons and Qt Multimedia.
# From the repo root:  pyinstaller --noconfirm packaging/aperture.spec
# PyInstaller's PySide6 hooks collect the QML modules and the FFmpeg multimedia backend.

import sys
from pathlib import Path

ROOT = Path(SPECPATH).parent
SRC = ROOT / "src" / "aperture"
ICONS = ROOT / "packaging" / "icons"

a = Analysis(
    [str(ROOT / "packaging" / "launcher.py")],
    pathex=[str(ROOT / "src")],
    datas=[
        (str(SRC / "ui" / "qml"), "aperture/ui/qml"),
        (str(SRC / "resources"), "aperture/resources"),
    ],
    hiddenimports=[
        "PySide6.QtMultimedia",
        "PySide6.QtQml",
        "PySide6.QtQuick",
        "PySide6.QtSvg",
    ],
    # Large Qt add-ons the player never touches.
    excludes=[
        "tkinter",
        "PySide6.Qt3DCore",
        "PySide6.QtCharts",
        "PySide6.QtDataVisualization",
        "PySide6.QtPdf",
        "PySide6.QtWebEngineCore",
        "PySide6.QtWebEngineQuick",
        "PySide6.QtWebEngineWidgets",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="aperture",
    console=False,
    icon=str(ICONS / "aperture.ico") if sys.platform == "win32" else None,
    upx=False,
)

coll = COLLECT(exe, a.binaries, a.datas, name="aperture", upx=False)
