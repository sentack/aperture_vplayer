"""Is Aperture the default video player, and can it become one? Per operating system.

- Linux: `xdg-mime`. An AppImage first gets a desktop entry, so there is something to point at.
- Windows: reads UserChoice. Windows 10+ forbids setting it programmatically, so claiming
  opens Aperture's page in Settings → Default apps (registered by the installer).
- macOS: LaunchServices through ctypes.
"""

from __future__ import annotations

import logging
import os
import re
import shlex
import shutil
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

log = logging.getLogger(__name__)

APP_ID = "io.github.sentack.Aperture"
DESKTOP_FILE = f"{APP_ID}.desktop"
# Same list as packaging/linux/io.github.sentack.Aperture.desktop (tests keep them equal).
MIME_TYPES = (
    "video/3gpp", "video/mp2t", "video/mp4", "video/mpeg", "video/ogg", "video/quicktime",
    "video/webm", "video/x-flv", "video/x-m4v", "video/x-matroska", "video/x-ms-wmv",
    "video/x-msvideo",
)  # fmt: skip
WINDOWS_PROG_IDS = ("Aperture.Video", "Applications\\aperture.exe")
# Settings → Default apps → Aperture; the name matches RegisteredApplications in the installer.
WINDOWS_DEFAULT_APPS = "ms-settings:defaultapps?registeredAppUser=Aperture"
MAC_CONTENT_TYPES = (
    "public.movie", "public.mpeg-4", "com.apple.quicktime-movie", "public.avi",
    "org.matroska.mkv", "org.webmproject.webm",
)  # fmt: skip

Runner = Callable[..., subprocess.CompletedProcess]

DONE, OPENED_SETTINGS, FAILED = "done", "settings", "failed"


# --- Linux --------------------------------------------------------------------------------


def _data_home() -> Path:
    return Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share")


def _desktop_entry_installed() -> bool:
    system = os.environ.get("XDG_DATA_DIRS") or "/usr/local/share:/usr/share"
    dirs = [_data_home(), *(Path(d) for d in system.split(":") if d)]
    return any((d / "applications" / DESKTOP_FILE).is_file() for d in dirs)


def linux_status(run: Runner = subprocess.run) -> bool | None:
    try:
        result = run(
            ["xdg-mime", "query", "default", "video/mp4"], capture_output=True, text=True, timeout=5
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return result.returncode == 0 and result.stdout.strip() == DESKTOP_FILE


def linux_can_claim() -> bool:
    return shutil.which("xdg-mime") is not None and (
        _desktop_entry_installed() or bool(os.environ.get("APPIMAGE"))
    )


def install_appimage_entry(appimage: Path, icon_svg: Path) -> Path:
    """Desktop entry and icon for a portable AppImage, so menus and xdg-mime can find it."""
    apps = _data_home() / "applications"
    icons = _data_home() / "icons" / "hicolor" / "scalable" / "apps"
    apps.mkdir(parents=True, exist_ok=True)
    icons.mkdir(parents=True, exist_ok=True)
    if icon_svg.is_file():
        shutil.copyfile(icon_svg, icons / f"{APP_ID}.svg")
    entry = apps / DESKTOP_FILE
    entry.write_text(
        "[Desktop Entry]\n"
        "Type=Application\n"
        "Name=Aperture\n"
        "GenericName=Video Player\n"
        # Desktop entries are POSIX-only; as_posix() also keeps tests stable on Windows.
        f"Exec=\"{appimage.as_posix()}\" %F\n"
        f"Icon={APP_ID}\n"
        "Terminal=false\n"
        "Categories=AudioVideo;Video;Player;Qt;\n"
        f"MimeType={';'.join(MIME_TYPES)};\n",
        encoding="utf-8",
    )
    return entry


_APPIMAGE_VERSION = re.compile(r"Aperture-(\d+\.\d+\.\d+(?:-[0-9A-Za-z.]+)?)-x86_64\.AppImage$")


def appimage_version(path: Path) -> str | None:
    """Version in a release file name such as `Aperture-0.3.0-x86_64.AppImage`."""
    match = _APPIMAGE_VERSION.search(path.name)
    return match[1] if match else None


def entry_target() -> Path | None:
    """The program our desktop entry launches, from its Exec line."""
    entry = _data_home() / "applications" / DESKTOP_FILE
    try:
        text = entry.read_text(encoding="utf-8")
    except OSError:
        return None
    match = re.search(r"^Exec=(.*)$", text, re.M)
    if match is None:
        return None
    try:
        words = shlex.split(match[1])
    except ValueError:
        return None
    return Path(words[0]) if words else None


def refresh_default_appimage(
    current: Path, version: str, icon_svg: Path, run: Runner = subprocess.run
) -> Path | None:
    """If Aperture is the default player but its entry opens an older or missing AppImage,
    point the entry at `current` (this AppImage) instead. Returns the path it replaced.

    The default-player choice names the desktop entry, not a file, so rewriting the entry's
    Exec line moves every "open with default" over without asking the user again. An older
    AppImage whose version cannot be read from its name is left alone.
    """
    from aperture.core.release import is_newer

    target = entry_target()
    if target is None or target == current or linux_status(run) is not True:
        return None
    if target.exists():
        old = appimage_version(target)
        if old is None or not is_newer(version, old):
            return None
    try:
        install_appimage_entry(current, icon_svg)
        apps = str(_data_home() / "applications")
        run(["update-desktop-database", apps], capture_output=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        log.warning("could not update the desktop entry", exc_info=True)
        return None
    return target


def linux_claim(icon_svg: Path, run: Runner = subprocess.run) -> str:
    try:
        appimage = os.environ.get("APPIMAGE")
        if not _desktop_entry_installed() and appimage:
            install_appimage_entry(Path(appimage), icon_svg)
            apps = str(_data_home() / "applications")
            run(["update-desktop-database", apps], capture_output=True, timeout=10)
        result = run(
            ["xdg-mime", "default", DESKTOP_FILE, *MIME_TYPES], capture_output=True, timeout=10
        )
    except (OSError, subprocess.SubprocessError):
        log.warning("could not set the default player", exc_info=True)
        return FAILED
    return DONE if result.returncode == 0 and linux_status(run) else FAILED


# --- Windows ------------------------------------------------------------------------------


def windows_status() -> bool | None:
    try:
        import winreg

        key = r"Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\.mp4\UserChoice"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key) as handle:
            prog_id, _ = winreg.QueryValueEx(handle, "ProgId")
    except FileNotFoundError:
        return False  # never chosen: the Windows default (Films & TV / Media Player) applies
    except (ImportError, OSError):
        return None
    return prog_id in WINDOWS_PROG_IDS


def windows_can_claim() -> bool:
    if not getattr(sys, "frozen", False):
        return False
    try:
        import winreg

        for root in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
            try:
                winreg.CloseKey(winreg.OpenKey(root, r"Software\Classes\Aperture.Video"))
                return True
            except FileNotFoundError:
                continue
    except (ImportError, OSError):
        pass
    return False


def windows_claim() -> str:
    try:
        os.startfile(WINDOWS_DEFAULT_APPS)  # type: ignore[attr-defined]
    except OSError:
        log.warning("could not open Default apps", exc_info=True)
        return FAILED
    return OPENED_SETTINGS


# --- macOS --------------------------------------------------------------------------------


def _mac_services():
    import ctypes

    frameworks = "/System/Library/Frameworks"
    cf = ctypes.cdll.LoadLibrary(f"{frameworks}/CoreFoundation.framework/CoreFoundation")
    ls = ctypes.cdll.LoadLibrary(f"{frameworks}/CoreServices.framework/CoreServices")
    cf.CFStringCreateWithCString.restype = ctypes.c_void_p
    cf.CFStringCreateWithCString.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_uint32]
    cf.CFStringGetCString.restype = ctypes.c_bool
    cf.CFStringGetCString.argtypes = [
        ctypes.c_void_p, ctypes.c_char_p, ctypes.c_long, ctypes.c_uint32,
    ]  # fmt: skip
    cf.CFRelease.argtypes = [ctypes.c_void_p]
    ls.LSCopyDefaultRoleHandlerForContentType.restype = ctypes.c_void_p
    ls.LSCopyDefaultRoleHandlerForContentType.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
    ls.LSSetDefaultRoleHandlerForContentType.restype = ctypes.c_int32
    ls.LSSetDefaultRoleHandlerForContentType.argtypes = [
        ctypes.c_void_p, ctypes.c_uint32, ctypes.c_void_p,
    ]  # fmt: skip
    return ctypes, cf, ls


_UTF8 = 0x08000100
_ROLES_ALL = 0xFFFFFFFF


def mac_status() -> bool | None:
    try:
        ctypes, cf, ls = _mac_services()
        content = cf.CFStringCreateWithCString(None, b"public.mpeg-4", _UTF8)
        handler = ls.LSCopyDefaultRoleHandlerForContentType(content, _ROLES_ALL)
        cf.CFRelease(content)
        if not handler:
            return False
        buffer = ctypes.create_string_buffer(256)
        ok = cf.CFStringGetCString(handler, buffer, len(buffer), _UTF8)
        cf.CFRelease(handler)
    except (OSError, AttributeError):
        return None
    return ok and buffer.value.decode().lower() == APP_ID.lower()


def mac_can_claim() -> bool:
    return getattr(sys, "frozen", False) and ".app/Contents/MacOS" in sys.executable


def mac_claim() -> str:
    try:
        _, cf, ls = _mac_services()
        bundle = cf.CFStringCreateWithCString(None, APP_ID.encode(), _UTF8)
        for uti in MAC_CONTENT_TYPES:
            content = cf.CFStringCreateWithCString(None, uti.encode(), _UTF8)
            ls.LSSetDefaultRoleHandlerForContentType(content, _ROLES_ALL, bundle)
            cf.CFRelease(content)
        cf.CFRelease(bundle)
    except (OSError, AttributeError):
        log.warning("could not set the default player", exc_info=True)
        return FAILED
    return DONE if mac_status() else FAILED


# --- dispatch -----------------------------------------------------------------------------


def status() -> bool | None:
    """True / False when known; None when this system cannot tell."""
    if sys.platform == "win32":
        return windows_status()
    if sys.platform == "darwin":
        return mac_status()
    return linux_status()


def can_claim() -> bool:
    if sys.platform == "win32":
        return windows_can_claim()
    if sys.platform == "darwin":
        return mac_can_claim()
    return linux_can_claim()


def claim(icon_svg: Path) -> str:
    """DONE, OPENED_SETTINGS (the user finishes in system settings) or FAILED."""
    if sys.platform == "win32":
        return windows_claim()
    if sys.platform == "darwin":
        return mac_claim()
    return linux_claim(icon_svg)
