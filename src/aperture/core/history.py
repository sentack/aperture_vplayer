"""Recently opened files and per-file resume points, persisted as one JSON file."""

from __future__ import annotations

import json
import logging
import os
import tempfile
from pathlib import Path

log = logging.getLogger(__name__)

RECENT_LIMIT = 10
RESUME_LIMIT = 200
# Positions this close to the start are not worth resuming.
MIN_RESUME_MS = 5_000
# Within this much of the end (or 2% of the length, whichever is larger) counts as finished.
END_MARGIN_MS = 10_000


def _key(path: Path | str) -> str:
    return str(Path(path).absolute())


class History:
    """In-memory when `path` is None; otherwise loads from and saves to `path`."""

    def __init__(self, path: Path | None = None) -> None:
        self._path = path
        self._recent: list[str] = []
        self._resume: dict[str, int] = {}  # insertion order = least recently updated first
        if path is not None:
            self._load(path)

    # --- recent ------------------------------------------------------------

    @property
    def recent(self) -> list[Path]:
        return [Path(p) for p in self._recent]

    def touch(self, path: Path | str) -> None:
        """Move `path` to the front of the recent list."""
        key = _key(path)
        if key in self._recent:
            self._recent.remove(key)
        self._recent.insert(0, key)
        del self._recent[RECENT_LIMIT:]

    def remove_recent(self, path: Path | str) -> None:
        key = _key(path)
        if key in self._recent:
            self._recent.remove(key)

    def clear_recent(self) -> None:
        self._recent.clear()

    # --- resume ------------------------------------------------------------

    def resume_point(self, path: Path | str) -> int | None:
        return self._resume.get(_key(path))

    def remember_position(self, path: Path | str, position_ms: int, duration_ms: int) -> None:
        """Store where playback stopped, or forget it if near the start or the end."""
        key = _key(path)
        self._resume.pop(key, None)
        if position_ms < MIN_RESUME_MS:
            return
        if duration_ms > 0 and duration_ms - position_ms < max(END_MARGIN_MS, duration_ms // 50):
            return
        self._resume[key] = position_ms
        while len(self._resume) > RESUME_LIMIT:
            del self._resume[next(iter(self._resume))]

    def forget_position(self, path: Path | str) -> None:
        self._resume.pop(_key(path), None)

    # --- persistence -------------------------------------------------------

    def save(self) -> None:
        if self._path is None:
            return
        data = {"version": 1, "recent": self._recent, "resume": self._resume}
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            fd, tmp = tempfile.mkstemp(dir=self._path.parent, prefix=".history-", suffix=".json")
        except OSError:
            log.warning("could not save history to %s", self._path, exc_info=True)
            return
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
            os.replace(tmp, self._path)
        except OSError:
            log.warning("could not save history to %s", self._path, exc_info=True)
            Path(tmp).unlink(missing_ok=True)

    def _load(self, path: Path) -> None:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return
        except (OSError, ValueError):
            log.warning("ignoring unreadable history at %s", path, exc_info=True)
            return
        if not isinstance(data, dict):
            return
        recent = data.get("recent", [])
        resume = data.get("resume", {})
        if isinstance(recent, list):
            self._recent = [p for p in recent if isinstance(p, str)][:RECENT_LIMIT]
        if isinstance(resume, dict):
            self._resume = {
                k: v for k, v in resume.items() if isinstance(k, str) and type(v) is int and v > 0
            }
