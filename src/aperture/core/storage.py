"""Small JSON files in the app-data folder: never crash on bad data, never leave half writes."""

from __future__ import annotations

import json
import logging
import os
import tempfile
from pathlib import Path

log = logging.getLogger(__name__)


def read_json(path: Path) -> object | None:
    """Parsed content, or None when missing or unreadable."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except (OSError, ValueError):
        log.warning("ignoring unreadable %s", path, exc_info=True)
        return None


def write_json(path: Path, data: object) -> None:
    """Write via a temp file and rename, so readers see the old or the new file, never a mix."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.stem}-", suffix=".json")
    except OSError:
        log.warning("could not save %s", path, exc_info=True)
        return
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        os.replace(tmp, path)
    except OSError:
        log.warning("could not save %s", path, exc_info=True)
        Path(tmp).unlink(missing_ok=True)
