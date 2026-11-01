"""Lyrics stored inside audio files.

MP3: synced lyrics go in an ID3 SYLT frame (timestamps in milliseconds), with the words also
in USLT for players that only read unsynchronized lyrics. FLAC/Ogg/Opus: a Vorbis LYRICS
comment, MP4: ©lyr, both holding LRC text, the convention players read synced lyrics from.
"""

from __future__ import annotations

from pathlib import Path

from mutagen import File as MutagenFile
from mutagen import MutagenError
from mutagen.easyid3 import EasyID3
from mutagen.flac import FLAC
from mutagen.id3 import ID3, SYLT, USLT, ID3NoHeaderError
from mutagen.mp4 import MP4
from mutagen.oggopus import OggOpus
from mutagen.oggvorbis import OggVorbis

from aperture.core.lyrics import LyricLine, LyricsTrack, format_lrc, parse_lyrics

EMBEDDABLE = (".flac", ".m4a", ".mp3", ".ogg", ".oga", ".opus")
_VORBIS = (FLAC, OggVorbis, OggOpus)
_VORBIS_KEYS = ("LYRICS", "UNSYNCEDLYRICS")
_MP4_KEY = "\xa9lyr"


class LyricsTagError(Exception):
    """The file cannot hold lyrics, or could not be read or written."""


def _open(path: Path):
    try:
        audio = MutagenFile(path)
    except MutagenError as exc:
        raise LyricsTagError(f"{path.name}: {exc}") from exc
    if audio is None:
        raise LyricsTagError(f"{path.name}: not a recognised audio file")
    return audio


def read_embedded(path: Path) -> str | None:
    """Lyrics text stored in `path`, or None when it has none or cannot be read."""
    try:
        if path.suffix.lower() == ".mp3":
            return _read_id3(ID3(path))
        audio = _open(path)
    except (ID3NoHeaderError, MutagenError, LyricsTagError, OSError):
        return None
    tags = audio.tags
    if tags is None:
        return None
    if isinstance(audio, MP4):
        values = tags.get(_MP4_KEY)
    elif isinstance(audio, _VORBIS):
        values = next((tags[key] for key in _VORBIS_KEYS if key in tags), None)
    else:
        return None
    return str(values[0]) if values else None


def embed(path: Path, text: str) -> None:
    """Store `text` (usually LRC) as the lyrics of `path`, replacing any existing lyrics."""
    if path.suffix.lower() not in EMBEDDABLE:
        raise LyricsTagError(f"{path.suffix or 'this'} files cannot hold lyrics")
    try:
        if path.suffix.lower() == ".mp3":
            try:
                tags = ID3(path)
            except ID3NoHeaderError:
                tags = ID3()
            _write_id3(tags, parse_lyrics(text))
            tags.save(path)
            return
        audio = _open(path)
        if audio.tags is None:
            audio.add_tags()
        if isinstance(audio, MP4):
            audio.tags[_MP4_KEY] = [text]
        elif isinstance(audio, _VORBIS):
            for key in _VORBIS_KEYS[1:]:
                if key in audio.tags:
                    del audio.tags[key]
            audio.tags["LYRICS"] = [text]
        else:
            raise LyricsTagError(f"{path.name}: this format cannot hold lyrics")
        audio.save()
    except (MutagenError, OSError) as exc:
        raise LyricsTagError(f"{path.name}: {exc}") from exc


def _read_id3(tags: ID3) -> str | None:
    """SYLT (synced) as LRC text when present, else USLT as stored."""
    for frame in tags.getall("SYLT"):
        if frame.format == 2 and frame.text:  # 2: timestamps in milliseconds
            return format_lrc([LyricLine(int(ms), str(words)) for words, ms in frame.text])
    frames = tags.getall("USLT")
    return str(frames[0].text) if frames else None


def _write_id3(tags: ID3, lines: list[LyricLine]) -> None:
    tags.delall("USLT")
    tags.delall("SYLT")
    words = "\n".join(line.text for line in lines)
    tags.add(USLT(encoding=3, lang="eng", desc="", text=words))
    if LyricsTrack(lines).synced:
        timed = [(line.text, line.time_ms) for line in lines if line.time_ms is not None]
        tags.add(SYLT(encoding=3, lang="eng", format=2, type=1, desc="", text=timed))


def song_fields(path: Path) -> dict[str, str]:
    """Title, artist and album from the file's tags, as a starting point for a search.

    Missing tags fall back to the file name, read as "Artist - Title" when it has a dash.
    """
    fields = {"title": "", "artist": "", "album": ""}
    try:
        if path.suffix.lower() == ".mp3":  # the tags alone: no need to parse the audio
            tags = EasyID3(path)
        else:
            tags = getattr(MutagenFile(path, easy=True), "tags", None) or {}
    except (MutagenError, OSError):
        tags = {}
    for key in fields:
        values = tags.get(key) if hasattr(tags, "get") else None
        if values:
            fields[key] = str(values[0]).strip()
    if not fields["title"]:
        artist, dash, title = path.stem.partition(" - ")
        fields["title"] = (title if dash else path.stem).strip()
        if dash and not fields["artist"]:
            fields["artist"] = artist.strip()
    return fields
