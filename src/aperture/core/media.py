"""Playable sources: local files (Path) and network streams (URL strings).

Local items stay `Path`; a stream stays the exact `str` the user gave, because `Path` would
fold `https://` into `https:/`.
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote, urlsplit

Source = Path | str

STREAM_SCHEMES = frozenset(
    {"http", "https", "rtsp", "rtsps", "rtmp", "rtmps", "mms", "srt", "udp", "rtp", "ftp"}
)
# Default frame time when a file does not report its frame rate (30 fps).
FALLBACK_FRAME_MS = 1000 / 30


def is_url(source: object) -> bool:
    return isinstance(source, str) and urlsplit(source).scheme.lower() in STREAM_SCHEMES


def parse_stream_url(text: str) -> str | None:
    """A playable stream URL from what the user typed, or None if it is not one.

    `example.com/video.mp4` gains `https://`; schemes outside STREAM_SCHEMES are refused.
    """
    text = text.strip()
    if not text or any(c.isspace() for c in text):
        return None
    if "://" not in text:
        text = f"https://{text}"
    parts = urlsplit(text)
    try:
        port = parts.port  # raises on a malformed port such as "javascript:alert(1)"
    except ValueError:
        return None
    if parts.scheme.lower() not in STREAM_SCHEMES or not parts.hostname:
        return None
    if "." not in parts.hostname and parts.hostname != "localhost" and not port:
        return None
    return text


def display_name(source: Source) -> str:
    """File name, or for a stream the last path segment (else the host)."""
    if not is_url(source):
        return Path(source).name
    parts = urlsplit(str(source))
    segment = unquote(parts.path.rstrip("/").rsplit("/", 1)[-1])
    return segment or parts.hostname or str(source)


def display_stem(source: Source) -> str:
    name = display_name(source)
    stem = Path(name).stem if "." in name else name
    return stem or name


def kind_label(source: Source) -> str:
    """`MKV`, `MP3`… or `STREAM` for a URL without a recognisable extension."""
    suffix = Path(display_name(source)).suffix.lstrip(".").upper()
    return suffix if suffix and len(suffix) <= 5 else ("STREAM" if is_url(source) else "")


def folder_label(source: Source) -> str:
    return urlsplit(str(source)).hostname or "" if is_url(source) else Path(source).parent.name


_UNSAFE = re.compile(r'[<>:"/\\|?*\x00-\x1f]+')


def screenshot_name(title: str, position_ms: int, taken: datetime) -> str:
    """`Movie 01-02-03.456 (2026-10-30 21-14-05).png` — sortable, safe on every filesystem."""
    safe = _UNSAFE.sub("_", title).strip(" ._") or "Aperture"
    total_s, ms = divmod(max(0, position_ms), 1000)
    hours, rest = divmod(total_s, 3600)
    minutes, seconds = divmod(rest, 60)
    clock = f"{hours:02d}-{minutes:02d}-{seconds:02d}.{ms:03d}"
    return f"{safe[:80]} {clock} ({taken:%Y-%m-%d %H-%M-%S}).png"


def frame_ms(frame_rate: float | None) -> float:
    """Duration of one frame; falls back to 30 fps for missing or absurd rates."""
    if not frame_rate or not 1 <= frame_rate <= 1000:
        return FALLBACK_FRAME_MS
    return 1000 / frame_rate
