"""External subtitle files: SRT / WebVTT parsing, sidecar discovery and cue lookup.

Cue text is emitted as Qt StyledText: only <b>, <i>, <u> survive, everything else is escaped.
"""

from __future__ import annotations

import bisect
import codecs
import html
import logging
import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from aperture.core.files import natural_key

log = logging.getLogger(__name__)

SUBTITLE_EXTENSIONS = frozenset({".srt", ".vtt"})

_STAMP = r"(?:\d+:)?\d{1,2}:\d{2}[.,]\d{3}"
_TIMING = re.compile(rf"(?P<start>{_STAMP})\s*-->\s*(?P<end>{_STAMP})")
_TAG = re.compile(r"<(?:/?[A-Za-z]|\d)[^>]*>")  # tags and VTT <00:01.500> stamps
_KEPT_TAG = re.compile(r"<(/?)([biu])(?:[.\s][^>]*)?>", re.IGNORECASE)
_ASS_OVERRIDE = re.compile(r"\{\\[^}]*\}")


@dataclass(frozen=True, slots=True)
class Cue:
    start_ms: int
    end_ms: int
    text: str


def _ms(stamp: str) -> int:
    *hours_minutes, rest = stamp.replace(",", ".").split(":")
    seconds, millis = rest.split(".")
    hours = int(hours_minutes[0]) if len(hours_minutes) == 2 else 0
    minutes = int(hours_minutes[-1])
    return ((hours * 60 + minutes) * 60 + int(seconds)) * 1000 + int(millis)


def _markup(line: str) -> str:
    line = _ASS_OVERRIDE.sub("", line)
    out, last = [], 0
    for match in _TAG.finditer(line):
        out.append(html.escape(line[last : match.start()], quote=False))
        kept = _KEPT_TAG.fullmatch(match.group())
        if kept:
            out.append(f"<{kept[1]}{kept[2].lower()}>")
        last = match.end()
    out.append(html.escape(line[last:], quote=False))
    return "".join(out).strip()


def parse_cues(text: str) -> list[Cue]:
    """Parse SRT or WebVTT. Headers, NOTE/STYLE blocks and cue settings are ignored."""
    cues = []
    for block in re.split(r"\n[ \t]*\n", text.replace("\r\n", "\n").replace("\r", "\n")):
        lines = block.split("\n")
        for i, line in enumerate(lines):
            timing = _TIMING.search(line)
            if timing:
                break
        else:
            continue
        body = [m for m in map(_markup, lines[i + 1 :]) if _TAG.sub("", m).strip()]
        start, end = _ms(timing["start"]), _ms(timing["end"])
        if body and end > start:
            cues.append(Cue(start, end, "<br>".join(body)))
    cues.sort(key=lambda cue: cue.start_ms)
    return cues


def decode(data: bytes) -> str:
    """UTF-16 by BOM, else UTF-8, else Windows-1252 (the usual legacy SRT encoding)."""
    if data.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)):
        return data.decode("utf-16")
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:
        return data.decode("cp1252", errors="replace")


def load_cues(path: Path) -> list[Cue]:
    return parse_cues(decode(path.read_bytes()))


def find_sidecars(video: Path) -> list[Path]:
    """Subtitle files next to `video` named `<stem>.srt` or `<stem>.<tag>.srt` (any case)."""
    stem = video.stem.casefold()
    try:
        candidates = [p for p in video.parent.iterdir() if p.suffix.lower() in SUBTITLE_EXTENSIONS]
    except OSError:
        log.warning("cannot list %s", video.parent, exc_info=True)
        return []
    matches = [p for p in candidates if p.stem.casefold() == stem or _is_tagged(p, stem)]
    return sorted(matches, key=lambda p: (p.stem.casefold() != stem, natural_key(p)))


def _is_tagged(path: Path, stem: str) -> bool:
    return path.stem.casefold().startswith(stem + ".")


class CueTrack:
    """Cues sorted by start, answering "what is on screen at t" in O(log n + overlap)."""

    def __init__(self, cues: Iterable[Cue]) -> None:
        self._cues = sorted(cues, key=lambda cue: cue.start_ms)
        self._starts = [cue.start_ms for cue in self._cues]
        self._longest = max((cue.end_ms - cue.start_ms for cue in self._cues), default=0)

    def __len__(self) -> int:
        return len(self._cues)

    def text_at(self, position_ms: int) -> str:
        active = []
        i = bisect.bisect_right(self._starts, position_ms) - 1
        # No cue starting at or before `position_ms - longest` can still be showing.
        while i >= 0 and self._cues[i].start_ms > position_ms - self._longest:
            if self._cues[i].end_ms > position_ms:
                active.append(self._cues[i].text)
            i -= 1
        return "<br>".join(reversed(active))
