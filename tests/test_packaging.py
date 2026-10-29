import re
from pathlib import Path

from aperture.core.formats import VIDEO_EXTENSIONS

PACKAGING = Path(__file__).resolve().parent.parent / "packaging"


def test_windows_installer_registers_every_video_extension():
    text = (PACKAGING / "windows" / "aperture.iss").read_text(encoding="utf-8")
    open_with = set(re.findall(r"Software\\Classes\\(\.\w+)\\OpenWithProgids", text))
    supported = set(re.findall(r'SupportedTypes"; ValueType: string; ValueName: "(\.\w+)"', text))
    assert open_with == supported == VIDEO_EXTENSIONS


def test_windows_installer_uses_generated_icon():
    text = (PACKAGING / "windows" / "aperture.iss").read_text(encoding="utf-8")
    assert "SetupIconFile=..\\icons\\aperture.ico" in text
    assert (PACKAGING / "icons" / "aperture.ico").is_file()


MIME_TYPES = {
    ".3gp": "video/3gpp",
    ".avi": "video/x-msvideo",
    ".flv": "video/x-flv",
    ".m2ts": "video/mp2t",
    ".m4v": "video/x-m4v",
    ".mkv": "video/x-matroska",
    ".mov": "video/quicktime",
    ".mp4": "video/mp4",
    ".mpeg": "video/mpeg",
    ".mpg": "video/mpeg",
    ".ogv": "video/ogg",
    ".ts": "video/mp2t",
    ".webm": "video/webm",
    ".wmv": "video/x-ms-wmv",
}


def desktop_entry() -> dict[str, str]:
    path = PACKAGING / "linux" / "io.github.sentack.Aperture.desktop"
    lines = path.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "[Desktop Entry]"
    return dict(line.split("=", 1) for line in lines[1:] if line)


def test_desktop_entry_claims_every_video_type():
    assert set(MIME_TYPES) == VIDEO_EXTENSIONS
    declared = set(filter(None, desktop_entry()["MimeType"].split(";")))
    assert declared == set(MIME_TYPES.values())


def test_desktop_entry_matches_app_id():
    from aperture.app import DESKTOP_ID

    entry = desktop_entry()
    assert entry["Icon"] == DESKTOP_ID
    assert entry["Exec"] == "aperture %F"
    assert (PACKAGING / "linux" / f"{DESKTOP_ID}.desktop").is_file()


def test_macos_bundle_assets():
    import plistlib

    entitlements = plistlib.loads((PACKAGING / "macos" / "entitlements.plist").read_bytes())
    assert entitlements["com.apple.security.cs.disable-library-validation"] is True
    assert (PACKAGING / "icons" / "aperture.icns").read_bytes()[:4] == b"icns"
    spec = (PACKAGING / "aperture.spec").read_text(encoding="utf-8")
    assert 'icon=str(ICONS / "aperture.icns")' in spec and "bundle_identifier=DESKTOP_ID" in spec


def test_bundle_drops_unused_qt_addons():
    import re

    spec = (PACKAGING / "aperture.spec").read_text(encoding="utf-8")
    names = re.search(r"UNUSED_QT = \((.*?)\)", spec, re.S).group(1)
    for addon in ("WebEngine", "Quick3D", "Pdf"):
        assert f'"{addon}"' in names
    # Add-ons the player does use must never match the filter.
    for needed in ("Qt6Multimedia", "Qt6Quick", "Qt6QuickControls2", "Qt6QuickShapes", "Qt6Svg"):
        assert not any(name.strip(' "\n') in needed for name in names.split(",") if name.strip())
    assert "a.binaries = [entry for entry in a.binaries if _used(entry)]" in spec
