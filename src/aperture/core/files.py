"""Turning user-supplied paths (dialog, drop, command line) into a playable list."""

from __future__ import annotations

import logging
import re
from collections.abc import Iterable
from pathlib import Path

from aperture.core.formats import is_media

log = logging.getLogger(__name__)

_DIGITS = re.compile(r"(\d+)")


def natural_key(path: Path) -> list[object]:
    """Sort key placing `Episode 2` before `Episode 10`, case-insensitively."""
    return [int(part) if part.isdigit() else part.casefold() for part in _DIGITS.split(path.name)]


def expand_paths(paths: Iterable[Path | str]) -> list[Path]:
    """Files pass through untouched; a folder contributes its video and audio files in natural order.

    Folders are not searched recursively. Missing paths are dropped.
    """
    result: list[Path] = []
    for path in map(Path, paths):
        if path.is_file():
            result.append(path)
        elif path.is_dir():
            try:
                videos = [child for child in path.iterdir() if child.is_file() and is_media(child)]
            except OSError:
                log.warning("cannot list %s", path, exc_info=True)
                continue
            result.extend(sorted(videos, key=natural_key))
    return result
