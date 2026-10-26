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
