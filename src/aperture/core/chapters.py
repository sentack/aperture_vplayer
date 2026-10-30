"""Chapter markers read straight from the file: Matroska/WebM and MP4.

Qt Multimedia does not expose chapters, so this reads the two common layouts itself:
Matroska `Chapters` (found directly or through the `SeekHead`) and the MP4 `chpl` atom that
FFmpeg, HandBrake and most tools write. Unreadable or chapterless files give an empty list.
"""

from __future__ import annotations

import bisect
import logging
import struct
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO

log = logging.getLogger(__name__)

MAX_CHAPTERS_BYTES = 4 << 20  # a Chapters element bigger than this is not chapters


@dataclass(frozen=True, slots=True)
class Chapter:
    start_ms: int
    title: str


def read_chapters(path: Path) -> list[Chapter]:
    suffix = path.suffix.lower()
    try:
        with path.open("rb") as f:
            if suffix in (".mkv", ".mka", ".webm", ".mk3d"):
                chapters = _matroska(f)
            elif suffix in (".mp4", ".m4v", ".m4a", ".m4b", ".mov"):
                chapters = _mp4(f)
            else:
                return []
    except (OSError, ValueError, struct.error):
        log.debug("no readable chapters in %s", path, exc_info=True)
        return []
    unique = {c.start_ms: c for c in sorted(chapters, key=lambda c: c.start_ms)}
    return list(unique.values())


def chapter_at(chapters: Sequence[Chapter], position_ms: int) -> int:
    """Index of the chapter playing at `position_ms`, -1 before the first one."""
    return bisect.bisect_right([c.start_ms for c in chapters], position_ms) - 1


# --- Matroska -----------------------------------------------------------------------------

_EBML, _SEGMENT, _SEEK_HEAD, _SEEK = 0x1A45DFA3, 0x18538067, 0x114D9B74, 0x4DBB
_SEEK_ID, _SEEK_POSITION, _CLUSTER = 0x53AB, 0x53AC, 0x1F43B675
_CHAPTERS, _EDITION, _ATOM = 0x1043A770, 0x45B9, 0xB6
_TIME_START, _HIDDEN, _DISPLAY, _STRING = 0x91, 0x98, 0x80, 0x85
_UNKNOWN = object()


def _vint(f: BinaryIO, keep_marker: bool) -> int | object | None:
    first = f.read(1)
    if not first:
        return None
    byte = first[0]
    length = next((n for n in range(8) if byte & (0x80 >> n)), None)
    if length is None:
        raise ValueError("invalid EBML length")
    rest = f.read(length)
    if len(rest) < length:
        raise ValueError("truncated EBML number")
    value = byte if keep_marker else byte & (0xFF >> (length + 1))
    for b in rest:
        value = (value << 8) | b
    if not keep_marker and value == (1 << (7 * (length + 1))) - 1:
        return _UNKNOWN  # "size unknown", used by live streams
    return value


def _element(f: BinaryIO) -> tuple[int, object] | None:
    element_id = _vint(f, keep_marker=True)
    if element_id is None:
        return None
    size = _vint(f, keep_marker=False)
    if size is None:
        raise ValueError("truncated EBML element")
    return element_id, size


def _children(data: bytes):
    """(id, payload) for each element in an in-memory EBML block."""
    from io import BytesIO

    stream = BytesIO(data)
    while (header := _element(stream)) is not None:
        element_id, size = header
        if size is _UNKNOWN:
            return
        yield element_id, stream.read(size)


def _uint(data: bytes) -> int:
    return int.from_bytes(data, "big") if data else 0


def _matroska(f: BinaryIO) -> list[Chapter]:
    header = _element(f)
    if header is None or header[0] != _EBML or header[1] is _UNKNOWN:
        return []
    f.seek(header[1], 1)
    segment = _element(f)
    if segment is None or segment[0] != _SEGMENT:
        return []
    start = f.tell()
    end = None if segment[1] is _UNKNOWN else start + segment[1]
    seek_to = None
    while end is None or f.tell() < end:
        child = _element(f)
        if child is None:
            break
        element_id, size = child
        if element_id == _CHAPTERS and size is not _UNKNOWN and size <= MAX_CHAPTERS_BYTES:
            return _matroska_chapters(f.read(size))
        if element_id == _SEEK_HEAD and size is not _UNKNOWN:
            for seek_id, seek in _children(f.read(size)):
                fields = dict(_children(seek)) if seek_id == _SEEK else {}
                if _uint(fields.get(_SEEK_ID, b"")) == _CHAPTERS and _SEEK_POSITION in fields:
                    seek_to = start + _uint(fields[_SEEK_POSITION])
            continue
        if element_id == _CLUSTER or size is _UNKNOWN:
            break  # media data from here on: chapters, if any, are wherever SeekHead said
        f.seek(size, 1)
    if seek_to is None:
        return []
    f.seek(seek_to)
    child = _element(f)
    if child is None or child[0] != _CHAPTERS or child[1] is _UNKNOWN:
        return []
    return _matroska_chapters(f.read(min(child[1], MAX_CHAPTERS_BYTES)))


def _matroska_chapters(data: bytes) -> list[Chapter]:
    """Chapters of the first edition, skipping hidden ones and nested sub-chapters."""
    for element_id, edition in _children(data):
        if element_id != _EDITION:
            continue
        chapters = []
        for atom_id, atom in _children(edition):
            if atom_id != _ATOM:
                continue
            fields = list(_children(atom))
            values = dict(fields)
            if _uint(values.get(_HIDDEN, b"")):
                continue
            start_ns = _uint(values.get(_TIME_START, b""))
            title = ""
            for field_id, payload in fields:
                if field_id == _DISPLAY:
                    title = dict(_children(payload)).get(_STRING, b"").decode("utf-8", "replace")
                    break
            chapters.append(Chapter(start_ns // 1_000_000, title.strip()))
        return chapters
    return []


# --- MP4 ----------------------------------------------------------------------------------


def _atoms(f: BinaryIO, end: int):
    """(type, payload start, payload end) for each atom between here and `end`."""
    while f.tell() + 8 <= end:
        start = f.tell()
        size, kind = struct.unpack(">I4s", f.read(8))
        if size == 1:
            size = struct.unpack(">Q", f.read(8))[0]
        elif size == 0:
            size = end - start
        if size < 8 or start + size > end:
            return
        yield kind, f.tell(), start + size
        f.seek(start + size)


def _find(f: BinaryIO, end: int, path: tuple[bytes, ...]) -> tuple[int, int] | None:
    for kind, body, body_end in _atoms(f, end):
        if kind == path[0]:
            if len(path) == 1:
                return body, body_end
            f.seek(body)
            return _find(f, body_end, path[1:])
    return None


def _mp4(f: BinaryIO) -> list[Chapter]:
    f.seek(0, 2)
    size = f.tell()
    f.seek(0)
    found = _find(f, size, (b"moov", b"udta", b"chpl"))
    if found is None:
        return []
    start, end = found
    f.seek(start)
    data = f.read(min(end - start, MAX_CHAPTERS_BYTES))
    version, pos = data[0], 4  # version + 3 flag bytes
    if version:
        pos += 4  # reserved word in version 1
    count, pos = data[pos], pos + 1
    chapters = []
    for _ in range(count):
        start_100ns = struct.unpack_from(">Q", data, pos)[0]
        length = data[pos + 8]
        title = data[pos + 9 : pos + 9 + length].decode("utf-8", "replace")
        chapters.append(Chapter(start_100ns // 10_000, title.strip()))
        pos += 9 + length
    return chapters
