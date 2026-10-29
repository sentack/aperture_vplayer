"""Playback core, UI-independent."""

from aperture.core.errors import ERROR_KINDS, FriendlyError, describe_error
from aperture.core.files import expand_paths
from aperture.core.formats import (
    AUDIO_EXTENSIONS,
    MEDIA_EXTENSIONS,
    VIDEO_EXTENSIONS,
    dialog_filters,
    is_audio,
    is_media,
    is_video,
)
from aperture.core.history import History
from aperture.core.lyrics import LyricLine, LyricsTrack, find_lyrics, format_lrc, parse_lyrics
from aperture.core.playlist import Playlist
from aperture.core.rate import RATES, format_rate, step_rate
from aperture.core.subtitles import SUBTITLE_EXTENSIONS, CueTrack, find_sidecars, load_cues
from aperture.core.thumbnails import thumbnail_bucket
from aperture.core.timefmt import format_time
from aperture.core.tracks import track_label

__all__ = [
    "AUDIO_EXTENSIONS",
    "MEDIA_EXTENSIONS",
    "LyricLine",
    "LyricsTrack",
    "ERROR_KINDS",
    "FriendlyError",
    "VIDEO_EXTENSIONS",
    "History",
    "Playlist",
    "RATES",
    "SUBTITLE_EXTENSIONS",
    "CueTrack",
    "describe_error",
    "dialog_filters",
    "expand_paths",
    "find_lyrics",
    "find_sidecars",
    "format_lrc",
    "format_rate",
    "format_time",
    "is_audio",
    "is_media",
    "is_video",
    "load_cues",
    "parse_lyrics",
    "step_rate",
    "thumbnail_bucket",
    "track_label",
]
