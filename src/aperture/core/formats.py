"""Media formats offered in file dialogs and picked from folders. Decoding is up to the backend."""

from __future__ import annotations

from pathlib import Path

VIDEO_EXTENSIONS = frozenset(
    {
        ".3gp", ".avi", ".flv", ".m2ts", ".m4v", ".mkv", ".mov",
        ".mp4", ".mpeg", ".mpg", ".ogv", ".ts", ".webm", ".wmv",
    }
)  # fmt: skip

AUDIO_EXTENSIONS = frozenset(
    {".aac", ".aiff", ".alac", ".flac", ".m4a", ".mp3", ".oga", ".ogg", ".opus", ".wav", ".wma"}
)
MEDIA_EXTENSIONS = VIDEO_EXTENSIONS | AUDIO_EXTENSIONS


def is_video(path: Path | str) -> bool:
    return Path(path).suffix.lower() in VIDEO_EXTENSIONS


def is_audio(path: Path | str) -> bool:
    return Path(path).suffix.lower() in AUDIO_EXTENSIONS


def is_media(path: Path | str) -> bool:
    return Path(path).suffix.lower() in MEDIA_EXTENSIONS


def dialog_filters() -> list[str]:
    def patterns(extensions: frozenset[str]) -> str:
        return " ".join(f"*{ext}" for ext in sorted(extensions))

    return [
        f"Media files ({patterns(MEDIA_EXTENSIONS)})",
        f"Video files ({patterns(VIDEO_EXTENSIONS)})",
        f"Audio files ({patterns(AUDIO_EXTENSIONS)})",
        "All files (*)",
    ]
