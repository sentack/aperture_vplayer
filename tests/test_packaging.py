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


def test_release_artifacts_are_compressed():
    iss = (PACKAGING / "windows" / "aperture.iss").read_text(encoding="utf-8")
    assert "Compression=lzma2/ultra64" in iss and "SolidCompression=yes" in iss
    appimage = (PACKAGING / "linux" / "build-appimage.sh").read_text(encoding="utf-8")
    assert "--comp zstd" in appimage and "xz -9" in appimage
    assert "-format ULMO" in (PACKAGING / "macos" / "build-dmg.sh").read_text(encoding="utf-8")


def _load_check_bundle():
    import importlib.util

    spec = importlib.util.spec_from_file_location("check_bundle", PACKAGING / "check_bundle.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _fake_bundle(root, windows=False):
    files = [
        "_internal/PySide6/qml/QtMultimedia/qmldir",
        "_internal/PySide6/qml/QtQuick/Controls/qmldir",
        "_internal/PySide6/qml/QtQuick/Dialogs/qmldir",
        "_internal/PySide6/qml/QtQuick/Shapes/qmldir",
        "_internal/aperture/ui/qml/Main.qml",
    ]
    if windows:
        files += ["_internal/PySide6/plugins/multimedia/ffmpegmediaplugin.dll"]
        files += [f"_internal/PySide6/{lib}-61.dll" for lib in ("avcodec", "avformat", "avutil")]
        files += ["_internal/PySide6/swresample-5.dll", "_internal/PySide6/swscale-8.dll"]
    else:
        files += ["_internal/PySide6/Qt/plugins/multimedia/libffmpegmediaplugin.so"]
        lib = "_internal/PySide6/Qt/lib"
        files += [f"{lib}/lib{name}.so.61" for name in ("avcodec", "avformat", "avutil")]
        files += [f"{lib}/libswresample.so.5", f"{lib}/libswscale.so.8"]
    for name in files:
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        (root / name).touch()


def test_check_bundle_accepts_complete_builds(tmp_path):
    check = _load_check_bundle().check
    _fake_bundle(tmp_path / "linux")
    _fake_bundle(tmp_path / "windows", windows=True)
    assert check(tmp_path / "linux") == []
    assert check(tmp_path / "windows") == []


def test_check_bundle_reports_missing_codecs_and_webengine(tmp_path):
    check = _load_check_bundle().check
    _fake_bundle(tmp_path)
    (tmp_path / "_internal/PySide6/Qt/lib/libavcodec.so.61").unlink()
    (tmp_path / "_internal/PySide6/Qt/lib/libQt6WebEngineCore.so.6").touch()
    problems = check(tmp_path)
    assert "missing: libavcodec (decoders)" in problems
    assert any(p.startswith("unexpected: Qt WebEngine") for p in problems)
    assert check(tmp_path / "nope") == [f"{tmp_path / 'nope'} is not a directory"]


def test_release_publishes_checksums_and_build_info():
    from aperture.core.release import CHECKSUMS_ASSET

    workflow = (PACKAGING.parent / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
    assert f"sha256sum -- * > {CHECKSUMS_ASSET}" in workflow
    assert "src/aperture/resources/build_info.json" in workflow
