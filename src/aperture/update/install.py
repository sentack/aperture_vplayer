"""How this copy of Aperture was installed, which decides how (or whether) it updates itself."""

from __future__ import annotations

import os
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

# Kinds that replace themselves in place; a macOS app opens the new disk image instead.
SELF_UPDATING = frozenset({"windows-installer", "appimage", "tarball"})
DOWNLOADABLE = SELF_UPDATING | {"macos-dmg"}
# Folders that belong to a package manager: updating there would fight its bookkeeping.
_MANAGED_PREFIXES = ("/usr/", "/snap/", "/app/", "/nix/store/", "/var/lib/flatpak/")


@dataclass(frozen=True, slots=True)
class Installation:
    kind: str  # windows-installer, macos-dmg, appimage, tarball, managed, portable, source
    target: Path | None  # the file or folder an update replaces
    hint: str = ""  # shown instead of "Update now" when this kind cannot update itself

    @property
    def self_updates(self) -> bool:
        return self.kind in SELF_UPDATING

    @property
    def downloads(self) -> bool:
        return self.kind in DOWNLOADABLE


def detect(
    platform: str = sys.platform,
    frozen: bool | None = None,
    executable: str = sys.executable,
    environ: Mapping[str, str] = os.environ,
) -> Installation:
    frozen = getattr(sys, "frozen", False) if frozen is None else frozen
    if not frozen:
        return Installation("source", None, "Running from source: update with git pull.")
    exe = Path(executable)
    if platform == "win32":
        if (exe.parent / "unins000.exe").is_file():
            return Installation("windows-installer", exe.parent)
        return Installation("portable", None, "Portable copy: download the new version below.")
    if platform == "darwin":
        app = next((p for p in exe.parents if p.suffix == ".app"), None)
        if app is not None:
            return Installation("macos-dmg", app)
        return Installation("portable", None, "Download the new version below.")
    appimage = environ.get("APPIMAGE")
    if appimage:
        return Installation("appimage", Path(appimage))
    if exe.as_posix().startswith(_MANAGED_PREFIXES):  # as_posix: same answer on any host
        return Installation("managed", None, "Installed by your package manager: update there.")
    return Installation("tarball", exe.parent)
