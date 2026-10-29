import re
import subprocess
from pathlib import Path

import pytest

from aperture.core.schedule import DEFAULT_PROMPT_INTERVAL_S, should_ask_default
from aperture.core.formats import VIDEO_EXTENSIONS
from aperture.settings import Settings
from aperture.system import default_player

ROOT = Path(__file__).resolve().parent.parent
HOUR = 3600


@pytest.mark.parametrize(
    ("now", "last", "enabled", "is_default", "expected"),
    [
        (10 * HOUR, 0, True, False, True),
        (10 * HOUR, 9 * HOUR, True, False, False),  # asked an hour ago
        (10 * HOUR, 10 * HOUR - DEFAULT_PROMPT_INTERVAL_S, True, False, True),
        (10 * HOUR, 0, False, False, False),  # turned off
        (10 * HOUR, 0, True, True, False),  # already default
        (10 * HOUR, 0, True, None, False),  # cannot tell
        (10 * HOUR, 20 * HOUR, True, False, True),  # clock moved back
    ],
)
def test_should_ask_default(now, last, enabled, is_default, expected):
    assert should_ask_default(now, last, enabled, is_default) is expected


class FakeRun:
    """Stands in for subprocess.run: remembers calls, answers `xdg-mime query`."""

    def __init__(self, default=""):
        self.default = default
        self.calls = []

    def __call__(self, args, **kwargs):
        self.calls.append(args)
        if args[:2] == ["xdg-mime", "default"]:
            self.default = args[2]
        out = self.default + "\n" if args[:2] == ["xdg-mime", "query"] else ""
        return subprocess.CompletedProcess(args, 0, stdout=out, stderr="")


def test_linux_status():
    assert default_player.linux_status(FakeRun("vlc.desktop")) is False
    assert default_player.linux_status(FakeRun(default_player.DESKTOP_FILE)) is True

    def missing(*args, **kwargs):
        raise FileNotFoundError("xdg-mime")

    assert default_player.linux_status(missing) is None


def test_linux_claim_installs_appimage_entry(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "share"))
    monkeypatch.setenv("XDG_DATA_DIRS", str(tmp_path / "system"))
    monkeypatch.setenv("APPIMAGE", "/opt/Aperture.AppImage")
    run = FakeRun("vlc.desktop")
    icon = tmp_path / "icon.svg"
    icon.write_text("<svg/>")

    assert default_player.linux_claim(icon, run) == default_player.DONE

    entry = (tmp_path / "share" / "applications" / default_player.DESKTOP_FILE).read_text()
    assert 'Exec="/opt/Aperture.AppImage" %F' in entry
    assert (tmp_path / "share" / "icons" / "hicolor" / "scalable" / "apps").is_dir()
    claimed = next(c for c in run.calls if c[:2] == ["xdg-mime", "default"])
    assert claimed[3:] == list(default_player.MIME_TYPES)


def test_mime_types_match_desktop_entry():
    desktop = (ROOT / "packaging" / "linux" / "io.github.sentack.Aperture.desktop").read_text()
    declared = re.search(r"^MimeType=(.*)$", desktop, re.M).group(1)
    assert set(filter(None, declared.split(";"))) == set(default_player.MIME_TYPES)


def test_installer_registers_default_apps_capabilities():
    iss = (ROOT / "packaging" / "windows" / "aperture.iss").read_text(encoding="utf-8")
    assert 'ValueName: "Aperture"; ValueData: "Software\\Aperture\\Capabilities"' in iss
    pattern = r'FileAssociations"; ValueType: string; ValueName: "(\.\w+)"'
    capabilities = set(re.findall(pattern, iss))
    assert capabilities == VIDEO_EXTENSIONS
    assert "registeredAppUser=Aperture" in default_player.WINDOWS_DEFAULT_APPS


def test_settings_default_prompt_fields(tmp_path):
    path = tmp_path / "settings.json"
    settings = Settings(path)
    assert settings.ask_default is True and settings.ask_default_last == 0
    settings.ask_default = False
    settings.ask_default_last = 1234.5
    settings.save()
    loaded = Settings(path)
    assert loaded.ask_default is False and loaded.ask_default_last == 1234.5
    loaded.reset()
    assert loaded.ask_default is True and loaded.ask_default_last == 1234.5
