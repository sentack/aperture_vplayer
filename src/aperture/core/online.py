"""Searching lyrics (LRCLIB) and subtitles (OpenSubtitles): requests and answers, no Qt.

The network side lives in player/online.py. Everything here is plain data in and out, so
the parsing of each service's answers is tested without a connection.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

LRCLIB_SEARCH = "https://lrclib.net/api/search"
OPENSUBTITLES_API = "https://api.opensubtitles.com/api/v1"
PROJECT_URL = "https://github.com/sentack/aperture_vplayer"
MAX_RESULTS = 30

_YEAR = re.compile(r"(?<!\d)(19[3-9]\d|20\d\d)(?!\d)")
# Where release names stop being the title: resolution, source, codec, episode markers.
_RELEASE_TAG = re.compile(
    r"\b(\d{3,4}p|[48]k|uhd|hdr\d*|bluray|blu-ray|bdrip|brrip|web-?dl|web-?rip|webrip|hdtv|"
    r"dvdrip|hdrip|x26[45]|h\.?26[45]|hevc|xvid|aac\d?|ac3|ddp?\d|dts|remux|proper|repack|"
    r"extended|unrated|s\d{1,2}e\d{1,3})\b",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class LyricsResult:
    track: str
    artist: str
    album: str
    duration_s: float
    synced: bool
    text: str  # LRC when synced, else plain lines


@dataclass(frozen=True, slots=True)
class SubtitleResult:
    file_id: int
    release: str
    language: str
    downloads: int
    hearing_impaired: bool


# --- lyrics ----------------------------------------------------------------------------------


def lrclib_query(title: str, artist: str = "", album: str = "") -> dict[str, str]:
    """Query parameters for an LRCLIB search; empty fields are left out."""
    fields = {"track_name": title, "artist_name": artist, "album_name": album}
    return {key: value.strip() for key, value in fields.items() if value.strip()}


def parse_lrclib(data: object, duration_s: float = 0) -> list[LyricsResult]:
    """Results with lyrics, synced first, then those closest to the file's length."""
    if not isinstance(data, list):
        return []
    results = []
    for item in data:
        if not isinstance(item, dict):
            continue
        synced, plain = item.get("syncedLyrics"), item.get("plainLyrics")
        text = synced if isinstance(synced, str) and synced.strip() else plain
        if not isinstance(text, str) or not text.strip():
            continue  # instrumentals and empty entries have nothing to show
        duration = item.get("duration")
        results.append(
            LyricsResult(
                track=str(item.get("trackName") or ""),
                artist=str(item.get("artistName") or ""),
                album=str(item.get("albumName") or ""),
                duration_s=float(duration) if isinstance(duration, int | float) else 0.0,
                synced=text is synced,
                text=text,
            )
        )

    def rank(result: LyricsResult) -> tuple[bool, float]:
        gap = abs(result.duration_s - duration_s) if duration_s and result.duration_s else 0
        return (not result.synced, gap)

    return sorted(results, key=rank)[:MAX_RESULTS]


# --- subtitles -------------------------------------------------------------------------------


def guess_title_year(name: str) -> tuple[str, str]:
    """A film's title and year from a file name such as `The.Movie.2014.1080p.BluRay.mkv`.

    Only a starting guess for the search form: the user can correct it.
    """
    text = re.sub(r"[._]+", " ", Path(name).stem)
    text = re.sub(r"^\s*\[[^\]]*\]\s*", "", text)  # a leading [Group] tag
    tag = _RELEASE_TAG.search(text)
    stop = tag.start() if tag else len(text)
    # The release year: one in brackets if any, else the last before the release tags, as
    # titles can hold years too ("Blade Runner 2049 2017"). Not at the very start: "2012.mkv".
    years = [m for m in _YEAR.finditer(text, 0, stop) if m.start() > 0]
    bracketed = [m for m in years if text[m.start() - 1] in "(["]
    year = (bracketed or years or [None])[-1]
    ends = [m.start() for m in (year, tag) if m and m.start() > 0]
    title = text[: min(ends)] if ends else text
    title = re.sub(r"\s+", " ", title).strip(" -([")
    return title or text.strip(), year.group(1) if year else ""


def opensubtitles_query(title: str, year: str = "", language: str = "") -> dict[str, str]:
    query = {"query": title.strip()}
    if year.strip().isdigit():
        query["year"] = year.strip()
    if language.strip():
        query["languages"] = ",".join(
            part.strip().lower() for part in language.split(",") if part.strip()
        )
    return query


def parse_subtitle_search(data: object) -> list[SubtitleResult]:
    """One result per subtitle file, most downloaded first."""
    items = data.get("data") if isinstance(data, dict) else None
    if not isinstance(items, list):
        return []
    results = []
    for item in items:
        attributes = item.get("attributes") if isinstance(item, dict) else None
        if not isinstance(attributes, dict):
            continue
        files = attributes.get("files")
        if not isinstance(files, list) or not files or not isinstance(files[0], dict):
            continue
        file_id = files[0].get("file_id")
        if not isinstance(file_id, int):
            continue
        details = attributes.get("feature_details")
        title = details.get("title") if isinstance(details, dict) else ""
        downloads = attributes.get("download_count")
        results.append(
            SubtitleResult(
                file_id=file_id,
                release=str(attributes.get("release") or files[0].get("file_name") or title),
                language=str(attributes.get("language") or ""),
                downloads=downloads if isinstance(downloads, int) else 0,
                hearing_impaired=bool(attributes.get("hearing_impaired")),
            )
        )
    results.sort(key=lambda r: -r.downloads)
    return results[:MAX_RESULTS]


def parse_download_link(data: object) -> str | None:
    """The temporary HTTPS link OpenSubtitles hands out for one download."""
    link = data.get("link") if isinstance(data, dict) else None
    return link if isinstance(link, str) and link.startswith("https://") else None


def subtitle_path(video: Path, language: str) -> Path:
    """`Movie.en.srt` next to `Movie.mkv`: the name Aperture loads automatically next time.

    An existing file is never overwritten; a number is added instead.
    """
    tag = re.sub(r"[^a-z-]", "", language.lower())[:8] or "sub"
    path = video.with_name(f"{video.stem}.{tag}.srt")
    number = 2
    while path.exists():
        path = video.with_name(f"{video.stem}.{tag}.{number}.srt")
        number += 1
    return path


# --- failures --------------------------------------------------------------------------------


def describe_failure(service: str, status: int | None, network_error: bool = False) -> str:
    """What to tell the user when a search or download did not work."""
    if network_error and status is None:
        return f"Couldn't reach {service}. Check your connection and try again."
    match status:
        case 401 | 403:
            return f"{service} refused the API key. Check it in Settings → Subtitles."
        case 406:
            return f"Today's {service} download limit is used up. Try again tomorrow."
        case 429:
            return f"{service} is getting too many searches. Try again in a minute."
        case int() if status >= 500:
            return f"{service} is unavailable right now. Try again later."
    return f"{service} didn't answer as expected. Try again later."
