"""Version and release date of this build. Release builds get a stamped build_info.json."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

from aperture import __version__
from aperture.core.storage import read_json

BUILD_INFO = Path(__file__).parent / "resources" / "build_info.json"


@dataclass(frozen=True, slots=True)
class BuildInfo:
    version: str
    released: date | None  # None for builds that were not made by the release workflow
    commit: str = ""


def load_build_info(path: Path = BUILD_INFO) -> BuildInfo:
    data = read_json(path) if path.is_file() else None
    released, commit = None, ""
    if isinstance(data, dict):
        try:
            released = date.fromisoformat(str(data.get("date", "")))
        except ValueError:
            released = None
        commit = str(data.get("commit", ""))[:12]
    return BuildInfo(__version__, released, commit)
