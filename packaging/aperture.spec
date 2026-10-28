# PyInstaller build: one-folder app at dist/aperture with QML, icons and Qt Multimedia,
# plus dist/Aperture.app on macOS.
# From the repo root:  pyinstaller --noconfirm packaging/aperture.spec
# PyInstaller's PySide6 hooks collect the QML modules and the FFmpeg multimedia backend.

import sys
from pathlib import Path

ROOT = Path(SPECPATH).parent
SRC = ROOT / "src" / "aperture"
ICONS = ROOT / "packaging" / "icons"

sys.path.insert(0, str(ROOT / "src"))
from aperture import __version__  # noqa: E402
from aperture.app import DESKTOP_ID  # noqa: E402
from aperture.core.formats import VIDEO_EXTENSIONS  # noqa: E402

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

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="Aperture.app",
        icon=str(ICONS / "aperture.icns"),
        bundle_identifier=DESKTOP_ID,
        version=__version__,
        info_plist={
            "CFBundleName": "Aperture",
            "CFBundleDisplayName": "Aperture",
            "CFBundleShortVersionString": __version__,
            "CFBundleVersion": __version__,
            "LSMinimumSystemVersion": "12.0",
            "LSApplicationCategoryType": "public.app-category.video",
            "NSHighResolutionCapable": True,
            # Follow the system light/dark appearance instead of forcing Aqua.
            "NSRequiresAquaSystemAppearance": False,
            # "Open With" for every container the player knows, without claiming the default.
            "CFBundleDocumentTypes": [
                {
                    "CFBundleTypeName": "Video",
                    "CFBundleTypeRole": "Viewer",
                    "LSHandlerRank": "Alternate",
                    "CFBundleTypeExtensions": sorted(ext.lstrip(".") for ext in VIDEO_EXTENSIONS),
                }
            ],
        },
    )
