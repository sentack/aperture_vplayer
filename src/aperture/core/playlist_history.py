"""Recently used playlists, newest first, persisted as one JSON file. No Qt.

A playlist is remembered when it is saved or opened as a file, and when a playlist of two
or more items is replaced, cleared or still open at quit, so it can be brought back later.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from aperture.core.media import Source, display_name, is_url
from aperture.core.storage import read_json, write_json

PLAYLIST_HISTORY_LIMIT = 12
MIN_REMEMBERED_ITEMS = 2  # a single file is the Recent list's job


@dataclass(frozen=True, slots=True)
class PlaylistEntry:
    name: str
    items: tuple[str, ...]
    used: float  # Unix time
    saved: str = ""  # the playlist file it was saved as or opened from, if any
    durations: dict[str, int] = field(default_factory=dict, compare=False)  # ms, by item


def default_name(items: list[Source]) -> str:
    """The shared folder's name, else "First item + 3 more"."""
    folders = {Path(item).parent for item in items if not is_url(item)}
    if len(folders) == 1 and not any(is_url(item) for item in items):
        folder = folders.pop()
        if folder.name:
            return folder.name
    first = display_name(items[0]) if items else "Playlist"
    return f"{first} + {len(items) - 1} more" if len(items) > 1 else first


class PlaylistHistory:
    """In-memory when `path` is None; otherwise loads from and saves to `path`."""

    def __init__(self, path: Path | None = None) -> None:
        self._path = path
        self._entries: list[PlaylistEntry] = []
        data = read_json(path) if path is not None else None
        if isinstance(data, dict) and isinstance(data.get("playlists"), list):
            for raw in data["playlists"][:PLAYLIST_HISTORY_LIMIT]:
                entry = _entry(raw)
                if entry is not None:
                    self._entries.append(entry)

    @property
    def entries(self) -> list[PlaylistEntry]:
        return list(self._entries)

    def record(
        self,
        items: list[Source],
        now: float,
        name: str = "",
        saved: str = "",
        durations: dict[str, int] | None = None,
    ) -> bool:
        """Remember `items` as the newest playlist. False when there were too few to keep.

        The same items again move their entry to the front, keeping its saved file and
        name unless new ones are given.
        """
        keys = tuple(str(item) for item in items)
        if len(keys) < MIN_REMEMBERED_ITEMS and not saved:
            return False
        previous = next((e for e in self._entries if e.items == keys), None)
        if previous is not None:
            self._entries.remove(previous)
        known = dict(previous.durations) if previous else {}
        known.update({k: v for k, v in (durations or {}).items() if k in keys and v > 0})
        self._entries.insert(
            0,
            PlaylistEntry(
                name=name or (previous.name if previous else default_name(list(items))),
                items=keys,
                used=now,
                saved=saved or (previous.saved if previous else ""),
                durations=known,
            ),
        )
        del self._entries[PLAYLIST_HISTORY_LIMIT:]
        return True

    def remove(self, index: int) -> None:
        if 0 <= index < len(self._entries):
            del self._entries[index]

    def clear(self) -> None:
        self._entries.clear()

    def save(self) -> None:
        if self._path is None:
            return
        playlists = [
            {
                "name": e.name,
                "items": list(e.items),
                "used": e.used,
                "saved": e.saved,
                "durations": e.durations,
            }
            for e in self._entries
        ]
        write_json(self._path, {"version": 1, "playlists": playlists})


def _entry(raw: object) -> PlaylistEntry | None:
    if not isinstance(raw, dict):
        return None
    items = raw.get("items")
    if not isinstance(items, list) or not items or not all(isinstance(i, str) for i in items):
        return None
    used = raw.get("used")
    durations = raw.get("durations")
    return PlaylistEntry(
        name=str(raw.get("name") or default_name(list(items))),
        items=tuple(items),
        used=float(used) if isinstance(used, int | float) else 0.0,
        saved=str(raw.get("saved") or ""),
        durations={
            k: int(v)
            for k, v in (durations if isinstance(durations, dict) else {}).items()
            if isinstance(k, str) and isinstance(v, int | float) and v > 0
        },
    )
