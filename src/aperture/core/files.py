"""Turning user-supplied paths (dialog, drop, command line) into a playable list."""

from __future__ import annotations

import logging
import re
from collections.abc import Iterable
from pathlib import Path

from aperture.core.formats import is_media
from aperture.core.media import is_url
from aperture.core.playlist_file import is_playlist, read_playlist

log = logging.getLogger(__name__)

_DIGITS = re.compile(r"(\d+)")


def natural_key(path: Path) -> list[object]:
    """Sort key placing `Episode 2` before `Episode 10`, case-insensitively."""
    return [int(part) if part.isdigit() else part.casefold() for part in _DIGITS.split(path.name)]


def expand_paths(
    paths: Iterable[Path | str], missing: list[Path] | None = None
) -> list[Path | str]:
    """Files pass through untouched; a folder contributes its media files in natural order;
    a playlist file contributes its entries.

    Folders are not searched recursively, nor playlists inside playlists. Missing paths are
    dropped; playlist entries that are gone are added to `missing`, for a notice.
    """
    result: list[Path | str] = []
    for item in paths:
        if is_url(item):
            result.append(str(item))
            continue
        path = Path(item)
        entries = read_playlist(path) if is_playlist(path) and path.is_file() else None
        if entries is not None:
            for entry in entries:
                if is_url(entry) or (Path(entry).is_file() and not is_playlist(entry)):
                    result.append(entry)
                elif missing is not None:
                    missing.append(Path(entry))
        elif path.is_file():
            result.append(path)
        elif path.is_dir():
            try:
                videos = [child for child in path.iterdir() if child.is_file() and is_media(child)]
            except OSError:
                log.warning("cannot list %s", path, exc_info=True)
                continue
            result.extend(sorted(videos, key=natural_key))
    return result
