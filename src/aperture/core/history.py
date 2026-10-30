"""Recently opened files and per-file resume points, persisted as one JSON file."""

from __future__ import annotations

from pathlib import Path

from aperture.core.media import Source, is_url
from aperture.core.storage import read_json, write_json

RECENT_LIMIT = 10
RESUME_LIMIT = 200
# Positions this close to the start are not worth resuming.
MIN_RESUME_MS = 5_000
# Within this much of the end (or 2% of the length, whichever is larger) counts as finished.
END_MARGIN_MS = 10_000


def _key(path: Source) -> str:
    return path if is_url(path) else str(Path(path).absolute())


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
    def recent(self) -> list[Source]:
        return [p if is_url(p) else Path(p) for p in self._recent]

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
        write_json(self._path, {"version": 1, "recent": self._recent, "resume": self._resume})

    def _load(self, path: Path) -> None:
        data = read_json(path)
        if not isinstance(data, dict):
            return
        recent = data.get("recent", [])
        resume = data.get("resume", {})
        # Keys go through _key() so files written elsewhere still match lookups here.
        if isinstance(recent, list):
            self._recent = list(dict.fromkeys(_key(p) for p in recent if isinstance(p, str)))
            del self._recent[RECENT_LIMIT:]
        if isinstance(resume, dict):
            self._resume = {
                _key(k): v
                for k, v in resume.items()
                if isinstance(k, str) and type(v) is int and v > 0
            }
