"""Lyrics stored inside audio files: ID3 USLT (MP3), Vorbis LYRICS (FLAC/Ogg/Opus), MP4 ©lyr."""

from __future__ import annotations

from pathlib import Path

from mutagen import File as MutagenFile
from mutagen import MutagenError
from mutagen.flac import FLAC
from mutagen.id3 import ID3, USLT, ID3NoHeaderError
from mutagen.mp4 import MP4
from mutagen.oggopus import OggOpus
from mutagen.oggvorbis import OggVorbis

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
            frames = ID3(path).getall("USLT")
            return str(frames[0].text) if frames else None
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
            tags.delall("USLT")
            tags.add(USLT(encoding=3, lang="eng", desc="", text=text))
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
