"""Playlist files: Aperture's own `.aplaylist`, plus `.m3u` / `.m3u8` from other players.

An `.aplaylist` is a UTF-8 extended M3U list, so any M3U reader can open it if renamed.
Entries inside the playlist's folder are stored relative to it, so a folder of videos with
its playlist can be moved or copied as a whole; others are stored as absolute paths.
"""

from __future__ import annotations

import os
from collections.abc import Iterable, Mapping
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import url2pathname

from aperture.core.formats import PLAYLIST_EXTENSIONS
from aperture.core.media import display_name, is_url

PLAYLIST_EXTENSION = ".aplaylist"
PLAYLIST_MIME = "application/x-aperture-playlist"
MAX_PLAYLIST_BYTES = 8 * 1024 * 1024


def is_playlist(path: Path | str) -> bool:
    return not is_url(path) and Path(path).suffix.lower() in PLAYLIST_EXTENSIONS


def format_playlist(
    items: Iterable[Path | str], folder: Path, durations: Mapping[str, int] | None = None
) -> str:
    """Extended M3U text for `items`, to be saved in `folder`. Durations are in ms."""
    lines = ["#EXTM3U"]
    for item in items:
        seconds = (durations or {}).get(str(item))
        length = round(seconds / 1000) if seconds else -1
        lines.append(f"#EXTINF:{length},{display_name(item)}")
        lines.append(_entry(item, folder))
    return "\n".join(lines) + "\n"


def parse_playlist(text: str, folder: Path) -> list[Path | str] | None:
    """Entries of a playlist read from `folder`; None when it is an HLS stream instead.

    HLS media playlists share the .m3u8 extension; their #EXT-X- tags give them away, and
    the player then plays the file as the stream it is.
    """
    if "#EXT-X-" in text:
        return None
    entries: list[Path | str] = []
    for raw in text.splitlines():
        line = raw.strip().lstrip("﻿")
        if not line or line.startswith("#"):
            continue
        if is_url(line):
            entries.append(line)
            continue
        if line.lower().startswith("file://"):
            line = url2pathname(urlsplit(line).path)
        path = Path(line.replace("\\", os.sep) if os.sep != "\\" else line)
        entries.append(path if path.is_absolute() else folder / path)
    return entries


def read_playlist(path: Path) -> list[Path | str] | None:
    """Entries of the playlist file at `path`; None for HLS streams or unreadable files."""
    try:
        if path.stat().st_size > MAX_PLAYLIST_BYTES:
            return None
        data = path.read_bytes()
    except OSError:
        return None
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = data.decode("latin-1")  # plain .m3u from older players
    return parse_playlist(text, path.parent)


def write_playlist(
    path: Path, items: Iterable[Path | str], durations: Mapping[str, int] | None = None
) -> None:
    """Write atomically, so a failed save never leaves half a playlist behind."""
    text = format_playlist(items, path.parent, durations)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(text, encoding="utf-8")
    os.replace(temporary, path)


def _entry(item: Path | str, folder: Path) -> str:
    if is_url(item):
        return str(item)
    path = Path(item)
    try:
        return path.relative_to(folder).as_posix()
    except ValueError:
        return str(path)


def keep_missing(entries: list, loaded: list, current: list) -> list:
    """What to write back into a playlist file: `current`, with the file's other entries kept.

    `entries` is what the file lists, `loaded` what of it opened (files that exist), and
    `current` the playlist now. Entries that didn't open (a drive not plugged in, a nested
    playlist) were never in the playlist to remove, so they stay where they were: after the
    nearest entry before them that is still in the playlist.
    """
    opened = {str(item) for item in loaded}
    kept = {str(item) for item in current}
    following: dict[str | None, list] = {}
    before = None
    for entry in entries:
        if str(entry) not in opened:
            following.setdefault(before, []).append(entry)
        elif str(entry) in kept:
            before = str(entry)
    result = list(following.pop(None, []))
    for item in current:
        result.append(item)
        result.extend(following.pop(str(item), []))
    return result
