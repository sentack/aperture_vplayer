"""Lyrics for audio playback: LRC parsing and writing, sidecar discovery, current-line lookup.

Synced lyrics use LRC: `[mm:ss.xx]line`, several stamps per line allowed, `[offset:±ms]`
honoured, other `[tag:value]` headers ignored. Text without stamps is plain, unsynced lyrics.
"""

from __future__ import annotations

import bisect
import logging
import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

log = logging.getLogger(__name__)

LYRICS_EXTENSIONS = (".lrc", ".txt")  # preference order for sidecar files

_STAMP = re.compile(r"\[(\d{1,3}):(\d{2})(?:[.:](\d{1,3}))?\]")
_HEADER = re.compile(r"\[([A-Za-z]+):([^\]]*)\]")


@dataclass(frozen=True, slots=True)
class LyricLine:
    time_ms: int | None  # None for unsynced lyrics
    text: str


def _stamp_ms(match: re.Match[str]) -> int:
    minutes, seconds, fraction = match[1], match[2], match[3] or "0"
    return (int(minutes) * 60 + int(seconds)) * 1000 + int(fraction.ljust(3, "0")[:3])


def parse_lyrics(text: str) -> list[LyricLine]:
    """Synced lines sorted by time if any line carries a stamp, else plain lines in order."""
    offset = 0
    synced: list[LyricLine] = []
    plain: list[LyricLine] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        stamps, pos = [], 0
        while match := _STAMP.match(line, pos):
            stamps.append(_stamp_ms(match))
            pos = match.end()
        if stamps:
            words = line[pos:].strip()
            synced.extend(LyricLine(ms, words) for ms in stamps)
            continue
        header = _HEADER.fullmatch(line)
        if header:
            if header[1].lower() == "offset":
                try:
                    offset = int(header[2].strip())
                except ValueError:
                    pass
            continue
        plain.append(LyricLine(None, line))
    if not synced:
        return plain
    # A positive LRC offset shows every line that many milliseconds earlier.
    shifted = (LyricLine(max(0, line.time_ms - offset), line.text) for line in synced)
    return sorted(shifted, key=lambda line: line.time_ms)


def format_stamp(ms: int) -> str:
    centis = max(0, ms) // 10
    minutes, centis = divmod(centis, 6000)
    return f"[{minutes:02d}:{centis // 100:02d}.{centis % 100:02d}]"


def format_lrc(lines: Iterable[LyricLine], tags: dict[str, str] | None = None) -> str:
    """LRC text for `lines`; unsynced lines are written without a stamp."""
    out = [f"[{key}:{value}]" for key, value in (tags or {}).items() if value]
    for line in lines:
        out.append(line.text if line.time_ms is None else f"{format_stamp(line.time_ms)}{line.text}")
    return "\n".join(out) + "\n"


def find_lyrics(audio: Path) -> Path | None:
    """`<stem>.lrc`, else `<stem>.txt`, next to `audio` (any case)."""
    stem = audio.stem.casefold()
    try:
        candidates = {
            p.suffix.lower(): p
            for p in audio.parent.iterdir()
            if p.stem.casefold() == stem and p.suffix.lower() in LYRICS_EXTENSIONS
        }
    except OSError:
        log.warning("cannot list %s", audio.parent, exc_info=True)
        return None
    return next((candidates[ext] for ext in LYRICS_EXTENSIONS if ext in candidates), None)


class LyricsTrack:
    """Which line is being sung at a position. Unsynced lyrics never have a current line."""

    def __init__(self, lines: Iterable[LyricLine]) -> None:
        self.lines = list(lines)
        self.synced = bool(self.lines) and all(line.time_ms is not None for line in self.lines)
        self._times = [line.time_ms for line in self.lines] if self.synced else []

    def index_at(self, position_ms: int) -> int:
        """Index of the last line started at `position_ms`, -1 before the first one."""
        return bisect.bisect_right(self._times, position_ms) - 1
