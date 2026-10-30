import subprocess
import sys
from pathlib import Path

import pytest

from aperture.update.install import detect
from aperture.update.scripts import POSIX_UPDATER, WINDOWS_UPDATER

# --- detect -------------------------------------------------------------------------------


def test_source_checkout():
    install = detect(frozen=False)
    assert install.kind == "source" and not install.downloads and "git pull" in install.hint


def test_windows_installer_vs_portable(tmp_path):
    exe = tmp_path / "Aperture" / "aperture.exe"
    exe.parent.mkdir()
    assert detect("win32", True, str(exe), {}).kind == "portable"
    (exe.parent / "unins000.exe").touch()
    install = detect("win32", True, str(exe), {})
    assert install.kind == "windows-installer" and install.target == exe.parent
    assert install.self_updates


def test_macos_app_bundle():
    install = detect("darwin", True, "/Applications/Aperture.app/Contents/MacOS/aperture", {})
    assert install.kind == "macos-dmg" and install.target == Path("/Applications/Aperture.app")
    assert install.downloads and not install.self_updates


def test_linux_appimage_keeps_its_path():
    env = {"APPIMAGE": "/home/me/Apps/Aperture.AppImage"}
    install = detect("linux", True, "/tmp/.mount_x/usr/bin/aperture", env)
    assert install.kind == "appimage" and install.target == Path("/home/me/Apps/Aperture.AppImage")


def test_linux_tarball_and_package_manager():
    tarball = detect("linux", True, "/home/me/aperture/aperture", {})
    assert tarball.kind == "tarball" and tarball.target == Path("/home/me/aperture")
    managed = detect("linux", True, "/usr/lib/aperture/aperture", {})
    assert managed.kind == "managed" and not managed.downloads


def test_windows_updater_backs_up_and_rolls_back():
    for step in ("Wait-Process", "robocopy $AppDir $backup", "/SILENT", "Test-Path $Marker",
                 "robocopy $backup $AppDir", "/ALLUSERS"):  # fmt: skip
        assert step in WINDOWS_UPDATER


# --- the POSIX updater, run for real ------------------------------------------------------

posix_only = pytest.mark.skipif(sys.platform == "win32", reason="needs /bin/sh")


def fake_app(path: Path, started: Path, writes_marker: Path | None) -> None:
    """An executable that records it ran and, if healthy, reports a successful start."""
    body = f'#!/bin/sh\necho "$0" >> "{started}"\n'
    if writes_marker is not None:
        body += f'touch "{writes_marker}"\n'
    path.write_text(body)
    path.chmod(0o755)


def run_updater(tmp_path, new, target, kind, marker, timeout="1"):
    script = tmp_path / "updater.sh"
    script.write_text(POSIX_UPDATER)
    gone = subprocess.Popen(["true"])
    gone.wait()  # a pid that has already exited, as the app will have by then
    return subprocess.run(
        ["sh", str(script), str(gone.pid), str(new), str(target), kind, str(marker), timeout],
        capture_output=True, text=True, timeout=20,
    )  # fmt: skip


@posix_only
def test_appimage_update_is_kept_when_new_version_starts(tmp_path):
    started, marker = tmp_path / "started.log", tmp_path / "launched"
    target, new = tmp_path / "Aperture.AppImage", tmp_path / ".Aperture-update.AppImage"
    fake_app(target, started, None)
    fake_app(new, started, marker)
    new.chmod(0o644)  # downloads are not executable; the updater fixes that

    result = run_updater(tmp_path, new, target, "appimage", marker, timeout="5")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "touch" in target.read_text()  # new version in place, same path
    assert not (tmp_path / "Aperture.AppImage.previous").exists()
    assert not new.exists()


@posix_only
def test_appimage_update_rolls_back_when_new_version_fails(tmp_path):
    started, marker = tmp_path / "started.log", tmp_path / "launched"
    target, new = tmp_path / "Aperture.AppImage", tmp_path / ".Aperture-update.AppImage"
    fake_app(target, started, None)
    old = target.read_text()
    fake_app(new, started, None)  # never reports a successful start
    new.write_text(new.read_text() + "# broken build\n")

    result = run_updater(tmp_path, new, target, "appimage", marker)

    assert result.returncode == 1
    assert target.read_text() == old
    assert not (tmp_path / "Aperture.AppImage.previous").exists()


@posix_only
def test_tarball_update_swaps_folders(tmp_path):
    started, marker = tmp_path / "started.log", tmp_path / "launched"
    target, new = tmp_path / "aperture", tmp_path / ".aperture-update"
    target.mkdir()
    new.mkdir()
    fake_app(target / "aperture", started, None)
    (target / "old.txt").touch()
    fake_app(new / "aperture", started, marker)

    result = run_updater(tmp_path, new, target, "tarball", marker, timeout="5")

    assert result.returncode == 0, result.stdout + result.stderr
    assert not (target / "old.txt").exists() and (target / "aperture").exists()
    assert not (tmp_path / "aperture.previous").exists()
